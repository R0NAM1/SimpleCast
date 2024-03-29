import pygame, myGlobals, time
from datetime import datetime

def drawRoundedRectangle(widthHeightTuple, positionTuple):
    # Put coords and size into rectangle
    recPosition = pygame.Rect(positionTuple, widthHeightTuple)
    
    # Create new surface
    rectangleSurface = pygame.Surface((myGlobals.screenObject.get_width(), myGlobals.screenObject.get_height()),  pygame.SRCALPHA)
    
    # Draw rectangle onto surface
    rectangleObject = pygame.draw.rect(rectangleSurface, (42, 42, 42, 150), recPosition, border_radius=25)

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
        
        # Render date 
        dateTextWhite = font.render(dateString, True, (255, 255, 255))
        dateTextWhite.set_alpha(240)
        
        # Render surface
        timeTextWhite = font.render(twelveHourString, True, (255, 255, 255))
        timeTextWhite.set_alpha(240)
        
        # Render connection text top
        connectionTextTopWhite = font.render(connectionStringTop, True, (255, 255, 255))
        connectionTextTopWhite.set_alpha(240)
        
        # Render connection text top
        connectionTextBottomWhite = font.render(connectionStringBottom, True, (255, 255, 255))
        connectionTextBottomWhite.set_alpha(240)
        
        # Render name text
        serverNameTextWhite = font.render(myGlobals.serverName + " [" + myGlobals.thisServersIpAddress + "]" , True, (255, 255, 255))
        serverNameTextWhite.set_alpha(240)
        
        # Calculate positions, top left is 0, 0 as origin
        
        # Top right, date (top right, anchor to right offset by 8, height is 8 down)
        dateTextPositionWhite = ((myGlobals.screenObject.get_width() - dateTextWhite.get_width()) - 8, (8))
        
        # Top right, date (top right, anchor to right offset by 8, height is height of datetime + 8 down)
        timeTextPositionWhite = ((myGlobals.screenObject.get_width() - timeTextWhite.get_width()) - 8, dateTextWhite.get_height() + 8)
        
        # DRAW Time date box
        # position is top right offset by dateTextPosition width with 10 offset, height is date + time strings offset 20
        posTuple = (((myGlobals.screenObject.get_width() - dateTextWhite.get_width()) - 20), 
                    (0 - (dateTextWhite.get_height() + timeTextWhite.get_height())) + 20)

        drawRoundedRectangle((((dateTextWhite.get_width()) * 2 ), ((dateTextWhite.get_height() + timeTextWhite.get_height()) * 2)), posTuple)
        
        
        
        # Bottom left, for name
        serverNamePositionWhite = ((0 + 5), ((myGlobals.screenObject.get_height() - serverNameTextWhite.get_height()) - (3 + 5)))
        
        # Position for connection text top
        connectionTextPositionWhiteTop = ((0 + 5), ((myGlobals.screenObject.get_height() - serverNameTextWhite.get_height() - (connectionTextTopWhite.get_height() + connectionTextBottomWhite.get_height())) - (3 + 10)))
             
        # Position for connection text top
        connectionTextPositionWhiteBottom = ((0 + 5), ((myGlobals.screenObject.get_height() - serverNameTextWhite.get_height() - (connectionTextTopWhite.get_height())) - (3 + 10)))
        
        widthToUse = 0
        
        # Calc widest surface
        if (serverNameTextWhite.get_width() > connectionTextBottomWhite.get_width()):
            # Server name is bigger, use
            widthToUse = serverNameTextWhite.get_width()
        else:
            # connectionTextBottomWhite is bigger
            widthToUse = connectionTextBottomWhite.get_width()

        combinedHeight = connectionTextBottomWhite.get_height() + connectionTextTopWhite.get_height() + serverNameTextWhite.get_height()
        
        # Connection info box
        posTuple = ((0 - widthToUse) + 20, (myGlobals.screenObject.get_height() - (combinedHeight)) - 25)
        
        drawRoundedRectangle(((widthToUse * 2), (combinedHeight * 2)), posTuple)
        
        
        # Blit both it to screen
        # Draw date text with outline, 1st top right
        myGlobals.screenObject.blit(dateTextWhite, dateTextPositionWhite)
        # Draw time text with outline, 2nd top right
        myGlobals.screenObject.blit(timeTextWhite, timeTextPositionWhite)
        # Draw server name with outline, bottom left
        myGlobals.screenObject.blit(serverNameTextWhite, serverNamePositionWhite)
        # Draw connection text, bottom left
        myGlobals.screenObject.blit(connectionTextTopWhite, connectionTextPositionWhiteTop)
        # Draw connectionBottom text, bottom left
        myGlobals.screenObject.blit(connectionTextBottomWhite, connectionTextPositionWhiteBottom)
        
# Draw pauseSurface, half opacity black surface, then time and date
def drawPausedScreen(displayInfo):
    
    # blit surface at top left
    myGlobals.screenObject.blit(myGlobals.pauseSurface, (0, 0))
    
    # Draw half opacity screen
    blackCurtain = pygame.Surface((displayInfo.current_w, displayInfo.current_h))
    blackCurtain.fill((0, 0, 0))
    blackCurtain.set_alpha(200)
    
    # Draw time and date
    currentTime = datetime.now()
    # Convert to 12 hour format
    dateString = currentTime.strftime("%A, %B %d, %Y")
    twelveHourString = currentTime.strftime("%I:%M:%S %p")
    
    # Create font objects
    dateStringFont = pygame.font.Font(None, 30)
    twelveHourStringFont = pygame.font.Font(None, 60)
    
    # Render to surfaces
    dateStringSurface = dateStringFont.render(dateString, True, (255, 255, 255))
    twelveHourStringSurface = twelveHourStringFont.render(twelveHourString, True, (255, 255, 255))
    
    # Calculate positions
    
    dateStringPositon = ((displayInfo.current_w / 2) - (dateStringSurface.get_width() / 2), (displayInfo.current_h / 2) - 20)
    twelveHourStringPositon = ((displayInfo.current_w / 2) - (twelveHourStringSurface.get_width() / 2), (displayInfo.current_h / 2) + 20)
    
    # Draw surfaces
    myGlobals.screenObject.blit(blackCurtain, (0, 0))
    myGlobals.screenObject.blit(dateStringSurface, dateStringPositon)
    myGlobals.screenObject.blit(twelveHourStringSurface, twelveHourStringPositon)

        
# Draw current connecting client and PIN if found, 
def drawConnectingInformation():    
    # New font object
    font = pygame.font.Font(None, 25)
    timerFont = pygame.font.Font(None, 40)
    fontPin = pygame.font.Font(None, 210)
    
    connectingString = (myGlobals.clientHostname + " is attemping to connect...")
    calculateConnectionDiff = (time.time() - myGlobals.connectionTimer)
    # myGlobals.connectionTimer
    
    # Connection timer logic
    # We find the difference between connectionTimer and current time, if above 20 then close connection
    # To calculate countdown, take countdown time (20) and take away diff time and draw int

    myGlobals.nearestConnectionInt = int(20 - calculateConnectionDiff)
    timerToDraw = str(myGlobals.nearestConnectionInt)

    
    boxHeight = 300
    boxWidth = 700
    
    center = myGlobals.screenObject.get_rect().center
    boxX = center[0] - (boxWidth // 2)
    boxY = center[1] - (boxHeight // 2)
    
    drawRoundedRectangle((boxWidth, boxHeight), (boxX, boxY))
    
    # Start drawing text
    connectionText = font.render(connectingString, True, (255, 255, 255))
    
    # Draw connectionTime
    timerToDrawText = timerFont.render(timerToDraw, True, (255, 255, 255))
    
    # Blit
    myGlobals.screenObject.blit(connectionText, (boxX + 10, boxY + 5))
    
    # Blit timer
    myGlobals.screenObject.blit(timerToDrawText, ((boxX + boxWidth) - (timerToDrawText.get_width() + 10), boxY + 5))

    pinString = 'READY'
    
    if myGlobals.generatedPin != 'False':
        # If a pin was not generated, show READY string
        pinString = str(myGlobals.generatedPin)
        
    # Draw text
    pinText = fontPin.render(pinString, True, (255, 255, 255, 220))
    # Blit
    myGlobals.screenObject.blit(pinText, ((boxX + (boxWidth // 2) - (pinText.get_width() // 2)), (boxY + (boxHeight // 2) - (pinText.get_height() // 2))))
  