import pygame, myGlobals
from datetime import datetime

def drawRoundedRectangle(widthHeightTuple, positionTuple):
    # Put coords and size into rectangle
    recPosition = pygame.Rect(positionTuple, widthHeightTuple)
    
    # Create new surface
    rectangleSurface = pygame.Surface((myGlobals.screenObject.get_width(), myGlobals.screenObject.get_height()),  pygame.SRCALPHA)
    
    # Draw rectangle onto surface
    rectangleObject = pygame.draw.rect(rectangleSurface, (42, 42, 42, 200), recPosition, border_radius=25)

    # Blit onto screen
    myGlobals.screenObject.blit(rectangleSurface, (0, 0))

# Draw information to display at all times while not connecting
# Name, Time, IP Address
def pyGameDrawInformation(font):
    
        connectionStringTop = 'To cast, download the'
        connectionStringBottom = 'SimpleCast app and select'
    
        # Show current time
        # Get time
        currentTime = datetime.now()
        # Convert to 12 hour format
        dateString = currentTime.strftime("%A, %B %d, %Y")
        twelveHourString = currentTime.strftime("%I:%M:%S %p")
        # Render text
        timeTextWhite = font.render(twelveHourString, True, (255, 255, 255))
        # Render bold background
        font.set_bold(True)
        timeTextBlack = font.render(twelveHourString, True, (0, 0, 0))
        font.set_bold(False)

        # Render connection text top
        connectionTextTopWhite = font.render(connectionStringTop, True, (255, 255, 255))
        font.set_bold(True)
        connectionTextTopBlack = font.render(connectionStringTop, True, (0, 0, 0))
        font.set_bold(False)

        # Render connection text top
        connectionTextBottomWhite = font.render(connectionStringBottom, True, (255, 255, 255))
        font.set_bold(True)
        connectionTextBottomBlack = font.render(connectionStringBottom, True, (0, 0, 0))
        font.set_bold(False)

        # Render name text
        serverNameTextWhite = font.render(myGlobals.serverName, True, (255, 255, 255))
        # Render bold background
        font.set_bold(True)
        serverNameTextBlack = font.render(myGlobals.serverName, True, (0, 0, 0))
        font.set_bold(False)
        
        # Render date 
        dateTextWhite = font.render(dateString, True, (255, 255, 255))
        # Render bold background
        font.set_bold(True)
        dateTextBlack = font.render(dateString, True, (0, 0, 0))
        font.set_bold(False)

        # Eventually make into a function (writeBoldText?) 

        # Calculate positions, top left is 0, 0 as origin. Use inset of 5 pixels so that way it's not on the edge
        # Top right, for time
        # Offset by dateTextWhite.get_height + 5
        timeTextPositionBlack = ((myGlobals.screenObject.get_width() - timeTextWhite.get_width()) - 5, (0 + 10) + dateTextWhite.get_height())
        timeTextPositionWhite = ((myGlobals.screenObject.get_width() - timeTextWhite.get_width()) - 5, (3 + 10) + dateTextWhite.get_height())
        
        # Top right, date
        dateTextPositionBlack = ((myGlobals.screenObject.get_width() - dateTextWhite.get_width()) - 5, (0 + 5))
        dateTextPositionWhite = ((myGlobals.screenObject.get_width() - dateTextWhite.get_width()) - 5, (3 + 5))
        
        # Bottom left, for name
        serverNamePositionBlack = ((0 + 5), ((myGlobals.screenObject.get_height() - serverNameTextWhite.get_height()) - (0 + 5)))
        serverNamePositionWhite = ((0 + 5), ((myGlobals.screenObject.get_height() - serverNameTextWhite.get_height()) - (3 + 5)))
        
        # Position for connection text top
        connectionTextPositionBlackTop = ((0 + 5), ((myGlobals.screenObject.get_height() - serverNameTextWhite.get_height() - (connectionTextTopWhite.get_height() + connectionTextBottomWhite.get_height())) - (0 + 10)))
        connectionTextPositionWhiteTop = ((0 + 5), ((myGlobals.screenObject.get_height() - serverNameTextWhite.get_height() - (connectionTextTopWhite.get_height() + connectionTextBottomWhite.get_height())) - (3 + 10)))
             
        # Position for connection text top
        connectionTextPositionBlackBottom = ((0 + 5), ((myGlobals.screenObject.get_height() - serverNameTextWhite.get_height() - (connectionTextTopWhite.get_height())) - (0 + 10)))
        connectionTextPositionWhiteBottom = ((0 + 5), ((myGlobals.screenObject.get_height() - serverNameTextWhite.get_height() - (connectionTextTopWhite.get_height())) - (3 + 10)))
        
        # Draw background rectangles
        # Time date box
        posTuple = ((myGlobals.screenObject.get_width() - dateTextWhite.get_width() - 20), (0 - dateTextWhite.get_height()) - 40)
        drawRoundedRectangle(((dateTextWhite.get_width() *2 ), (dateTextWhite.get_height() * 4)), posTuple)
        
        
        # Connection info box
        posTuple = ((0 - connectionTextBottomWhite.get_width()) + 20, (myGlobals.screenObject.get_height() - (connectionTextBottomWhite.get_height() * 3)) - 20)
        drawRoundedRectangle(((connectionTextBottomWhite.get_width() *2 ), (connectionTextBottomWhite.get_height() * 4)), posTuple)
        
        
        # Blit both it to screen
        # Draw date text with outline, 1st top right
        # myGlobals.screenObject.blit(dateTextBlack, dateTextPositionBlack)
        myGlobals.screenObject.blit(dateTextWhite, dateTextPositionWhite)
        
        # Draw time text with outline, 2nd top right
        # myGlobals.screenObject.blit(timeTextBlack, timeTextPositionBlack)
        myGlobals.screenObject.blit(timeTextWhite, timeTextPositionWhite)
        # Draw server name with outline, bottom left
        # myGlobals.screenObject.blit(serverNameTextBlack, serverNamePositionBlack)
        myGlobals.screenObject.blit(serverNameTextWhite, serverNamePositionWhite)
        # Draw connection text, bottom left
        # myGlobals.screenObject.blit(connectionTextTopBlack, connectionTextPositionBlackTop)
        myGlobals.screenObject.blit(connectionTextTopWhite, connectionTextPositionWhiteTop)
        # Draw connectionBottom text, bottom left
        # myGlobals.screenObject.blit(connectionTextBottomBlack, connectionTextPositionBlackBottom)
        myGlobals.screenObject.blit(connectionTextBottomWhite, connectionTextPositionWhiteBottom)
        
# Draw current connecting client and PIN if found, 
def drawConnectingInformation():    
    # New font object
    font = pygame.font.Font(None, 40)
    fontPin = pygame.font.Font(None, 210)
    
    connectingString = (myGlobals.clientHostname + " is attemping to connect...")
    
    boxHeight = 300
    boxWidth = 700
    
    center = myGlobals.screenObject.get_rect().center
    boxX = center[0] - (boxWidth // 2)
    boxY = center[1] - (boxHeight // 2)
    
    drawRoundedRectangle((boxWidth, boxHeight), (boxX, boxY))
    
    # Start drawing text
    connectionText = font.render(connectingString, True, (255, 255, 255))
    # Blit
    myGlobals.screenObject.blit(connectionText, (boxX + 10, boxY + 5))
    
    pinString = 'READY'
    
    if myGlobals.generatedPin != 'False':
        # If a pin was not generated, show READY string
        pinString = str(myGlobals.generatedPin)
        
    # Draw text
    pinText = fontPin.render(pinString, True, (255, 255, 255))
    # Blit
    myGlobals.screenObject.blit(pinText, ((boxX + (boxWidth // 2) - (pinText.get_width() // 2)), (boxY + (boxHeight // 2) - (pinText.get_height() // 2))))
  