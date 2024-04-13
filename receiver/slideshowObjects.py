import time, pygame, random

# Import globals
import myGlobals

# Scale surface to screen with fixed width
def aspectRatioResizeFixedWidth(surface):
    displayInfo = pygame.display.Info()
    
    # Find difference between screen height and image height
    widthDiff = (displayInfo.current_w / surface.get_width())

    # Generate new width of 'surface' based on height difference
    newHeight = int(surface.get_height() * widthDiff)

    # Transform surface
    scaledSurface = pygame.transform.scale(surface, (displayInfo.current_w, newHeight))
    
    # Return scaled surface
    return scaledSurface

# Scale surface to screen with fixed height
def aspectRatioResizeFixedHeight(surface):
    displayInfo = pygame.display.Info()
    
    # Find difference between screen height and image height
    heightDiff = (displayInfo.current_h / surface.get_height())

    # Generate new width of 'surface' based on height difference
    newWidth = int(surface.get_width() * heightDiff)

    # Transform surface
    scaledSurface = pygame.transform.scale(surface, (newWidth, displayInfo.current_h))
    
    # Return scaled surface
    return scaledSurface

# Load image uri into memory, scale too
def loadImageOntoSurface(imageUri, thisIndex):
    if 'http' in imageUri:
        try:
            # print("Loading HTTP Screenshot")
            # Grab image from websiteScreenShotArray
            loadedSurface = pygame.image.frombytes(myGlobals.websiteScreenShotArray[thisIndex], (myGlobals.screenObject.get_width(), myGlobals.screenObject.get_height()), 'RGBA').convert()   
            
            # Return loaded and scaled surface object
            return loadedSurface
        except Exception as e:
            # IF fails, load 'could not capture' image
            # print("Loading 404 Image")
            # print(e)
            # Load URI into 
            loadedSurface = pygame.image.load('404.png').convert()
            
            # Return loaded and scaled surface object
            return loadedSurface
    
    else:
        # print("Loading Local Image")
        # Load URI into 
        loadedSurface = pygame.image.load(imageUri).convert()
        
        # Convert surface into correct aspect ratio and resolution
        loadedSurface = aspectRatioResizeFixedWidth(loadedSurface)
        
        # Return loaded and scaled surface object
        return loadedSurface



# Tick function
def drawBlackCatchBackground(backgroundCatch):
    # Draw a black background so if scaling is weird we dont show any previous draw
    # Expect existing pygame surface, 
    
    # Blit into screen
    myGlobals.screenObject.blit(backgroundCatch, (0, 0))
    
# Tick function
def drawStaticBackground(backgroundImage):
    # Draw a static background onto the myGlobals.screenObject
    # background image expects pygame.image.load('background.jpg').convert()
    
    myGlobals.screenObject.blit(backgroundImage, (0, 0))
    
# Tick function
def drawNextSlideShowFrameTick(displayInfo):
    
    # If come in at start, draw initial frame
    # Every tick check if 10 seconds have passed, if so set fade to true
    # While fade, draw new frame then old frame with lowering alpha every tick
    # One opacity hits zero, start drawing only one frame    
    
    # This function is constantly called
    
    # if slideshow timer is 'f' is first draw, set myGlobals.slideShowTimer
    if myGlobals.slideShowTimer == 'f':
        # Load first slideshow in array to backgroundSurface
        
        myGlobals.newX = 0
        myGlobals.newX = 0
        
        myGlobals.backgroundToDraw = loadImageOntoSurface(myGlobals.slideshowBackgrounds[0], 0)
        
        # If height is bigger then width, resize by height
        if (myGlobals.backgroundToDraw.get_height() > myGlobals.backgroundToDraw.get_width()):
            myGlobals.backgroundToDraw = aspectRatioResizeFixedHeight(myGlobals.backgroundToDraw)
            # Set originX to be in the middle, displayWidth - FrameWidth = Difference, (Difference / 2)
            coordDifference = (displayInfo.current_w - myGlobals.backgroundToDraw.get_width())
            if coordDifference > 0:
                myGlobals.newX = (coordDifference / 2)
        
        # If width is bigger then height, resize by width
        elif (myGlobals.backgroundToDraw.get_width() > myGlobals.backgroundToDraw.get_height()):
            myGlobals.backgroundToDraw = aspectRatioResizeFixedWidth(myGlobals.backgroundToDraw)
            # Set originY to be in the middle, displayHeight - FrameHeight = Difference, (Difference / 2)
            coordDifference = (displayInfo.current_h - myGlobals.backgroundToDraw.get_height())
            if coordDifference > 0:
               myGlobals.newY = (coordDifference / 2)
        
        
        # Blit onto screen, position is 0, 0, was originally going to be centered, but rule of thirds makes this look better
        # May add slow pan eventually, looks fine as is though
        myGlobals.screenObject.blit(myGlobals.backgroundToDraw, (myGlobals.newX, myGlobals.newY))
        
        # Set myGlobals.slideShowTime inital
        myGlobals.slideShowTimer = time.time()
        
    # If not f then must be a time float, check if 10 seconds have passed
    elif (time.time() - myGlobals.slideShowTimer) > 10:
        # 10 seconds have passed, start fade into another slide
        
        # Make current background previous one (Cannot deepcopy, have to makes bytes)
        bkBytes = pygame.image.tobytes(myGlobals.backgroundToDraw, 'RGBA')
        myGlobals.oldBackground = (pygame.image.frombytes(bkBytes, (myGlobals.backgroundToDraw.get_width(), myGlobals.backgroundToDraw.get_height()), 'RGBA')).convert_alpha()
        
        myGlobals.oldX = 0
        myGlobals.oldY = 0
        
        # Coord calc for old background
        # If height is bigger then width, resize by height
        if (myGlobals.oldBackground.get_height() > myGlobals.oldBackground.get_width()):
            myGlobals.oldBackground = aspectRatioResizeFixedHeight(myGlobals.oldBackground)
            # Set originX to be in the middle, displayWidth - FrameWidth = Difference, (Difference / 2)
            coordDifference = (displayInfo.current_w - myGlobals.oldBackground.get_width())
            if coordDifference > 0:
                myGlobals.oldX = (coordDifference / 2)
        
        # If width is bigger then height, resize by width
        elif (myGlobals.oldBackground.get_width() > myGlobals.oldBackground.get_height()):
            myGlobals.oldBackground = aspectRatioResizeFixedWidth(myGlobals.oldBackground)
            # Set originY to be in the middle, displayHeight - FrameHeight = Difference, (Difference / 2)
            coordDifference = (displayInfo.current_h - myGlobals.oldBackground.get_height())
            if coordDifference > 0:
                myGlobals.oldY = (coordDifference / 2)
        
        # Set myGlobals.fading to true
        myGlobals.fading = True
        
        # Reset timer
        myGlobals.slideShowTimer = time.time()
        
        # Increase myGlobals.slideshowIndexTracker, or rollover
        if myGlobals.shuffleWallpapers == True:
            # Store old index
            oldIndex = myGlobals.slideshowIndexTracker
            # Create list excluding old index
            newIndexList = list(range(0, oldIndex)) + list(range(oldIndex+1, len(myGlobals.slideshowBackgrounds)))
            # Set on random
            myGlobals.slideshowIndexTracker = random.choice(newIndexList)
        else:
            # Increment index
            myGlobals.slideshowIndexTracker += 1
            if myGlobals.slideshowIndexTracker >= len(myGlobals.slideshowBackgrounds):
                myGlobals.slideshowIndexTracker = 0
        
        myGlobals.newX = 0
        myGlobals.newY = 0
        
        # Change background to new one, next in index
        myGlobals.backgroundToDraw = loadImageOntoSurface(myGlobals.slideshowBackgrounds[myGlobals.slideshowIndexTracker], myGlobals.slideshowIndexTracker)
                
        # Coord calc for new background
        # If height is bigger then width, resize by height
        if (myGlobals.backgroundToDraw.get_height() > myGlobals.backgroundToDraw.get_width()):
            myGlobals.backgroundToDraw = aspectRatioResizeFixedHeight(myGlobals.backgroundToDraw)
            # Set originX to be in the middle, displayWidth - FrameWidth = Difference, (Difference / 2)
            coordDifference = (displayInfo.current_w - myGlobals.backgroundToDraw.get_width())
            if coordDifference > 0:
                myGlobals.newX = (coordDifference / 2)
        
        # If width is bigger then height, resize by width
        elif (myGlobals.backgroundToDraw.get_width() > myGlobals.backgroundToDraw.get_height()):
            myGlobals.backgroundToDraw = aspectRatioResizeFixedWidth(myGlobals.backgroundToDraw)
            # Set originY to be in the middle, displayHeight - FrameHeight = Difference, (Difference / 2)
            coordDifference = (displayInfo.current_h - myGlobals.backgroundToDraw.get_height())
            if coordDifference > 0:
               myGlobals.newY = (coordDifference / 2)
                
        # Blit onto screen
        myGlobals.screenObject.blit(myGlobals.oldBackground, (myGlobals.oldX, myGlobals.oldY))

    else:
        # Timer must be below time, keep drawing same frame
        # myGlobals.backgroundToDraw does not change except when over time
        
        if myGlobals.fading == True:
            # Is fading, change alpha and draw old and new backgrounds
            
            # Check if alpha is none, if so set to 255
            if myGlobals.oldBackground.get_alpha() == None:
                myGlobals.oldBackground.set_alpha(255)
        
            # Check if myGlobals.oldBackground is at 0 alpha, if so set myGlobals.fading to false
            if myGlobals.oldBackground.get_alpha() == 0:
                myGlobals.fading = False
            else:
                myGlobals.oldBackground.set_alpha(myGlobals.oldBackground.get_alpha() - myGlobals.slideShowAlphaStepDown)

            # Draw oldBackground above newBackground
            myGlobals.screenObject.blit(myGlobals.backgroundToDraw, (myGlobals.newX, myGlobals.newY))
            myGlobals.screenObject.blit(myGlobals.oldBackground, (myGlobals.oldX, myGlobals.oldY))
        
        else:
            # If not fading then draw background every frame
            myGlobals.screenObject.blit(myGlobals.backgroundToDraw, (myGlobals.newX, myGlobals.newY))