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

# Other
connectionTimer = 0
serverName = 'noNameFoundSomethingIsWrong'
clientHostname = ''
generatedPin = 'False'

