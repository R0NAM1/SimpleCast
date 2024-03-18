import pygame
import clientGlobals

global scrollOffsetYScan, scrollOffsetYFav, listSurfacesDrawn
scrollOffsetYScan = 40
scrollOffsetYFav = 40
listSurfacesDrawn = []


def pyGameDrawBackground(screenObject):
    blueBackground = pygame.Surface((screenObject.get_width(), screenObject.get_height()))
    blueBackground.fill((47,55,120))
    screenObject.blit(blueBackground, (0, 0))


# Draws and returns a font surface
def createFontSurface(screenObject, stringToRender, textSize):
    fontObject = pygame.font.Font(None, textSize)
    # Render to surface
    textToDraw = fontObject.render(stringToRender, True, (192, 192, 192))
    return textToDraw


def drawBackgroundBoxForSurface(screenObject, surface, offsetWidth, offsetHeight):
    recPosition = pygame.Rect((0, 0), (screenObject.get_width(), surface.get_height() * 2))
    # Assumes width is window width
    # Create new surface
    rectangleSurface = pygame.Surface((screenObject.get_width(), surface.get_height() * 2))
    
    # Draw rectangle onto surface
    rectangleObject = pygame.draw.rect(rectangleSurface, (39,47,69), recPosition)

    # Blit onto screen
    screenObject.blit(rectangleSurface, (0, offsetHeight))


def drawStaticElements(screenObject):
    # Servers found text
    localServText = createFontSurface(screenObject, ("Servers found in local subnet..."), 30)
    
    # Draw box for it
    drawBackgroundBoxForSurface(screenObject, localServText, 0, 0)
    
    # Blit to Screen
    localServTextWidthPos = (screenObject.get_width() / 2) - (localServText.get_width() / 2)
    screenObject.blit(localServText, (localServTextWidthPos, 10))
    
    # Draw favroite servers text, draw at 400
    favServText = createFontSurface(screenObject, ("Favorited Servers..."), 30)
    
    # Draw box for it
    drawBackgroundBoxForSurface(screenObject, favServText, 0, 390)
    
    # Blit to Screen
    favServTextWidthPos = (screenObject.get_width() / 2) - (favServText.get_width() / 2)
    screenObject.blit(favServText, (favServTextWidthPos, 400))


def handleMouseScrollBasedOnCoords(event):
    global scrollOffsetYScan, scrollOffsetYFav
    # -1 is scroll down, 1 is scroll up
    # Check if hovering over correct area
    # Check if at 40
    if scrollOffsetYScan > 40 or event.y == -1:
        scrollOffsetYScan += (event.y * -10)
        print("scrollOffsetYScan: " + str(scrollOffsetYScan))

def handleMouseOverSurface(screenObject):
    global listSurfacesDrawn
    # Get current mouse coords
    mouse_x, mouse_y = pygame.mouse.get_pos()
    pass

def drawFoundServerList(screenObject):
    global scrollOffsetYScan, scrollOffsetYFav, listSurfacesDrawn
    # Each list item will be 20 pixels tall
    # Create rectangle to draw with Bar at bottom
    
    listSurfacesDrawn = []
    
     # Create text and draw it of list
    index = 0
    for server in clientGlobals.foundServers:
        # Generate text
        stringToRender = (server[1] + " [" + server[0] + "] " + "| " + clientGlobals.foundServersStatus[index])

        fontSurface = createFontSurface(screenObject, stringToRender, 24)
        
        offsetY = 0
        
        listSurfacesDrawn.append(fontSurface)
        
        # Go throuhg listSurfacesDrawn to generate offset
        for surface in listSurfacesDrawn:
            offsetY += surface.get_height()
                
        
        index += 1
    
    # Draw containing surface, which all elements will treat as origin and follow
    containingRectangle = pygame.Rect((0, 0), (screenObject.get_width(), offsetY))
    # Create new surface
    rectangleSurface = pygame.Surface((screenObject.get_width(), offsetY))
    
    # Draw rectangle onto surface
    rectangleObject = pygame.draw.rect(rectangleSurface, (39,52,74), containingRectangle)
    # rectangleObject = pygame.draw.rect(rectangleSurface, (0,255,0), containingRectangle)

    finalContainerPositionOriginY = (0 + scrollOffsetYScan)

    # Blit onto screen
    screenObject.blit(rectangleSurface, (0, finalContainerPositionOriginY))
    
    heightOffset = 0
    # Now draw each text surface
    for surface in listSurfacesDrawn:
        screenObject.blit(surface, (0, finalContainerPositionOriginY + heightOffset))
        heightOffset += surface.get_height()


    
def pyGameDrawingThread():
    global screenToDraw
    # Initialize pygame
    pygame.init()
    
    # Change Window name and Icon
    programIcon = pygame.image.load('../logo-pallete.png')
    pygame.display.set_icon(programIcon)
    
    # Set name
    pygame.display.set_caption("SimpleCast Client")
    
    # Set display mode, will initially be scanning so 480x640
    screenObject = pygame.display.set_mode((480, 640))
    
    # Get display info
    displayInfo = pygame.display.Info() 
    
    clientGlobals.programRunning = True
    
    
    # Main loop,
    # Every tick draw frame
    # Wait for user input
    while clientGlobals.programRunning:
        
        # Draw screen depending on connecting info
        if clientGlobals.screenToDraw == 'scanning':
            # Draw colored background
            pyGameDrawBackground(screenObject)

            # Draw List of Servers
            drawFoundServerList(screenObject)
            
            # Draw static information
            drawStaticElements(screenObject)

        
        
        # Finish Drawing
        pygame.display.flip()
        
    # Handle events, like client clicks
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                clientGlobals.programRunning = False
            # Implement scrolling later, I doubt anybody will have 30+ devices immediently
            # elif event.type == pygame.MOUSEWHEEL:
            #     handleMouseScrollBasedOnCoords(event)

          
    # END LOOP