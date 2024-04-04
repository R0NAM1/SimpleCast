<img src="logo-pallete.png" alt="SimpleCast Logo, a smiling face using the WiFi symbol as a wink" width="200"/> <br />

This is a simple AioRTC based software that takes your current screen and audio buffer and sends them over the network via the WebRTC standard to 'cast' to another display. Completely complient with WebRTC and HTTP standards, so implementing a custom client is easy.

Client Downloads:
https://r0nam1.github.io/SimpleCast/

Features (will) include:
- Show a slideshow by default, will be customizable to either show a static image or a screenshot of a webpage, like AP NEWS headlines
- Pin Authentication, with a PSK bypass for certain clients
( For instance, Students have to type in a PIN, while Teachers can auto connect)
- Optional Audio Redirection
- Ability to pause casting
- PSK clients can kick other clients and toggle castability to the server
- Windows, Mac and Linux clients (Python Script Bundled into Native Execution Format)
- Chrome Extension (Eventually, so it can be used on ChromeOs devices)
- Individual application window capture if I can find a cross platform library for it
- Broadcast traffic for passive discovery and mDNS for active discovery

## TODO
- ✓ Tell client server timeout
- ✓ Make github page for quick downloads (r0nam1.github.io/simplecast, put into link shortener)
    https://bit.ly/simplecast-client -> https://r0nam1.github.io/SimpleCast/
- ✓ TransItion all 'globals' to myGlobals
- Add sigint handling
- Allow PSK to kick connection, disable/enable casting
- Finish Browser Extension Clients, maybe finish native OS client in the future?
- Website grabbing for slideshow, every slideshow loop flip info to act as screensaver
- Test edgecases
- Add debug for server, will show all relevent debug data, time to draw frame, receiver frame, resolution other
- Logging to file in home directory or local directory: Format ## Month/Day/Year 13:00 (Severity) Action
- Add option to replace slideshow with video file, like a cozy fireplace or livestream (Rosa the Sea Otter?) 
- Implement mDNS discovery for browser client

## SimpleCast Config Keys & Possible Values
| Config Key | Meaning | Possible Values |
| ---------- | ------- | --------------- |
| `serverName` | The name that the server displays and broadcasts | String, "Conference Room 1" |
| `usePINAuthentication` | Force PIN authentication or allow anybody to connect at anytime from anywhere | Boolean, true or false |
| `allowAudioRedirection` | Allow clients to cast audio to the server | Boolean, true or false |
| `allowedPskList` | List of client PSK's that have authority over the server, usually assigned Teachers or equivilent | String array, ["psk1", "psk2"] |
| `slideshowPictures` | List of pictures in backgrounds folder to display, can also be a URL with http locator (Eventually) | String array, ["0.jpg", "1.jpg"] |
| `serverIP` | The IP Address of the primary interface the server uses, forces you to make it static or static lease | String, "10.42.255.249" |
| `shuffleSlideshow` | Either show background slides in sequencial order, or randomly shuffle | Boolena, true or false |
| `connectionScreenScale` | The size of information drawn on the 'open' screen | String, "low", "meduim" or "high" |
| `countDownTime` | How long to wait until a connecting client becomes invalid | Integer, 20 |
| `slideshowAlphaStepdown` | Amount to step down fading slideshow transitions | Integer, 1 - 255, Do 255 for no fading |
| `doBroadcastDiscovery` | Enable or disable subnet broadcast traffic to advertise server | Boolean, true or false |

  