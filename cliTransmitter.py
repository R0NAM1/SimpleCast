import time, socket, os, uuid, mss, json, asyncio, threading, aiohttp
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer, RTCDataChannel, RTCRtpCodecParameters
from aiortc.mediastreams import VideoFrame
from aiortc.contrib.media import MediaPlayer, MediaBlackhole, MediaStreamTrack, MediaRelay
from aiortc.rtcrtpsender import RTCRtpSender
# Non GUI version of SimpleCast client to get basics working

global screenFrameBufferQueue, clientPsk, serverPinAuthNeeded, serverAudioAllowed

foundServers = [];

clientPsk = ''
configServerList = []

serverPinAuthNeeded = False
serverAudioAllowed = False
willSendAudio = False

async def startRTCPeering(serverIpAddress):
    print("Should have authed, now attempting RTC")
    
    serverPostAddress = 'http://' + serverIpAddress + ':4825/sdpOffer'
    
    # Define config
    stunServer = RTCIceServer(
        # urls=["stun:" + serverIpAddress]
        urls=["stun:10.42.0.8"] # Test ICE server
    )
    
    config = RTCConfiguration(
        iceServers=[stunServer]
    )
    
    # Create peer connection
    clientPeer = RTCPeerConnection(configuration=config)
    
    # Add media tracks
    # TEMP, use video mp4 for now, change to mss later
    tmpPath = ('tmpVideo.webm') # Pootis Engage, great test video
    videoPLayerTrack = (MediaPlayer(tmpPath)).video
    # clientPeer.addTrack(videoPLayerTrack)
    clientPeer.addTransceiver(videoPLayerTrack, direction='sendonly')
    
    # Add data channel
    dataChannel = clientPeer.createDataChannel("chat")
    
    @dataChannel.on("open")
    def onOpen():
        print("Data Channel Opened")
        dataChannel.send("ThisIsDataChannel!")
        
    @dataChannel.on("message")
    def on_message(message):
        print(f"Message received: {message}")
    
    # Create SDP offer
    sdpOffer = await clientPeer.createOffer()
        
    # Set local description
    await clientPeer.setLocalDescription(sdpOffer)
        
    # Open new HTTP session and send SDP
    session = aiohttp.ClientSession()
    
    # SEND POST, wait for response
    serverDataRecieved = await session.post(serverPostAddress, data=str(sdpOffer.sdp)) 

    serverTextReceived = (await serverDataRecieved.text())
            
    print("Got SDP response")
            
    # Set server description
    serverSDPResponseObject = RTCSessionDescription(serverTextReceived, 'answer')

    await clientPeer.setRemoteDescription(serverSDPResponseObject)
    
    # Frames should start being sent now, are they? Do I have to do that manually?

    print("State:")
    print(clientPeer.signalingState)

    # Close session
    await session.close()

    # Call recv
    # print("At sin")
    # while True:
    #     # Temp keep running
    #     pass
    #     print(await videoPLayer.video.recv())

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
    global clientPsk, foundServers, configServerList
    # For each entry in array, print like such
    # arrayIndex) [ipAddress] friendlyName, status
    
    # Print top banner showing clientPsk
    print("SimpleCast | " + str(clientPsk) + " | Servers found in LAN:")
    print("====================================")
    
    # Print all servers in foundServers
    arrayIndex = 0
    for listEntry in foundServers:
        
        # Create string to print
        stringToPrint = (str(arrayIndex) + ')' + ' [' + listEntry[0] + '] ' + listEntry[1] + ' [' + listEntry[2] + ']')
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
    
    # Let user select number input, if not a number below of equal to arrayIndex, then try again

    while True:
        
        try:
            selectedServerIndex = int(input("Select Server: "))
                        
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
    global clientPsk, serverPinAuthNeeded, serverAudioAllowed, serverIpAddress
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
            else:
                print("Unreconized option, try again...")
                
        # End of True
        amIAuthText = (await amIAuth.text())

        print(amIAuthText)
        
        # Close HTTP session
        await session.close()
                
        # Wait on response:accepted to move to rtc connection
        if amIAuthText == 'response:accepted':
            # loop = asyncio.get_event_loop()
            # # Push to another thread?
            # loop.run_until_complete(startRTCPeering(combinedList[serverIndex][0]))
            clientPeer = await startRTCPeering(combinedList[serverIndex][0])
            
            return clientPeer
            
            # loop.run_forever()
            
        elif amIAuthText == 'response:rejected':
            print("Connection rejected, restarting program")
            time.sleep(3)
            programStart()
    

# Capture Broadcast packets for 5 seconds since servers broadcast every 2 seconds
# Listens on port 1337 (Yes, and I'm not changing it.)
def singleBroadcastScan(secondsToScan):
    global foundServers
    # Reset found servers
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
    print("=== Scanning for servers ===")
    
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
        tempArray = [ipAddress, dataArray[0], dataArray[1]]
        
        # Add to foundServers array if not already in there
        if tempArray not in foundServers:
            # Not already in array, add to
            
            foundServers.append(tempArray)
        
        # Already exists, does not add

async def programStart():
    # Check local config for static server addresses and this clients PSK
    readConfigFile()
    
    # Clear screen
    clearConsoleScreen()
    
    # Do a broadcast scan for 5 seconds, push into array
    singleBroadcastScan(5)
    
    # Clear screen to show list
    clearConsoleScreen()
    
    # Show broadcast found servers and servers from config
    selectedIndex = await showAndSelectSelectableServers()

    clearConsoleScreen()
    
    clientPeer = await startConnecting(selectedIndex)
    
    # Keep running forever?
    while True:
        print("Status: " + str((clientPeer.signalingState)))
        await asyncio.sleep(1)

    # Connecting with options, show connected interface
    # Start transmiting audio and video to server

if __name__ == '__main__':
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(programStart())
    asyncio.run(programStart())