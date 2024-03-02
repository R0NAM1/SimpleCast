import time, socket, json, os, random, struct, queue, ast, asyncio
from threading import Thread, active_count
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer, RTCDataChannel, RTCRtpCodecParameters
from aiortc.mediastreams import VideoFrame
from aiortc.contrib.media import MediaPlayer, MediaBlackhole, MediaStreamTrack, MediaRelay
from aiortc.rtcrtpsender import RTCRtpSender
from aiohttp import web


global clientIP, generatedPin, thisServersIpAddress, sendBroadcastPacket, allowAudioRedirection, usePINAuthentication, allowedPskList, serverName, currentConnection

sendBroadcastPacket = True

# This server should be set at a static address, the 'public' one that will be used on your network

thisServersIpAddress = '10.42.0.8'

# Audio Redirection default is false
allowAudioRedirection = False

# Default to true
usePINAuthentication = True

# Initialize PSK List
allowedPskList = []

# Default to noName
serverName = 'noNameFoundSomethingIsWrong'

# Current connection information,
# 'open' by default, 'connecting' for client connecting, 'connected' for client being connected

currentConnection = 'open'

generatedPin = 'False'
clientIP = ''

# Open screen and audio buffer port, with only accepting traffic from passed through IP address
async def startReceivingScreenDataOverRTP(sdpObject):
    global thisServersIpAddress
    
    sdpObjectText = await sdpObject.text()
    sdpObjectOriginIP = sdpObject.remote
    
    print("=== Got SDP Offer From " + sdpObjectOriginIP + " ===")
    
    # Check if request ip is clientIp and currentConnection is connected
    
    if (sdpObjectOriginIP == clientIP) and (currentConnection == 'connected'):
        
        print("=== Client ALLOWED, start RTC ===")
                
        stunServer = RTCIceServer(
            # urls=["stun:" + thisServersIpAddress]
            urls=["stun:10.42.0.8"]
        )
        
        config = RTCConfiguration(
            iceServers=[stunServer]
        )
        
        
        # Create local peer object, set remote peer to clientSdpOfferSessionDescription
        serverPeer = RTCPeerConnection(configuration=config)
        
        @serverPeer.on("datachannel")
        def on_datachannel(channel):
            print("Data channel received.")
        
            # Set up event listeners for the incoming data channel
            @channel.on("open")
            def on_open():
                print("Data channel is open. Waiting for message")
                # channel.send("Hello from the server!")
            
            @channel.on("message")
            def on_message(message):
                print(f"Message received: {message}")
                print("Responding")
                channel.send("Hello from server!")
            
        @serverPeer.on("track")
        def onTrack(track):
            print("Got track: " + str(track.kind))
            # DOES NOT WORK, I don't know why
            # @track.on("frame")
            # def on_frame(frame):
            #     # This function will be called when a frame is received
            #     print("Received frame: " + str(frame))
        
        serverPeer.addTransceiver('video', direction='recvonly')

        clientSdpOfferSessionDescription = RTCSessionDescription(sdpObjectText, 'offer')
        print("Got SDP offer from client, generating response SDP")
        
        print("Loading into RTCSessionDescription")
        
        await serverPeer.setRemoteDescription(clientSdpOfferSessionDescription)
        
        # Create answer
        clientAnswer = await serverPeer.createAnswer()
        
        # Set answer to local description
        await serverPeer.setLocalDescription(clientAnswer)
        
        print("Generated SDP response, returning")
                
        print("State:")
        print(serverPeer.sctp.state)
        
        # Schedule task to run to gather frames
        
        async def processFrames():
            print("Start process frames")
            receivers = serverPeer.getReceivers()
        
            for rec in receivers:
                if rec.track.kind == "video":
                    while True:
                        print("Waiting for frame")
                        frame = await rec.track.recv()
                        print("Frame:")
                        print(frame)
            
        # Create said task under this request
        sdpObject.app.loop.create_task(processFrames())
        
        # Return SDP
        return web.Response(content_type="text/html", text=serverPeer.localDescription.sdp)
                
    else:
        print("=== Client DENIED, notAuthorized ===")
        return web.Response(content_type="text/html", status=401, text="response:notAuthorized")

    
    
    
    
    

    pass

# Read configuration file, set global variables based on that
def readConfigurationFile():
    global allowAudioRedirection, usePINAuthentication, allowedPskList, serverName
    print("=== Reading Configuration Data ===")
    try:
        with open('simpleCastConfig.json') as config_file:
            jsonObject = json.load(config_file)
        
            # Set server name based on JSON, if string is empty default to hostname
            if jsonObject['serverName'] == "":
                serverName = socket.gethostname()
            else:
                serverName = jsonObject['serverName']
                
            print("Server Name: " + str(serverName))
        
            # Check if PIN Authentication is enabled
            usePINAuthentication = jsonObject['usePINAuthentication']
            print("PIN Authentication: " + str(usePINAuthentication))
            
            # Check audio redirection
            allowAudioRedirection = jsonObject['allowAudioRedirection']
            print("Audio Redirection: " + str(allowAudioRedirection))

            # Grab PSK List
            allowedPskList = jsonObject['allowedPskList']
            print("Allowed PSK List: " + str(allowedPskList))

    except Exception as e:
        print("Exception Reading From Config File, Follows: " + str(e))


# While sendBroadcastPacket, send one every two seconds
def sendBroadcastPacketWhileTrue():
    global serverName, currentConnection
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
        broadcastDataString = (str(serverName) + "|" + str(currentConnection)).encode()
        
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
    global usePINAuthentication, allowedPskList, generatedPin, clientIP, serverName, currentConnection
                
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
        returnString = (serverName + "|" + currentConnection)
            
        # Return string to client, break connection and reset
        return web.Response(content_type="text/html", text=returnString)

    # Process command, is it command:attemptConnection?
    elif (splitData[0] == 'command:attemptConnection'):
            
        # Print official connection information
        print('=========================================')
        print(splitData[1] + " is attempting to connect.")
        print("Client PSK Is " + str(splitData[2]))
        print('=========================================')
            
        # Set currentConnection to connecting
        currentConnection = 'connecting'
        clientIP = thisClientIP
                            
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
                generatedPin = str(random.randint(10000, 99999))
                responseString = 'response|True|' + str(allowAudioRedirection)
                print('=========================================')
                print("Connection PIN is: " + generatedPin)
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
            
            if generatedPin == "False":
                # PIN was not generated, so client can immediently connect
                currentConnection = 'connected'
                # # Start sending screen data
                print('--- No PIN Generated, Auto-Connecting ---')
                return web.Response(content_type="text/html", text="response:accepted")
                # loop.run_until_complete(startReceivingScreenDataOverRTP(address[0], connectionObject))
                # loop.run_forever()
                pass
              
            else:
                # PIN was generated, check if correct
                if splitData[1] == generatedPin:
                    # PIN Correct
                    print('--- PIN Accepted, connecting...')
                    currentConnection = 'connected'
                    return web.Response(content_type="text/html", text="response:accepted")
                    # loop.run_until_complete(startReceivingScreenDataOverRTP(address[0], connectionObject))
                    # loop.run_forever()
                else:
                    print('--- PIN REJECTED')
                    return web.Response(content_type="text/html", text="response:rejected")
                        
        else:
            # Client not authed, reject
            return web.Response(content_type="text/html", text="response:rejected")
# Program start
if __name__ == '__main__':
    # Read configuration data into memory
    readConfigurationFile()
    
    # Start seperate thread for broadcast packets, eventually make async
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