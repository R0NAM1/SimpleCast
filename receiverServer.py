import time, socket, json, os, random, struct, queue, ast, asyncio, pygame, sys, pyaudio, numpy
from threading import Thread, active_count
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer, RTCDataChannel, RTCRtpCodecParameters
from aiortc.mediastreams import VideoFrame
from aiortc.contrib.media import MediaPlayer, MediaBlackhole, MediaStreamTrack, MediaRelay
from aiortc.rtcrtpsender import RTCRtpSender
from aiohttp import web
from datetime import datetime

# SimpleCast specific imports
from slideshowObjects import drawBlackCatchBackground, drawStaticBackground, drawNextSlideShowFrameTick, aspectRatioResizeFixedHeight
from drawGuiObjects import drawConnectingInformation, pyGameDrawInformation
import myGlobals

global clientIP, latestVideoFrame, processFrames, pingPongTime, thisServersIpAddress, sendBroadcastPacket, allowAudioRedirection, usePINAuthentication, allowedPskList, currentConnection
# Global variables initialization

# Client info variables
currentConnection = 'open'
clientIP = ''

# Config variables
allowAudioRedirection = False
usePINAuthentication = True
allowedPskList = []

# Server variables
sendBroadcastPacket = True
# Needed so that we can set STUN correctly
# Should be set to STATIC, or use a DHCP reservation.
# Having this instead of grabbing from an interface forces you to keep it static in some way
thisServersIpAddress = '10.42.255.249'
# Latest videoFrame object from AioRTC
latestVideoFrame = None

# AioRTC PcObject
globalPcObject = None
# Ping pong object to track active connection, if above 3 seconds, assume connection lost
pingPongTime = 0
# Process Frames?
processFrames = False


# Open screen and audio buffer port, with only accepting traffic from passed through IP address
async def startReceivingScreenDataOverRTP(sdpObject):
    global thisServersIpAddress, latestVideoFrame, globalPcObject, pingPongTime
    
    sdpObjectText = await sdpObject.text()
    sdpObjectOriginIP = sdpObject.remote
    
    print("=== Got SDP Offer From " + sdpObjectOriginIP + " ===")
    
    # Check if request ip is clientIp and currentConnection is connected
    
    if (sdpObjectOriginIP == clientIP) and (currentConnection == 'connected'):
        
        print("=== Client ALLOWED, start RTC ===")
        # Create local peer object, set remote peer to clientSdpOfferSessionDescription
        stunServer = ("stun:" + thisServersIpAddress)
        serverPeer = RTCPeerConnection(configuration=RTCConfiguration(
            iceServers=[RTCIceServer(
                urls=[stunServer])]))
        
        globalPcObject = serverPeer
        
        serverPeer.addTransceiver('video', direction='recvonly')
        # If we can and are allowed to redirect audio, create pyaudio stream to write frames to
        if allowAudioRedirection == True:
            # Add transceiver
            serverPeer.addTransceiver('audio', direction='recvonly')
            # Initialize pyaudio stream
            pyFormat = pyaudio.paInt16
            pyChannels = 2
            pyRate = 48000
            myGlobals.pyAudioStream = myGlobals.pyAudioDevice.open(format=pyFormat, channels=pyChannels, rate=pyRate, output=True, frames_per_buffer=4800)
            
        clientSdpOfferSessionDescription = RTCSessionDescription(sdpObjectText, 'offer')
        print("Got SDP offer from client, generating response SDP")
            
        await serverPeer.setRemoteDescription(clientSdpOfferSessionDescription)
        
        # Create answer
        clientAnswer = await serverPeer.createAnswer()
        
        # Set answer to local description
        await serverPeer.setLocalDescription(clientAnswer)
        
        print("Generated SDP response, returning")
        
        # Schedule task to run to gather frames
        async def processVideoFrames():
            global latestVideoFrame, globalPcObject, processFrames, allowAudioRedirection
            # Wait one second for sctp to establish
            await asyncio.sleep(1)
            receivers = serverPeer.getReceivers()
            lastFrame = time.time()
            processFrames = True
        
            for rec in receivers:
                # Wrap over video and audio receivers, grab frames from each
                    if rec.track.kind == "video":
                        while processFrames:
                            # Wrap in try statement, if Exception ignore
                            try:
                                # Load video, wrap aronud timeout so we don't block forever, 5 seconds
                                latestVideoFrame = await asyncio.wait_for(rec.track.recv(), timeout=5.0)
                                # Below is frame delay calculations to see it, make it into a debug mode someday
                                # calc = time.time() - lastFrame
                                # lastFrame = time.time()
                                # print("Got frame, time diff: " + str(calc))
                                    
                            except Exception as e:
                                print("MediaPlayer Failed, " + str(e))
                                await globalPcObject.close()
                                processFrames = False
                                setInitalValues()
                        
        async def processAudioFrames():
            global latestVideoFrame, globalPcObject, processFrames, allowAudioRedirection
            # Wait one second for sctp to establish
            await asyncio.sleep(1)
            receivers = serverPeer.getReceivers()
            lastFrame = time.time()
            processFrames = True
                        
            for rec in receivers:
                if rec.track.kind == "audio":
                    while processFrames == True:
                        # Wrap in try statement, if Exception ignore
                        try:
                            # Load video, wrap aronud timeout so we don't block forever, 5 seconds
                            latestAudioFrame = await asyncio.wait_for(rec.track.recv(), timeout=5.0)
                            # calc = time.time() - lastFrame
                            # lastFrame = time.time()
                            # print("Got frame, time diff: " + str(calc))
                                                        
                            # Write to pyAudioBufferQueue
                            audioBuffer = numpy.frombuffer(latestAudioFrame.to_ndarray(), dtype=numpy.int16)
                                    
                            # Write to stream device
                            myGlobals.pyAudioStream.write(audioBuffer.tobytes())
                            
                        except Exception as e:
                            print("AudioMediaPlayer Failed, pass, " + str(e))
                            processFrames = False
                            # Close audio stream
                            time.sleep(0.2)
                            myGlobals.pyAudioStream.stop_stream()
                            myGlobals.pyAudioStream.close()
                            # myGlobals.pyAudioDevice.terminate()
                        
        # Create frame ingest tasks                            
        asyncio.create_task(processVideoFrames())
        if allowAudioRedirection:
            asyncio.create_task(processAudioFrames())
        
        # Return SDP
        return web.Response(content_type="text/html", text=serverPeer.localDescription.sdp)
                
    else:
        print("=== Client DENIED, notAuthorized ===")
        # 418 Teapot, 401 not authorized
        return web.Response(content_type="text/html", status=418, text="response:notAuthorized")


# Read configuration file, set global variables based on that
def readConfigurationFile():
    global allowAudioRedirection, usePINAuthentication, allowedPskList
    print("=== Reading Configuration Data ===")
    try:
        with open('simpleCastConfig.json') as config_file:
            jsonObject = json.load(config_file)
        
            # Set server name based on JSON, if string is empty default to hostname
            if jsonObject['serverName'] == "":
                myGlobals.serverName = socket.gethostname()
            else:
                myGlobals.serverName = jsonObject['serverName']
                
            print("Server Name: " + str(myGlobals.serverName))
        
            # Check if PIN Authentication is enabled
            usePINAuthentication = jsonObject['usePINAuthentication']
            print("PIN Authentication: " + str(usePINAuthentication))
            
            # Check audio redirection
            allowAudioRedirection = jsonObject['allowAudioRedirection']
            print("Audio Redirection: " + str(allowAudioRedirection))
            allowAudioRedirection = True
            # Grab PSK List
            allowedPskList = jsonObject['allowedPskList']
            print("Allowed PSK List: " + str(allowedPskList))
            
            # Load slideshow images into variable, verify if file exists first
            verifyArray = jsonObject['slideshowPictures']
            for slideBack in verifyArray:
                # Make sure file exists in path, must be in backgrounds/
                absolutePath = 'backgrounds/' + slideBack
                if os.path.isfile(absolutePath):
                    # Exists, add to config
                    myGlobals.slideshowBackgrounds.append(absolutePath)
                else:
                    print("File does not exist, " + str(slideBack))
                    

    except Exception as e:
        print("Exception Reading From Config File, Follows: " + str(e))
        sys.exit()

# While sendBroadcastPacket, send one every two seconds
def sendBroadcastPacketWhileTrue():
    global currentConnection
    print("=== Broadcast Thread Started ===")
    # Open udp socket with IPV4 to send broadcast traffic on
    broadcastSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Bind socket to fixed port on all interfaces, port 1337. Clients must recieve on this port as well
    broadcastSocket.bind(('', 1337))
    
    # Enable the broadcast option on the socket (1) 
    broadcastSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    # While sendBroadcastPacket is true, will be false when client stops
    while sendBroadcastPacket:
        # Generate string to send to lan, has serverName and connection status
        broadcastDataString = (str(myGlobals.serverName) + "|" + str(currentConnection)).encode()
        
        # Send broadcast packet to entire subnet
        broadcastSocket.sendto(broadcastDataString, ("255.255.255.255", 1337))
        
        # Wait 2 seconds to repeat
        time.sleep(2)

    # When sendBroadcastPacket is False, close socket 
    broadcastSocket.close()
    
# Wait for connection, when we get one process PSK provided,
# If we use PIN Authentication, check if PSK is allowed, if not generate PIN
# Wait for client to send connect command, with or without pin
async def processHTTPCommand(commandRequest):
    global usePINAuthentication, allowedPskList, clientIP, currentConnection
                
    # Main loop, wait for connection on port, check if currentConnection is 'open'
    # If so continue, if not drop connection with 'error:connected'      
    
    textData = await commandRequest.text()
    thisClientIP = commandRequest.remote
    
    print("=== Got command: " + str(textData) + " from client " + str(thisClientIP) + " ===")
           
    # Split data recieved
    splitData = textData.split("|")
    
    # Check if command:statusProbe or command:attemptConnection    
    if splitData[0] == 'command:statusProbe':
        # Got a probe request, return wanted data,
        # serverName|serverStatus 
        returnString = (myGlobals.serverName + "|" + currentConnection)
            
        # Return string to client, break connection and reset
        return web.Response(content_type="text/html", text=returnString)

    # Process command, is it command:attemptConnection?
    elif (splitData[0] == 'command:attemptConnection'):
        
        # Set connectionTimer to current time
        myGlobals.connectionTimer = time.time()   
            
        # Print official connection information
        print('=========================================')
        print(splitData[1] + " is attempting to connect.")
        print("Client PSK Is " + str(splitData[2]))
        print('=========================================')
            
        # Set currentConnection to connecting
        currentConnection = 'connecting'
        clientIP = thisClientIP
        
        # Set hostname
        myGlobals.clientHostname = splitData[1]
                            
        # Repond to the client telling it what we can do
        # pinIfRequired|audioRedirection
            
        # Init empty response string                   
        responseString = ''
            
        # If PIN auth is enabled, process PSK to see if we need to use it
        if usePINAuthentication == True:
           
            # Check if PSK is in allowedList
            if splitData[2] in allowedPskList:
                # PIN auth not needed, set response string to reflect
                responseString = 'response|False|' + str(allowAudioRedirection)
                print('=========================================')
                print("No PIN Required, PSK Found")
                print('=========================================')
            else:
                # No PSK found, generate PIN
                myGlobals.generatedPin = str(random.randint(10000, 99999))
                responseString = 'response|True|' + str(allowAudioRedirection)
                print('=========================================')
                print("Connection PIN is: " + myGlobals.generatedPin)
                print('=========================================')

                                    
        else:
            # PIN auth disabled, allow client to connect automatically
            responseString = 'response|False|' + str(allowAudioRedirection)
            print('=========================================')
            print("PIN Auth disabled")
            print('=========================================')
                    
        # PIN Check done, return response telling if pin is required
        return web.Response(content_type="text/html", text=responseString)
                            
    # Expected next response, if no PIN was generated, then we don't need to check it, client can connect immediently              
                            
    elif splitData[0] == "command:connect":
        # Check if IP matches and currentConnection = 'connecting'
        if clientIP == thisClientIP and currentConnection == 'connecting':
            # Client is authorized
            loop = asyncio.get_event_loop()
            # Branch processing if we generated a PIN or no
            
            if myGlobals.generatedPin == "False":
                # PIN was not generated, so client can immediently connect
                currentConnection = 'connected'
                # # Start sending screen data
                print('--- No PIN Generated, Auto-Connecting ---')
                return web.Response(content_type="text/html", text="response:accepted")
              
            else:
                # PIN was generated, check if correct
                if splitData[1] == myGlobals.generatedPin:
                    # PIN Correct
                    print('--- PIN Accepted, connecting...')
                    currentConnection = 'connected'
                    return web.Response(content_type="text/html", text="response:accepted")
                else:
                    print('--- PIN REJECTED')
                    return web.Response(content_type="text/html", text="response:rejected")
                        
        else:
            # Client not authed, reject
            return web.Response(content_type="text/html", text="response:rejected")

  

# Seperate Threaded function that constantly updates the GUI
# open means show slideshow/time/ip/friendlyName
# connecting means show psk if one is generated and who is trying to connect
# connected means show frameBuffer
def pyGameConstantUpdating():
    global currentConnection, latestVideoFrame, globalPcObject, pingPongTime
    
    # Load display info
    displayInfo = pygame.display.Info()
    
    # Create black background image, so something is always drawn
    blackBackground = pygame.Surface((displayInfo.current_w, displayInfo.current_h))
    blackBackground.fill((0, 0, 0))
            
    # Create time font object
    font = pygame.font.Font(None, 40)
        
    # Constant check, wrap in while True for now
    # While thread is running
    while True:
        # Always draw black background as catch
        drawBlackCatchBackground(blackBackground)
        
        # Check currentConnection
        if currentConnection == 'open':
            # Should set these everytime we are open, just in case
            setInitalValues()
            
            # Draw slideShowBackground
            drawNextSlideShowFrameTick()
            
            # Draw Server Information
            pyGameDrawInformation(font)

            ## END OF OPEN
            
        elif currentConnection == 'connecting':
            # A client is connecting, same as open plus draw box in middle that shows PIN if required, if all 0's, just show host connecting
            
            # Calculate time difference
            # myGlobals.nearestConnectionInt
            
            # Draw slideShowBackground
            drawNextSlideShowFrameTick()
            
            # Draw information
            pyGameDrawInformation(font)
            
            # Draw PIN box with current host connecting
            drawConnectingInformation()
            
            ## END OF CONNECTING
            
        elif currentConnection == 'connected':
            # Have connection, take latestVideoFrame and convert to surface object to draw on screen
            # Wrap in try, in case of exception since latestVideoFrame is none by default
            try:
                # Transform VideoFrame object to RGB image in a bytearray                
                frameArray = latestVideoFrame.to_rgb().to_ndarray()
                # Make into a PyGame Surface
                frameSurface = pygame.surfarray.make_surface(frameArray)
                # Rotate 90 degrees to fix
                frameSurface = pygame.transform.rotate(frameSurface, 90)
                # Flip upsidedown to flip image
                frameSurface = pygame.transform.flip(frameSurface, False, True)
                # Resize surface to fit display by fixed height
                frameSurface = aspectRatioResizeFixedHeight(frameSurface)
                
                # Draw frameSurface to PyGame
                myGlobals.screenObject.blit(frameSurface, (0, 0))
                
            except Exception as e:
                # Called if latestVideoFrame is None usually, is ok to pass
                # print("Exception: " + str(e))
                pass

        # End of connection specific logic, all things drawn, now update display
        pygame.display.flip() 
    
    # Wrap around to while
        
# Initialize empty pygame window, hidden
def pygameInitializeBackgroundWaiting():
    # Initialize pygame
    pygame.init()
    
    # Change Window name and Icon
    programIcon = pygame.image.load('logo-pallete.png')
    pygame.display.set_icon(programIcon)
    
    # Set name
    pygame.display.set_caption("SimpleCast Receiver | " + str(myGlobals.serverName))
    
    # Set display mode
    myGlobals.screenObject = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    
    # Get display info
    displayInfo = pygame.display.Info() 
    
    # Make cursor invisible
    pygame.mouse.set_visible(False)
    
    # Start seperate thread to update screen depending on connectionStatus
    pyGameUpdateThread = Thread(target=pyGameConstantUpdating)
    pyGameUpdateThread.start()
        
# Set initial connection values, 
def setInitalValues():
    global currentConnection, clientIP
    # Reset connection to open
    currentConnection = 'open'
    # Reset client IP to empty
    clientIP = ''
    # Reset Generated PIN
    myGlobals.generatedPin = 'False'
    # Reset client hostname
    myGlobals.clientHostname = ''
    
# Initialize pyAudio
def pyAudioInit():
    myGlobals.pyAudioDevice = pyaudio.PyAudio()
    
        
# Program start
if __name__ == '__main__':
    # Read configuration data into memory
    readConfigurationFile()
    
    # Init audio
    pyAudioInit()
    
    # Initialize vars
    setInitalValues()
    
    # Initialize PyGame with Frame Update Thread
    pygameInitializeBackgroundWaiting()
    
    # Start seperate thread for broadcast packets
    broadcastThread = Thread(target=sendBroadcastPacketWhileTrue)
    broadcastThread.start()
    
    # Init AioHTTP Webapp
    app = web.Application()
    # Add route for client communication
    app.router.add_post("/command", processHTTPCommand)
    # Add route for client trying to attempt RTC connection
    app.router.add_post("/sdpOffer", startReceivingScreenDataOverRTP)

    # Start AioHTTP server on port 4825, wait for connection
    print("=== Opened HTTP port on 4825 ===")
    # Empty space
    print('')

    web.run_app(app, host='0.0.0.0', port=4825)    