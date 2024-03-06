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
