import time, socket, os, uuid, mss, json, asyncio, threading, aiohttp, screenMediaSourceClass, av
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer, RTCDataChannel, RTCRtpCodecParameters
from aiortc.mediastreams import VideoFrame
from aiortc.contrib.media import MediaPlayer, MediaBlackhole, MediaStreamTrack, MediaRelay
from aiortc.rtcrtpsender import RTCRtpSender
from screeninfo import get_monitors
# Non GUI version of SimpleCast client to get basics working

global clientPsk, configServerList, serverPinAuthNeeded, serverAudioAllowed, willSendAudio, foundServers, globalPcObject, monitorsFound

# Initialize Global Variables
# Config variables
clientPsk = ''
configServerList = []

# Server settings
serverPinAuthNeeded = False
serverAudioAllowed = False

# Other
willSendAudio = False
foundServers = []
foundServersStatus = []
globalPcObject = None
monitorsFound = []
monitorSelectionIndex = 0

def toggleResolutionScale():
    # This function looks at the resolution scale and bumps it to the next step depending on
    # Valid steps are 1, 1.5, 1.7, 2, 2.3, 2.5
    if screenMediaSourceClass.resolutionScaler == 1:
        screenMediaSourceClass.resolutionScaler = 1.5
    elif screenMediaSourceClass.resolutionScaler == 1.5:
        screenMediaSourceClass.resolutionScaler = 1.7
    elif screenMediaSourceClass.resolutionScaler == 1.7:
            screenMediaSourceClass.resolutionScaler = 2
    elif screenMediaSourceClass.resolutionScaler == 2:
            screenMediaSourceClass.resolutionScaler = 2.3
    elif screenMediaSourceClass.resolutionScaler == 2.3:
            screenMediaSourceClass.resolutionScaler = 2.5
    elif screenMediaSourceClass.resolutionScaler == 2.5:
            screenMediaSourceClass.resolutionScaler = 1
            
    print("Toggled to " + str(screenMediaSourceClass.resolutionScaler))
            
    # A truly amazing state machine, I know
                   
def selectMonitor():
    global monitorsFound,monitorSelectionIndex
    # Print found monitors:
    while True:
        print("Monitors Found, primary is default")
        trackingIndex = 0
        for monitor in monitorsFound:
            # name, width, height, posx, posy, isdefault
            if (monitor[5] == True):
                stringToPrint = (str(trackingIndex) + ") " + "[PRIMARY] " + str(monitor[0]) + ", " + str(monitor[1]) + "x" + str(monitor[2]))
            else:
                stringToPrint = (str(trackingIndex) + ") " + "[EXTENDED] " + str(monitor[0]) + ", " + str(monitor[1]) + "x" + str(monitor[2]))
            trackingIndex += 1
            print(stringToPrint)
            
        monitorSelectionIndex = input("Monitor To Use: ")
        
        # Attempt to convert to int, if fails, retry
        try:
            monitorSelectionIndex = int(monitorSelectionIndex)
        except:
            print("Not an integer, try again")
            continue
        
        # If int, check if in range
        if monitorSelectionIndex > (trackingIndex - 1):
            print("Not valid, try again")
            continue
        else:
            break
        # If in range, then set perminantly
    

def boolSort(subArray):
    return subArray[0]

def getMontiorSelection():
    global monitorsFound
    
    for monitor in get_monitors():
        # Print name, width, height, posx, posy, isdefault
        monitorArray = [monitor.name, monitor.width, monitor.height, monitor.x, monitor.y, monitor.is_primary]
        monitorsFound.append(monitorArray)

    # Attempt sort
    
    monitorsFound = sorted(monitorsFound, key=boolSort, reverse=True)

async def doHTTPPost(commandToSend, serverIpAddress):
 # Open HTTP session with server
            session = aiohttp.ClientSession()
            
            serverUrl = 'http://' + serverIpAddress + ':4825/command'
            commandString = (commandToSend)
            # SEND POST, wait for response
            serverDataRecieved = await (session.post(serverUrl, data=commandString)) 

            serverTextReceived = await (serverDataRecieved.text())
            
            print("Response: " + str(serverTextReceived))
            
            await session.close()
            
            
async def startRTCPeering(serverIpAddress):
    global globalPcObject, monitorSelectionIndex, monitorsFound, willSendAudio
    print("Should have authed, now attempting RTC")
    
    serverPostAddress = 'http://' + serverIpAddress + ':4825/sdpOffer'
    
    # Define config
    stunServer = ("stun:" + serverIpAddress)
    
    # Create peer connection
    clientPeer = RTCPeerConnection(configuration=RTCConfiguration(
            iceServers=[RTCIceServer(
                urls=[stunServer])]))
    
    globalPcObject = clientPeer
        
    internalCaps = RTCRtpSender.getCapabilities('video').codecs
    
    codecToUse = []
    
    # Available mimeTypes, video/H264, video/VP8
    # H264, 42e01f higher quality, more resources
    # 42001f lower quality, less resources
    
    # H264 42001f seems to be the best combo, VP8 can have variable resolutions, but constantly takes 1 - 5 seconds to recv when bitrate goes above 2 mbs
    # FINAL: H264 42001f with retransmission (rtx)
    # Because H264 does not like variable resolution, force to stay 720p, maybe 1080p in the future
    wantCodec = 'video/H264'
    
    for cap in internalCaps:
        if cap.mimeType == 'video/H264' and wantCodec == 'video/H264':
            # Check if wanted profile
            if cap.parameters.get('profile-level-id') == '42001f':
                codecToUse.append(cap)
                print("Using Codec: " + str(cap))
        elif cap.mimeType == 'video/VP8' and wantCodec == 'video/VP8':
            codecToUse.append(cap)
            print("Using Codec: " + str(cap))
        # Always use vpx for better control?
        elif cap.mimeType == 'video/rtx':
            codecToUse.append(cap)
            print("Using Codec: " + str(cap))
    
    # Add screen capture MediaPlayer
    screenPlayer = screenMediaSourceClass.ScreenPlayer(monitorsFound, monitorSelectionIndex, willSendAudio)
    # Create videoPlayerTrack from player that receives frames
    videoPlayerTrack = screenMediaSourceClass.VideoFramePlayerTrack(screenPlayer)
    
    videoTransceiver = clientPeer.addTransceiver(videoPlayerTrack, direction='sendonly')
    # Set codec
    videoTransceiver.setCodecPreferences(codecToUse)

    # print("Codecs: " + str(clientPeer.get))
    
    # Add audio
    if willSendAudio == True:
        audioPlayerTrack = screenMediaSourceClass.AudioCameraPlayerTrack(screenPlayer)
        clientPeer.addTransceiver(audioPlayerTrack, direction='sendonly')

    
    
    # Add data channel
    # DOES NOT WORK WITHOUT DATACHANNEL, I again, don't know why :/
    dataChannel = clientPeer.createDataChannel("datachannel")
    
    # Create SDP offer
    sdpOffer = await clientPeer.createOffer()
        
    # Set local description
    await clientPeer.setLocalDescription(sdpOffer)
        
    # Open new HTTP session and send SDP
    session = aiohttp.ClientSession()
    
    # SEND POST, wait for response
    serverDataRecieved = await session.post(serverPostAddress, data=str(clientPeer.localDescription.sdp)) 

    serverTextReceived = (await serverDataRecieved.text())
            
    # Set server description
    serverSDPResponseObject = RTCSessionDescription(serverTextReceived, 'answer')

    await clientPeer.setRemoteDescription(serverSDPResponseObject)

    # Close HTTP session
    await session.close()

    # Return client peer
    return clientPeer


# Clean screen function
def clearConsoleScreen():
    # If OS type is NT (Windows), use cls, else clear
    if (os.name == 'nt'):
        os.system('cls')
    else:
        os.system('clear')
        
# Read config json file, has psk and array of IP addresses for static servers
# If none exists, create empty one with new PSK
# Eventually add last checked settings, remember audio redirection and other
def readConfigFile():
    global configServerList, clientPsk
    # First verify if file exists, if not create empty json file and generate PSK
    fullPath = os.path.expanduser('~/.simpleCastClient.json')
    
    # Assume file does not exist by default
    fileExists = False
    
    # Check if exists, if not populate
    if os.path.exists(fullPath):
        # File for sure exists
        fileExists = True
    else:
        # Does not exist, create empty file and populate
        # Generate new PSK
        pskString = str(uuid.uuid4())
        serverListArray = []
        
        # Data to push into .json
        jsonData = {
            'psk': pskString,
            'serverList': serverListArray
        }
        
        # Open new config file
        newConfigJson = open(fullPath, 'w')
        
        # Dump JSON data into file
        json.dump(jsonData, newConfigJson)
        
        # Close config file
        newConfigJson.close()
        # File now exists
        fileExists = True
        
    # File should now exist no matter what, if so then read as config
    if fileExists == True:    
        # Read config from disk, then close
        readConfigJson = open(fullPath, 'r')
        readConfigJsonObject = json.load(readConfigJson)
        readConfigJson.close()
        
        # Read client data
        clientPsk = readConfigJsonObject['psk']
        configServerList = readConfigJsonObject['serverList']
        
    # Done reading config
    
# Function to draw selection screen, takes in array with IP and Friendly Name
async def showAndSelectSelectableServers():
    global clientPsk, foundServers, configServerList, monitorsFound, foundServersStatus
    # For each entry in array, print like such
    # arrayIndex) [ipAddress] friendlyName, status
    arrayIndex = 0
    async def showServers():
    
        # Print top banner showing clientPsk
        print("SimpleCast | " + "PSK: " + str(clientPsk) + " | Servers found in LAN:")
        print("====================================")
        
        # Print all servers in foundServers
        arrayIndex = 0
        for server in foundServers:
            
            # Create string to print
            stringToPrint = (str(arrayIndex) + ')' + ' [' + server[0] + '] ' + server[1] + ' [' + foundServersStatus[arrayIndex] + ']')
            # Print string
            print(stringToPrint)
            # Add one to index
            arrayIndex =+ 1
            
        # Print all servers from config, using same arrayIndex
        # Implement when probe properly returns status
        
        print("===Static Servers===================")
        for listEntry in configServerList:
            # Split data, ipAddress, Name
            listEntry = listEntry.split("|")
                
            # Probe server for hostname and status
            # dataProveResponse serverName, status
            dataProveResponse = await probeServerForStatus(listEntry[0])
                
            # Create string to print
            stringToPrint = (str(arrayIndex) + ')' + ' [' + listEntry[0] + '] ' + dataProveResponse[0] + ' [' + dataProveResponse[1] + ']')
            # # Print string
            print(stringToPrint)
            # # Add one to index
            arrayIndex =+ 1
        return arrayIndex
        
        # Print ReScan option
        print("====================================")
        print("R) Re-Scan")
    
    arrayIndex = await showServers()

    # Let user select number input, if not a number below of equal to arrayIndex, then try again

    while True:
        # While true until valid
        try:
            selectedServerIndex = (input("Select Option: "))
            
            if selectedServerIndex == 'r' or selectedServerIndex == 'R':
                pass
                # Re run scan broadcast
                singleBroadcastScan(5)
                arrayIndex = await showServers()

            else:
                # Convert to int
                selectedServerIndex = int(selectedServerIndex)
                            
                if selectedServerIndex <= arrayIndex:
                    return selectedServerIndex
                else:
                    print(str(selectedServerIndex) + " is not a valid server index, try again...")

        except Exception:
                print("Not an integer, try again...")

# Probe server for connetion status, friendly name, other info
async def probeServerForStatus(serverIpAddress):

    # Open HTTP session with server
    session = aiohttp.ClientSession()
    
    serverUrl = 'http://' + serverIpAddress + ':4825/command'
    commandString = ('command:statusProbe|')
    # SEND POST, wait for response
    serverDataRecieved = await session.post(serverUrl, data=commandString) 

    serverTextReceived = (await serverDataRecieved.text())

    serverSplitData = serverTextReceived.split("|")
    
    # Close HTTP session
    await session.close()
    
    return serverSplitData

# Probe server, is PIN required, forward PSK, if so. Is Audio enabled?
async def startConnecting(serverIndex):
    global clientPsk, serverPinAuthNeeded, serverAudioAllowed, serverIpAddress, willSendAudio
    serverIndex = int(serverIndex)
    
    # Combine foundServers and configServers to get one list with applicable indexes
    combinedList = []
    for item in foundServers:
        combinedList.append(item)
        
    for item in configServerList:
        item  = item.split("|")
        combinedList.append(item)
    
    # Create attemptConnection string with my hostname and psk
    # command:attemptConnection|myHostname|myPsk
    conString = ("command:attemptConnection|" + str(socket.gethostname() + "|" + str(clientPsk)))
    
    # Send connection attempt
    # Open HTTP session with server
    session = aiohttp.ClientSession()
    
    serverUrl = 'http://' + str(combinedList[serverIndex][0]) + ':4825/command'
    
    # SEND POST, wait for response
    serverDataRecieved = await session.post(serverUrl, data=conString) 

    serverTextReceived = (await serverDataRecieved.text())

    receivedData = serverTextReceived.split("|")
    
    # Wait to receive data back, 
    # will be response|doINeedToProvideAPin|audioRedirectionBool
    
    # Check if data received is command:response
    if receivedData[0] == 'response':
        
        # Is Pin Auth required?
        if receivedData[1] == "True":   
            serverPinAuthNeeded = True
            print("PIN AUTH REQUIRED")
        else:
            serverPinAuthNeeded = False
            print("NO PIN REQUIRED")
            
        # Is audio redirection allowed?
        if receivedData[2] == "True":
            serverAudioAllowed = True
        else:
            serverAudioAllowed = False
            
        # Let user toggle options, C for connect
        # For now just allow connection, or enter pin, 
        
        print("Options options, ")
        print("C) Connect to server")
        # if serverAudioAllowed:
            # print("A) Toggle Audio Redirection") #TODO
            # willSendAudio
        
        amIAuth = ''
        
        while True:
            userInput = input("Enter Option: ")
        
            if userInput == 'c' or userInput == 'C':
                if serverPinAuthNeeded == True:
                    inputtedPin = input("Enter PIN On Screen: ")
                    
                    # Send PIN response
                    probeString = "command:connect|" + str(inputtedPin)
                    # Send probe command
                    amIAuth = await session.post(serverUrl, data=probeString) 
                    break
                else:
                    # Just send connect with blank pin data
                    probeString = "command:connect|00000"
                    # Send probe command
                    amIAuth = await session.post(serverUrl, data=probeString) 
                    break
            
            elif userInput == 'a' or userInput == 'A':
                print("Audio not available, TODO")
                # if serverAudioAllowed:
                    # Can toggle
                    # if willSendAudio == False:
                    #     willSendAudio = True
                    # else:
                    #     willSendAudio = False
                    # print("Toggled Audio Redirection to " + str(willSendAudio))
                # else:
                    # print("Server Audio Redirection not allowed")


            else:
                print("Unreconized option, try again...")
                
        # End of True
        amIAuthText = (await amIAuth.text())

        print(amIAuthText)
        
        # Close HTTP session
        await session.close()
                
        # Wait on response:accepted to move to rtc connection
        if amIAuthText == 'response:accepted':            
            # Return True to send RTP
            return combinedList[serverIndex][0]
        
        elif amIAuthText == 'response:rejected':
            print("Connection rejected, restarting program")
            time.sleep(3)
            programStart()
    

# Capture Broadcast packets for 5 seconds since servers broadcast every 2 seconds
# Listens on port 1337 (Yes, and I'm not changing it.)
def singleBroadcastScan(secondsToScan):
    global foundServers, foundServersStatus
    
    # Clear screen
    clearConsoleScreen()
    
    # Reset found servers and status
    foundServersStatus = []
    foundServers = []
    
    
    # Set start time
    startListenTime = time.time()
    
    # Open UDP port to listen on
    listenBroadcastSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Bind socket to port on all interfaces
    listenBroadcastSocket.bind(('', 1337))
    
    # Enable the broadcast option on the socket (1) 
    listenBroadcastSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    # Let client know server scan is occuring
    print("=== Scanning for servers for 5 seconds ===")
    
    while True:
        # Check if secondsToScan seconds have passed, if so break loop
        if ((time.time() - startListenTime) >= secondsToScan):
            
            # Close listener socket
            listenBroadcastSocket.close()
            
            # Break loop
            break
        
        # Blocking operation, wait to receive data packet
        # Currently code does not continue unless a single packet is received
        data, address = listenBroadcastSocket.recvfrom(1024)
        
        # Extract IP Address
        ipAddress = address[0]
        
        # Split data into friendly name and current connection status
        dataArray = (data.decode()).split("|")
        
        # Show broadcast received
        print("=== Broadcast From " + str(address[0]) + " / Name: " + str(dataArray[0]) + " / Status: " + str(dataArray[1]) + " ===")
        
        # Make array from packet data
        tempArray = [ipAddress, dataArray[0]]

        # Add to foundServers array if not already in there
        if tempArray not in foundServers:
            # Not already in array, add to
            foundServers.append(tempArray)
            # Was not in before, we should also append status
            foundServersStatus.append(dataArray[1])
            
        else:
            # Is in array, find position
            index = foundServers.index(tempArray)
            foundServersStatus[index] = dataArray[1]
        
        # Already exists, does not add
    
    clearConsoleScreen()

# Main program loop, rerun here if program needs to 'quit'
def programStart():
    global globalPcObject
    # Check local config for static server addresses and this clients PSK
    readConfigFile()
    
    # Clear screen
    clearConsoleScreen()
    
    # Get local screens
    getMontiorSelection()
    
    # Do a broadcast scan for 5 seconds, push into array
    singleBroadcastScan(5)
    
    # Show broadcast found servers and servers from config
    loop = asyncio.get_event_loop()
    
    selectedIndex = loop.run_until_complete(showAndSelectSelectableServers())

    clearConsoleScreen()
    
    # Grab monitor selection
    selectedMonitor = selectMonitor()
    
    clearConsoleScreen()
    
    serverIpAddress = loop.run_until_complete(startConnecting(selectedIndex))
    
    # rtcLoop = asyncio.new_event_loop()
    
    # clientPeer = rtcLoop.run_until_complete(startRTCPeering(serverIpAddress))
    clientPeer = loop.run_until_complete(startRTCPeering(serverIpAddress))
    # Push to another thread
    rtcThread = threading.Thread(target=(loop.run_forever))
    rtcThread.start()
    
    # Wait for one second for connections
    time.sleep(1)
    
    while True:
        print("=====================Connected")
        print("P) Pause Casting")
        print("R) Toggle Resolution Scale")
        print("Q) Quit Program")
        isQ = input("Command: ")
        clearConsoleScreen()
        
        if isQ == 'Q' or isQ == 'q':
                     
            # Somehow call globalPcObject.close()
            print("Closing Peer")
            loop.stop()
            time.sleep(0.5)
            loop.run_until_complete(globalPcObject.close())
            print("Closed!")
            break
        
        elif isQ == 'p' or isQ == 'P':
            asyncio.run(doHTTPPost("command:pause|", serverIpAddress))
        elif isQ == 'r' or isQ == 'R':
            toggleResolutionScale()
           
    
    # Program should exit here
    print("Exiting program")

    # Connecting with options, show connected interface
    # Start transmiting audio and video to server

if __name__ == '__main__':
    av.logging.set_level(av.logging.FATAL)
    programStart()