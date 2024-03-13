import pygame
import clientGlobals

def pyGameDrawBackground(screenObject):
    blueBackground = pygame.Surface((screenObject.get_width(), screenObject.get_height()))
    blueBackground.fill((47,55,120))
    screenObject.blit(blueBackground, (0, 0))


# Draws and returns a font surface
def drawFontObject(screenObject, stringToRender, textSize, positionTuple):
    fontObject = pygame.font.Font(None, textSize)
    # Render to surface
    textToDraw = fontObject.render(stringToRender, True, (192, 192, 192))
    # Calc position, TODO
    # Blit to screen
    screenObject.blit(textToDraw, positionTuple)
    return textToDraw


def drawServerList(screenObject, posOffsetSurface):
    # Create rectangle to draw with Bar at bottom
    #TODO
    # Create text and draw it of list
    index = 0
    for server in clientGlobals.foundServers:
        # Generate text
        stringToRender = (server[1] + " [" + server[0] + "] " + "| " + clientGlobals.foundServersStatus[index])
        drawFontObject(screenObject, stringToRender, 24, (0, posOffsetSurface.get_height()))
        
        index += 1
    pass


    #    

    
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
    
    running = True
    
    # Main loop, waiting for logic input
    while clientGlobals.programRunning:
        
        # Draw screen depending on connecting info
        if clientGlobals.screenToDraw == 'scanning':
            # Draw screen
            pyGameDrawBackground(screenObject)

            # Draw static information
            localServText = drawFontObject(screenObject, ("Servers found in local subnet..."), 26, (0, 0))

            # Draw List of Servers
            drawServerList(screenObject, localServText)
        
        
        # Finish Drawing
        pygame.display.flip()
        
    # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                clientGlobals.programRunning = False
          
    # END LOOP