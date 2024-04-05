# PyGame screen objects
screenObject = None
slideshowBackgrounds = []
guiScale = 1

# slideShowTimer
slideShowTimer = 'f'
slideshowIndexTracker = 0
backgroundToDraw = ''
oldBackground = ''
shuffleWallpapers = False
fading = False

# Server Settings
serverName = 'noNameFoundSomethingIsWrong'
usePINAuthentication = True
allowAudioRedirection = False
allowedPskList = []
sendBroadcastPacket = True
slideshowAlphaStepdown = 5
infoScreenConnectionText = 'default'


# Other
connectionTimer = 0
nearestConnectionInt = 20
connectionTimeOut = 20
clientHostname = ''
generatedPin = 'False'
pyAudioDevice = None
pyAudioStream = None
pyAudioBufferQueue = None
isPaused = False
pauseSurface = None
currentConnection = 'open'
clientIP = ''
latestVideoFrame = None
globalPcObject = None
processFrames = False
gotSDPResponse = False
connectedTime = 0
sigIntReceived = False
castingToggle = True


# Having this instead of grabbing from an interface forces you to keep it static in some way
thisServersIpAddress = ""

# Resolution scale for decreasing current screen resolution by X factor
# Original is 1, half is 2, 3/4 is 3, 4 is 6/8?
resolutionScale = 1