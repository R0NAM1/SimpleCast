import time, socket, json, os, random, struct, queue, ast, asyncio, pygame, sys, pyaudio, numpy, aiohttp_cors, signal, io, ipaddress
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from threading import Thread, active_count
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer, RTCDataChannel, RTCRtpCodecParameters
from aiortc.mediastreams import VideoFrame
from aiortc.contrib.media import MediaPlayer, MediaBlackhole, MediaStreamTrack, MediaRelay
from aiortc.rtcrtpsender import RTCRtpSender
from aiohttp import web
from datetime import datetime
from PIL import Image
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf

# SimpleCast specific imports
from slideshowObjects import drawBlackCatchBackground, drawStaticBackground, drawNextSlideShowFrameTick, aspectRatioResizeFixedHeight, aspectRatioResizeFixedWidth
from drawGuiObjects import drawConnectingInformation, pyGameDrawInformation, drawPausedScreen, drawDebugStats
from seleniumRemoveElements import removeApplicableElements
import myGlobals

class MyListener(ServiceListener):
    
    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        # Ignore service updates
        pass

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        for inadd in info.addresses:
            numIp = str(ipaddress.ip_address(inadd))
             # Ignore 127.0.0.1
            if numIp == '127.0.0.1':
                pass
            else:
                myGlobals.discoveredMdnsArray.remove(numIp)

    # If a service if found, add IP to discoveredMdnsArray
    
    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        for inadd in info.addresses:
            numIp = str(ipaddress.ip_address(inadd))
            # Ignore 127.0.0.1
            if numIp == '127.0.0.1':
                pass
            else:
                myGlobals.discoveredMdnsArray.append(numIp)
            
        

def logStringToFile(stringToWrite):
    # We can always open with a, it will create the file if it does not exist
    # Open file
    logFile = open("./simplecast.log", "a")
    
    # Get time and date in format ## Month/Day/Year 13:00 Action
    currentDateTime = datetime.now()
    currentDateTime = currentDateTime.strftime("%m/%d/%Y %H:%M")
    
    # Assemble final string
    finalLogString = "## " + currentDateTime + " | " + stringToWrite + "\r\n"
    
    logFile.write(finalLogString)
    
    # Close file
    logFile.close()
    
# Register Sigint handler
def sigint_handler(signum ,frame):
    logStringToFile('SigInt received, server should be shutting down!')
    
    myGlobals.sigIntReceived = True
    sys.exit(0)
    
# If GET, return 
async def respondDiscover(commandRequest):
    # textData = await commandRequest.text()
    thisClientIP = commandRequest.remote
    
    # print("GET DNS-SD from: " + str(thisClientIP))
    
    # Array of IP Addresses
    toSendArray = json.dumps(myGlobals.discoveredMdnsArray)

    return web.Response(content_type="text/html", status=200, text=toSendArray)



# If valid PSK, attempt to stop current globalPcObject and call setInitialValues
async def kickCurrentConnection(commandRequest):
    # Expects commandRequest text of 'command:kick|PSK'
    textData = await commandRequest.text()
    thisClientIP = commandRequest.remote
    
           
    # Split data recieved
    splitData = textData.split("|")
    if splitData[0] == 'command:kick':
        logStringToFile("Client " + str(thisClientIP) + " is trying to kick current connection")
        # Check if PSK exists, if not send 401
        if splitData[1] in myGlobals.allowedPskList:
            
            if myGlobals.currentConnection == 'open':
                logStringToFile("-- Not possible, no active connection")
                return web.Response(content_type="text/html", status=401, text="response:notConnected")
            else:
                
                logStringToFile("-- Valid PSK, kicking active connection")
                
                try:
                    await myGlobals.globalPcObject.close()
                except:
                    pass
                
                setInitalValues()
                return web.Response(content_type="text/html", status=200, text="response:clientKicked")
        
        else:
            # PSK Does not exist, cannot kick connection
            logStringToFile("-- Invalid PSK, doing nothing")
            return web.Response(content_type="text/html", status=401, text="response:notAuthorized")
    else:
        return web.Response(content_type="text/html", status=401, text="response:notValidCommand")

# If valid PSK, allow ability to toggle ability to cast
async def toggleCasting(commandRequest):
    # Expects commandRequest text of 'command:toggle|PSK'
    textData = await commandRequest.text()
    thisClientIP = commandRequest.remote
               
    # Split data recieved
    splitData = textData.split("|")
    if splitData[0] == 'command:toggleCast':
        logStringToFile("Client " + str(thisClientIP) + " is trying to toggle casting")
        # Check if PSK exists, if not send 401
        if splitData[1] in myGlobals.allowedPskList:
            
            if myGlobals.currentConnection == 'open':
                # If is open, continue
                pass
            else:
                # Not open, reset to open
                
                try:
                    await myGlobals.globalPcObject.close()
                except:
                    pass
                
                setInitalValues()
            
            
            logStringToFile("-- Valid PSK, toggling casting")

    
            # Toggle boolean
            if myGlobals.castingToggle == False:
                myGlobals.castingToggle = True
                return web.Response(content_type="text/html", status=200, text="response:enabledCasting")
            
            elif myGlobals.castingToggle == True:
                myGlobals.castingToggle = False
                return web.Response(content_type="text/html", status=200, text="response:disabledCasting")
    
        else:
            # PSK Does not exist, cannot kick connection
            logStringToFile("-- Invalid PSK, doing nothing")
            return web.Response(content_type="text/html", status=401, text="response:notAuthorized")
    else:
        return web.Response(content_type="text/html", status=401, text="response:notValidCommand")


# Open screen and audio buffer port, with only accepting traffic from passed through IP address
async def startReceivingScreenDataOverRTP(sdpObject):
    
    sdpObjectText = await sdpObject.text()
    sdpObjectOriginIP = sdpObject.remote
    
    logStringToFile("Got SDP Offer From " + sdpObjectOriginIP + ", checking if valid")
    myGlobals.gotSDPResponse = True
    
    # Check if request ip is clientIp and currentConnection is connected
    
    if (sdpObjectOriginIP == myGlobals.clientIP) and (myGlobals.currentConnection == 'connected'):
        
        logStringToFile("Client is ALLOWED, starting RTC")
        # Create local peer object, set remote peer to clientSdpOfferSessionDescription
        stunServer = ("stun:" + myGlobals.thisServersIpAddress)
        serverPeer = RTCPeerConnection(configuration=RTCConfiguration(
            iceServers=[RTCIceServer(
                urls=[stunServer])]))
        
        myGlobals.globalPcObject = serverPeer
        
        serverPeer.addTransceiver('video', direction='recvonly')
        # If we can and are allowed to redirect audio
        # Check if client is sending audio by checking SDP for m=audio
        if (myGlobals.allowAudioRedirection == True) and ("m=audio" in sdpObjectText):
            # Add transceiver
            serverPeer.addTransceiver('audio', direction='recvonly')
            # Initialize pyaudio stream
            pyFormat = pyaudio.paInt16
            pyChannels = 2
            pyRate = 48000
            myGlobals.pyAudioStream = myGlobals.pyAudioDevice.open(format=pyFormat, channels=pyChannels, rate=pyRate, output=True, frames_per_buffer=9600)
            
        clientSdpOfferSessionDescription = RTCSessionDescription(sdpObjectText, 'offer')
            
        await serverPeer.setRemoteDescription(clientSdpOfferSessionDescription)
        
        # Create answer
        clientAnswer = await serverPeer.createAnswer()
        
        # Set answer to local description
        await serverPeer.setLocalDescription(clientAnswer)
        
        # Schedule task to run to gather frames
        async def processVideoFrames():
                    
            # Wait one second for sctp to establish
            await asyncio.sleep(1)
            receivers = serverPeer.getReceivers()
            myGlobals.processFrames = True
            startTime = time.time()
        
            for rec in receivers:
                # Wrap over video and audio receivers, grab frames from each
                if rec.track.kind == "video":
                    while myGlobals.processFrames:
                        # Wrap in try statement, if Exception ignore
                        try:
                            # Load video, wrap aronud timeout so we don't block forever, 5 seconds
                            myGlobals.latestVideoFrame = await asyncio.wait_for(rec.track.recv(), timeout=5.0)
                            
                            # print("Got video frame: " + str(myGlobals.latestVideoFrame))
                            myGlobals.lastWebRTCVideoFrameReceived = time.time()
                            
                        except Exception as e:
                            # print("MediaPlayer Failed, " + str(e))
                            await myGlobals.globalPcObject.close()
                            myGlobals.processFrames = False
                            setInitalValues()
                            break
        
        async def processAudioFrames():
            # Wait one second for sctp to establish
            await asyncio.sleep(1)
            receivers = serverPeer.getReceivers()
            lastFrame = time.time()
            myGlobals.processFrames = True
                        
            for rec in receivers:
                if rec.track.kind == "audio":
                    # Get the first few as fast as possible.
                    for i in range(10):
                        await asyncio.wait_for(rec.track.recv(), timeout=0.05)
                        
                    while myGlobals.processFrames == True:
                        # Wrap in try statement, if Exception ignore
                        try:
                            # Load video, wrap aronud timeout so we don't block forever, 5 seconds
                            latestAudioFrame = await asyncio.wait_for(rec.track.recv(), timeout=5.0)
                            # print(latestAudioFrame)
                            calc = time.time() - lastFrame
                            lastFrame = time.time()
                            # print("Got audio frame, time diff: " + str(calc) + ", " + str(latestAudioFrame))
                                                        
                            # Write to pyAudioBufferQueue
                            audioBuffer = numpy.frombuffer(latestAudioFrame.to_ndarray(), dtype=numpy.int16)
                                    
                            # Write to stream device if unpaused
                            if myGlobals.isPaused == False:
                                myGlobals.pyAudioStream.write(audioBuffer.tobytes())
                            
                        except Exception as e:
                            # print("AudioMediaPlayer Failed, pass, " + str(e))
                            myGlobals.processFrames = False
                            # Close audio stream
                            time.sleep(0.2)
                            myGlobals.pyAudioStream.stop_stream()
                            myGlobals.pyAudioStream.close()
                            # If audioPlayer fails close stream
                            await myGlobals.globalPcObject.close()
                            # setInitalValues()
                            break
                            # myGlobals.pyAudioDevice.terminate()

        async def run_process_audio_frames():
            # Having video and audio in the same event loop effectively DDOSes the Video, doing this seems to at least make video network level quality.
            await processAudioFrames()

        if myGlobals.allowAudioRedirection:
            asyncio.create_task(asyncio.to_thread(asyncio.run, run_process_audio_frames()))
            asyncio.create_task(processVideoFrames())
        else:
            asyncio.create_task(processVideoFrames())
    
    
        # Return SDP
        return web.Response(content_type="text/html", text=serverPeer.localDescription.sdp)
                
    else:
        logStringToFile("Client DENIED, not Authorized")
        # 418 Teapot, 401 not authorized
        return web.Response(content_type="text/html", status=401, text="response:notAuthorized")

## Redo better later
# Read configuration file, set global variables based on that
def readConfigurationFile():
    logStringToFile('Server started, reading config file')
    try:
        with open('simpleCastConfig.json') as config_file:
            # Load into JSON object
            jsonObject = json.load(config_file)
        
            ############
            # Set server name based on JSON, if string is empty default to hostname
            if jsonObject['serverName'] == "":
                myGlobals.serverName = socket.gethostname()
            else:
                myGlobals.serverName = jsonObject['serverName']
                        
            ############
            # Check if PIN Authentication is enabled
            myGlobals.usePINAuthentication = jsonObject['usePINAuthentication']
            
            ############
            # Check audio redirection
            myGlobals.allowAudioRedirection = jsonObject['allowAudioRedirection']

            ############
            # Grab PSK List
            myGlobals.allowedPskList = jsonObject['allowedPskList']
            
            ############
            # Load slideshow images into variable, verify if file exists first
            verifyArray = jsonObject['slideshowPictures']
            
            for slideBack in verifyArray:
                # Check if starts with http, if so then treat as url
                
                if "http" in slideBack:
                    # URL
                    myGlobals.websiteBackgroundExists = True
                    
                    myGlobals.websiteScreenShotArray.append(None)
                    myGlobals.websiteScreenShotUrlArray.append(slideBack)
                    myGlobals.slideshowBackgrounds.append(slideBack)
                
                else: 
                    # File
                    # Make sure file exists in path, must be in backgrounds/
                    absolutePath = 'backgrounds/' + slideBack
                    if os.path.isfile(absolutePath):
                        # Exists, add to config
                        myGlobals.slideshowBackgrounds.append(absolutePath)
                    else:
                        logStringToFile(("File does not exist, " + str(slideBack)))
                    myGlobals.websiteScreenShotArray.append(None)
                    myGlobals.websiteScreenShotUrlArray.append(None)
                    
            # Check if myGlobals.websiteBackgroundExists is true, if so start selenuimScreenShotThread
            if myGlobals.websiteBackgroundExists == True:
                seleniumWebsiteScreenShotThreadObject = Thread(target=seleniumWebsiteScreenShotThread)
                seleniumWebsiteScreenShotThreadObject.start()
                
                    
            ############
            # # Read server IP from config
            myGlobals.thisServersIpAddress = jsonObject['serverIP']
            
            ############
            # Should shuffle slideshow?
            myGlobals.shuffleWallpapers = jsonObject['shuffleSlideshow']
            
            ############
            # Set GUI scale, three options, low, medium, high
            myGlobals.guiScale = jsonObject['connectionScreenScale']
            
            ############
            # Load countDownTime, default 20
            myGlobals.connectionTimeOut = jsonObject['countDownTime']
            
            ############
            # Load slideShowAlphaStepDown
            myGlobals.slideShowAlphaStepDown = jsonObject['slideshowAlphaStepdown']
            
            ############
            # Load sendBroadcastPacket
            myGlobals.sendBroadcastPacket = jsonObject['doBroadcastDiscovery']

            ############
            # Load infoScreenConnectionText
            myGlobals.infoScreenConnectionText = jsonObject['infoScreenConnectionText']
            
            ############
            # Load infoTextAlignment
            myGlobals.infoTextAlignment = jsonObject['infoTextAlignment']

            ############
            # Load enableWhitelist
            myGlobals.enableWhitelist = jsonObject['enableWhitelist']
            
            ############
            # Load whitelistArray
            myGlobals.whitelistArray = jsonObject['whitelistArray']
            
            ############
            # Load displayDebugStats
            myGlobals.displayDebugStats = jsonObject['displayDebugStats']
                    
            ############
            # Load doDnsSdDiscovery
            myGlobals.doDnsSdDiscovery = jsonObject['doDnsSdDiscovery']
                    
    except Exception as e:
        logStringToFile("Exception Reading From Config File, Follows: " + str(e))
        sys.exit()

# While sendBroadcastPacket, send one every two seconds
def sendBroadcastPacketWhileTrue():
    if myGlobals.sendBroadcastPacket:
        # Open udp socket with IPV4 to send broadcast traffic on
        broadcastSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Bind socket to fixed port on all interfaces, port 1337. Clients must recieve on this port as well
        broadcastSocket.bind(('', 1337))
        
        # Enable the broadcast option on the socket (1) 
        broadcastSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        # While sendBroadcastPacket is true, will be false when client stops
        while myGlobals.sendBroadcastPacket and myGlobals.sigIntReceived == False:
            # Generate string to send to lan, has serverName and connection status
            broadcastDataString = (str(myGlobals.serverName) + "|" + str(myGlobals.currentConnection)).encode()
            
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
                
    # Main loop, wait for connection on port, check if currentConnection is 'open'
    # If so continue, if not drop connection with 'error:connected'      
    
    textData = await commandRequest.text()
    thisClientIP = commandRequest.remote
    
    # logStringToFile("Got command: " + str(textData) + " from client " + str(thisClientIP))
           
    # Split data recieved
    splitData = textData.split("|")
    
    # Check if command:statusProbe or command:attemptConnection    
    if splitData[0] == 'command:statusProbe':
        # Got a probe request, return wanted data,
        # serverName|serverStatus 
        returnString = (myGlobals.serverName + "|" + myGlobals.currentConnection)
            
        # Return string to client, break connection and reset
        return web.Response(content_type="text/html", text=returnString)

    # Is client asking to pause?
    elif (splitData[0] == 'command:pause'):
        # Verify status is connected and clientIP Matches
        if (thisClientIP == myGlobals.clientIP) and (myGlobals.currentConnection == 'connected'):
            
            if myGlobals.isPaused == False:
            # Toggle isPaused
                myGlobals.isPaused = True
                return web.Response(content_type="text/html", status=200, text="response:paused")

            elif myGlobals.isPaused == True:
            # Toggle isPaused
                myGlobals.isPaused = False
                return web.Response(content_type="text/html", status=200, text="response:unpaused")

        else:
            return web.Response(content_type="text/html", status=401, text="response:notAuthorized")

    
    # Process command, is it command:attemptConnection?
    # Eventually change castingToggle to a status? Is a possibility
    elif (splitData[0] == 'command:attemptConnection') and myGlobals.currentConnection == 'open' and myGlobals.castingToggle == True:
        
        # Set connectionTimer to current time
        myGlobals.connectionTimer = time.time()   
            
        # Print official connection information
        logStringToFile(splitData[1] + " is attempting to connect.")
                            
        # Repond to the client telling it what we can do
        # pinIfRequired|audioRedirection
            
        # Init empty response string                   
        responseString = ''
            
        # Check if whitelist is enabled, if so overtake process
        
        if myGlobals.enableWhitelist == True:
            # Check if PSK is in whitelistArray
            if splitData[2] in myGlobals.whitelistArray:
                # PIN auth not needed, set response string to reflect
                
                # Set currentConnection to connecting
                myGlobals.currentConnection = 'connecting'
                myGlobals.clientIP = thisClientIP
                myGlobals.clientHostname = splitData[1]
                
                responseString = 'response|False|' + str(myGlobals.allowAudioRedirection) + "|" + str(myGlobals.connectionTimeOut)
                
        
        else:
                
            # If PIN auth is enabled, process PSK to see if we need to use it
            if myGlobals.usePINAuthentication == True:
            
                # Check if PSK is in allowedList
                if splitData[2] in myGlobals.allowedPskList:
                    # PIN auth not needed, set response string to reflect
                    
                    # Set currentConnection to connecting
                    myGlobals.currentConnection = 'connecting'
                    myGlobals.clientIP = thisClientIP
                    myGlobals.clientHostname = splitData[1]
                    
                    responseString = 'response|False|' + str(myGlobals.allowAudioRedirection) + "|" + str(myGlobals.connectionTimeOut)
                else:
                    # No PSK found, generate PIN
                    
                    # Set currentConnection to connecting
                    myGlobals.currentConnection = 'connecting'
                    myGlobals.clientIP = thisClientIP
                    myGlobals.clientHostname = splitData[1]
            
                    myGlobals.generatedPin = str(random.randint(10000, 99999))
                    responseString = 'response|True|' + str(myGlobals.allowAudioRedirection) + "|" + str(myGlobals.connectionTimeOut)

                                        
            else:
                # PIN auth disabled, allow client to connect automatically
                
                # Set currentConnection to connecting
                myGlobals.currentConnection = 'connecting'
                myGlobals.clientIP = thisClientIP
                myGlobals.clientHostname = splitData[1]
                
                responseString = 'response|False|' + str(myGlobals.allowAudioRedirection) + "|" + str(myGlobals.connectionTimeOut)
                        
        # PIN Check done, return response telling if pin is required
        return web.Response(content_type="text/html", text=responseString)
                            
    # Expected next response, if no PIN was generated, then we don't need to check it, client can connect immediently              
                            
    elif (splitData[0] == "command:connect") and (myGlobals.currentConnection == 'connecting'):
        # Check if IP matches and currentConnection = 'connecting'
        if myGlobals.clientIP == thisClientIP and myGlobals.currentConnection == 'connecting':
            # Client is authorized
            loop = asyncio.get_event_loop()
            # Branch processing if we generated a PIN or no
            
            if myGlobals.generatedPin == "False":
                # PIN was not generated, so client can immediently connect
                myGlobals.currentConnection = 'connected'
                # # Start sending screen data
                logStringToFile('No PIN Generated, Allowing Connection')
                myGlobals.connectedTime = time.time()
                return web.Response(content_type="text/html", text="response:accepted")
              
            else:
                # PIN was generated, check if correct
                if splitData[1] == myGlobals.generatedPin:
                    # PIN Correct
                    logStringToFile('PIN Accepted, connecting')
                    myGlobals.currentConnection = 'connected'
                    myGlobals.connectedTime = time.time()
                    return web.Response(content_type="text/html", text="response:accepted")
                else:
                    logStringToFile('PIN Rejected')
                    setInitalValues()
                    return web.Response(content_type="text/html", text="response:rejected")
                        
        else:
            # Client not authed, reject
            return web.Response(content_type="text/html", text="response:rejected")

  

# Seperate Threaded function that constantly updates the GUI
# open means show slideshow/time/ip/friendlyName
# connecting means show psk if one is generated and who is trying to connect
# connected means show frameBuffer
def pyGameConstantUpdating():
    
    # Load display info
    displayInfo = pygame.display.Info()
    
    # Create black background image, so something is always drawn
    blackBackground = pygame.Surface((displayInfo.current_w, displayInfo.current_h))
    blackBackground.fill((0, 0, 0))
            
    # Create time font object
    font = pygame.font.Font(None, round(40 * myGlobals.guiScale))
        
    # Constant check, wrap in while True for now
    # While thread is running
    while myGlobals.sigIntReceived == False:
        # Always draw black background to catch any pixels not drawn previously (Move to connected?)
        drawBlackCatchBackground(blackBackground)
        
        # Check currentConnection
        if myGlobals.currentConnection == 'open':
            # Should set these everytime we are open, just in case
            setInitalValues()
            
            # Draw slideShowBackground
            drawNextSlideShowFrameTick(displayInfo)
            
            # Draw Server Information # DO myGlobals.castingToggle == True
            pyGameDrawInformation(font)

            ## END OF OPEN
            
        elif myGlobals.currentConnection == 'connecting':
            # A client is connecting, same as open plus draw box in middle that shows PIN if required, if all 0's, just show host connecting
            
            
            # Draw slideShowBackground
            drawNextSlideShowFrameTick(displayInfo)
            
            # Draw information
            pyGameDrawInformation(font)
            
            # Draw PIN box with current host connecting
            drawConnectingInformation()
            
            # Check if nearestConnectionInt is at or below 0, if so then set connection back to open
            if (myGlobals.nearestConnectionInt <= 0):
                    setInitalValues()
                    
            ## END OF CONNECTING
            
        elif myGlobals.currentConnection == 'connected':
            # Have connection, take latestVideoFrame and convert to surface object to draw on screen
            # Wrap in try, in case of exception since latestVideoFrame is none by default
            
            # Check if paused, if so draw a paused screen
            if myGlobals.isPaused:
                drawPausedScreen(displayInfo)
            else:
                # By default draw latest video frame from aiortc, worst case errors out when latestVideoFrame is non (AKA Black)
                try:
                    # Transform VideoFrame object to RGB image in a bytearray                
                    frameArray = myGlobals.latestVideoFrame.to_rgb().to_ndarray()
                    # Make into a PyGame Surface
                    frameSurface = pygame.surfarray.make_surface(frameArray)
                    # Rotate 90 degrees to fix
                    frameSurface = pygame.transform.rotate(frameSurface, 90)
                    # Flip upsidedown to flip image
                    frameSurface = pygame.transform.flip(frameSurface, False, True)
                    
                    originX = 0
                    originY = 0
                    
                    # If height is bigger then width, resize by height
                    if (frameSurface.get_height() > frameSurface.get_width()):
                        frameSurface = aspectRatioResizeFixedHeight(frameSurface)
                        # Set originX to be in the middle, displayWidth - FrameWidth = Difference, (Difference / 2)
                        coordDifference = (displayInfo.current_w - frameSurface.get_width())
                        if coordDifference > 0:
                            originX = (coordDifference / 2)
                    
                    # If width is bigger then height, resize by width
                    elif (frameSurface.get_width() > frameSurface.get_height()):
                        frameSurface = aspectRatioResizeFixedWidth(frameSurface)
                        # Set originY to be in the middle, displayHeight - FrameHeight = Difference, (Difference / 2)
                        coordDifference = (displayInfo.current_h - frameSurface.get_height())
                        if coordDifference > 0:
                            originY = (coordDifference / 2)
                    
                    # Set paused surface
                    myGlobals.pauseSurface = frameSurface
                    
                    # Draw frameSurface to PyGame
                    myGlobals.screenObject.blit(frameSurface, (originX, originY))
                    
                except Exception as e:
                    # Called if latestVideoFrame is None usually, is ok to pass
                    # print("Exception: " + str(e))
                    pass
                
            # If connected for more then connectionTimeOut seconds and gotSDPResponse is false, set back to open
            if (time.time() - myGlobals.connectedTime > myGlobals.connectionTimeOut) and (myGlobals.gotSDPResponse == False):
                setInitalValues()

        if myGlobals.displayDebugStats == True:
            drawDebugStats()

        # End of connection specific logic, all things drawn, now update display
        pygame.display.flip()
        
        myGlobals.timeLastFrameDrawn = time.time()
        
        # Check if pygame event quit was received
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Got pygame quit, call sigIntReceived
                myGlobals.sigIntReceived = True
                
    # Primary Loop, check if myGlobals.sigIntReceived is True
    if myGlobals.sigIntReceived == True:
        
        myGlobals.pyAudioDevice.terminate()
        pygame.quit()
        sys.exit()
        
    
    # Wrap around to while
##############################
        
def seleniumWebsiteScreenShotThread():
    # Wait for pygame to start
    time.sleep(5)
    # Wanted to use Firefox but for some reason the page would never load, got stuck at
    # driver.get, geckodriver being installed didn't help either, at least chrome works!
    # Use in new headless mode to load extensions, namely ublock and dark reader
    
    # While program is running
    while myGlobals.sigIntReceived == False:
        myGlobals.isSeleniumTakingScreenShots = True
        # Itterate over websiteScreenShotUrlArray
        thisIndex = 0
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--hide-scrollbars')
        
        # Need to add user agent or else we get 403's
        options.add_argument("user-agent=Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36")

        service = webdriver.ChromeService(executable_path='/usr/bin/chromedriver')
        
        # Load extensions, ublock origin for ads and dark reader to make it NOT blinding by default
        # Extensions got from github repos and repacked in local browser
        # To load your own extensions, add them as crx files to this folder
        for extensionFile in os.listdir('./seleniumChromeExtensions/'):
            fileName = os.fsdecode(extensionFile)
            # Check if crx file, if so load as extension
            if ('.crx') in fileName:
                options.add_extension('./seleniumChromeExtensions/' + fileName)
            else:
                logStringToFile(fileName + " is not a CRX file")

        time.sleep(1)

        try:
            driver = webdriver.Chrome(service=service, options=options)
            # Have had issues with window size while headless, needs to be less then current screen resolution, so take away 10, then resize with PIL
            driver.set_window_size((myGlobals.screenObject.get_width() * 0.80), (myGlobals.screenObject.get_height() * 0.80))
            
            for websiteUrl in myGlobals.websiteScreenShotUrlArray:
                if websiteUrl == None:
                    pass
                else:
                    # Valid url in index, create new driver
                    # print("=== Grabbing screenshot of " + websiteUrl + " ===")
                    driver.get(websiteUrl)
                    # print("== Website Loaded == ")
                    # Do element processing if applicable
                    removeApplicableElements(driver, websiteUrl)
                    
                    # Grab screenshot and convert from png to rgba
                    screenShotPngPillow = Image.open(io.BytesIO(driver.get_screenshot_as_png()))
                                    
                    # Resize
                    screenShotPngPillow = screenShotPngPillow.resize((myGlobals.screenObject.get_width(), myGlobals.screenObject.get_height()))
                    
                    # Convert to RGBA
                    screenShotRGBA = screenShotPngPillow.convert('RGBA')
                    
                    # Store screenshot in memory
                    myGlobals.websiteScreenShotArray[thisIndex] = (screenShotRGBA.tobytes())
                    # print("== Finished ScreenShot Processing ==")
                    
                thisIndex += 1
            
            # Close driver
            driver.quit()
            myGlobals.isSeleniumTakingScreenShots = False
            time.sleep(60)
        except Exception as e:
            myGlobals.isSeleniumTakingScreenShots = False
                      
            print(e)
                        
            try:
                driver.quit()
            except:
                pass
            
            time.sleep(10)
            
# Init pygame and start drawing thread
# Does not work on multiple monitors, pygame limitation?
def pygameInitializeBackgroundWaiting():
    # Initialize pygame
    pygame.init()
    
    # Change Window name and Icon
    programIcon = pygame.image.load('../logo-pallete.png')
    pygame.display.set_icon(programIcon)
    
    # Set name
    pygame.display.set_caption("SimpleCast Receiver | " + str(myGlobals.serverName))
    
    # Set display mode
    myGlobals.screenObject = pygame.display.set_mode((0, 0), pygame.FULLSCREEN, vsync=1)
    
    # Get display info
    displayInfo = pygame.display.Info() 
    
    # Make cursor invisible
    pygame.mouse.set_visible(False)
    
    # Move onto main thread forever loop        
    pyGameConstantUpdating()
        
# Set initial connection values, meant to reset program to a starting state where nobody is connected. 
def setInitalValues():
    # Reset connection to open
    myGlobals.currentConnection = 'open'
    # Reset client IP to empty
    myGlobals.clientIP = ''
    # Reset Generated PIN
    myGlobals.generatedPin = 'False'
    # Reset client hostname
    myGlobals.clientHostname = ''
    # Reset latestVideoFrame so last frame isn't carried over
    myGlobals.latestVideoFrame = None
    # Change gotSDPResponse
    myGlobals.gotSDPResponse = False
    
# Initialize pyAudio
def pyAudioInit():
    if myGlobals.allowAudioRedirection == True:
        myGlobals.pyAudioDevice = pyaudio.PyAudio()
        
# mDNS Discovery Thread
def dnsSdThread():
    # Do Dns SD Things
    zeroconf = Zeroconf()
    listener = MyListener()
    browser = ServiceBrowser(zeroconf, "_simplecast._tcp.local.", listener)
        
    while myGlobals.sigIntReceived == False:
        time.sleep(60)
    # Loop stopped, close zeroconf 
    zeroconf.close()
    
async def runHTTP():
     # Init AioHTTP Webapp
    app = web.Application()
    
    # CORS Setup, because it is needed.
    cors = aiohttp_cors.setup(app, defaults={
    "*": aiohttp_cors.ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*",
        max_age=3600,
    )
    })
    
    # Add route for client communication, meant for main connection commands
    commandResource = cors.add(app.router.add_resource("/command"))
    cors.add(commandResource.add_route("POST", processHTTPCommand))
    
    # Add route for client trying to attempt RTC connection
    sdpOfferResource = cors.add(app.router.add_resource("/sdpOffer"))
    cors.add(sdpOfferResource.add_route("POST", startReceivingScreenDataOverRTP))
    
    # Add route for kicking current connection
    kickResource = cors.add(app.router.add_resource("/kick"))
    cors.add(kickResource.add_route("POST", kickCurrentConnection))
    
    # Add route for toggling ability to cast
    toggleResource = cors.add(app.router.add_resource("/toggle"))
    cors.add(toggleResource.add_route("POST", toggleCasting))
    
    # If myGlobals.doDnsSdDiscovery is true, add route for returning mdns and add thread to do discovery?
    if myGlobals.doDnsSdDiscovery == True:
        dnsSdThreadOb = Thread(target=dnsSdThread)
        dnsSdThreadOb.start()
    
        dnsSdResource = cors.add(app.router.add_resource("/discover"))
        cors.add(dnsSdResource.add_route("GET", respondDiscover))
    
    # Start AioHTTP server on port 4825, wait for connection
    logStringToFile('Server and AioHTTP started')
    # web.run_app(app, host='0.0.0.0', port=4825)
    runner = web.AppRunner(app)
    
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', 4825)
    await site.start() 
        
# Program start
if __name__ == '__main__':
    # Register Sigint handler
    signal.signal(signal.SIGINT, sigint_handler)
    signal.signal(signal.SIGTERM, sigint_handler)
    
    # Read configuration data into memory
    readConfigurationFile()
    
    # Attempt to init audio
    pyAudioInit()
    
    # Initialize vars
    setInitalValues()
    
    
    # Start seperate thread for broadcast packets
    # broadcastThread = Thread(target=sendBroadcastPacketWhileTrue)
    # broadcastThread.start()
    
    # Run aioHTTP in asyncronous mode forever
    httpLoop = asyncio.new_event_loop()
    asyncio.set_event_loop(httpLoop)
    httpLoop.create_task(runHTTP())
    # Run forever in seperate thread
    httpThread = Thread(target=httpLoop.run_forever)
    httpThread.start()
    
    # Initialize PyGame and continue to run in main thread
    pygameInitializeBackgroundWaiting()