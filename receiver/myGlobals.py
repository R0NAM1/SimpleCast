import time

# PyGame screen objects
screenObject = None
slideshowBackgrounds = []
guiScale = 1

# slideShowStuff
slideShowTimer = 'f'
slideshowIndexTracker = 0
backgroundToDraw = ''
oldBackground = ''
shuffleWallpapers = False
fading = False
# Will mirror slideshowPictures, all local will be None for padding, while all http will be image
websiteScreenShotArray = []
websiteScreenShotUrlArray = []
websiteBackgroundExists = False

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
lastFlipTime = time.time()
isScreenFlipped = False
infoTextAlignment = 'flip'

# Debug vars
displayDebugStats = False
debugSlowdownTime = time.time()
timeLastFrameDrawn = time.time()
lastWebRTCVideoFrameReceived = time.time()
# Audio not needed, mirrors video
isSeleniumTakingScreenShots = False
# Display res
# Current State 'open'
# WebRTC Resolution

# Debug surfaces
fpsSurface = None
stateSurface = None
videoSurface = None
seleniumSurface = None
resolutionSurface = None
rtcResolutionSurface = None

# Having this instead of grabbing from an interface forces you to keep it static in some way
thisServersIpAddress = ""

# Resolution scale for decreasing current screen resolution by X factor
# Original is 1, half is 2, 3/4 is 3, 4 is 6/8?
resolutionScale = 1