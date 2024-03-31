import queue
# Init certain globals here, then can be imported
global screenObject, slideshowBackgrounds, serverName, slideShowTimer, slideshowIndexTracker, backgroundToDraw, oldBackground, fading, connectionTimer

# PyGame screen object
screenObject = None
slideshowBackgrounds = []

# slideShowTimer
slideShowTimer = 'f'
slideshowIndexTracker = 0
backgroundToDraw = ''
fading = False
oldBackground = ''
shuffleWallpapers = False
guiScale = "medium"

# Other
connectionTimer = 0
nearestConnectionInt = 20
connectionTimeOut = 20
serverName = 'noNameFoundSomethingIsWrong'
clientHostname = ''
generatedPin = 'False'
pyAudioDevice = None
pyAudioStream = None
pyAudioBufferQueue = None
isPaused = False
pauseSurface = None


# Having this instead of grabbing from an interface forces you to keep it static in some way
thisServersIpAddress = ""

# Resolution scale for decreasing current screen resolution by X factor
# Original is 1, half is 2, 3/4 is 3, 4 is 6/8?
resolutionScale = 1