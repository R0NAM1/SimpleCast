<img src="logo-pallete.png" alt="SimpleCast Logo, a smiling face using the WiFi symbol as a wink" width="200"/> <br />

SimpleCast is an AioRTC based software that takes your current screen and audio buffer and sends them over the network via the WebRTC standard to 'cast' to another display. Completely complient with WebRTC and HTTP standards, so implementing a custom client is easy.

For use anywhere that wireless casting akin to a ChromeCast is wanted, but with more management and the ability to do pin authentication.
Not a replacement for an HDMI cable if one can be ran. Depending on hardware ran on it might be able to display 4K, it cannot STREAM 4k,
has a hard time with 1080p, defaults to 720p for balance between framerate and resolution. 

Try different display resolutions between 720p, 1080p and 4K and see how smooth the slideshow transition is, usually a good gauge.

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
- Individual application window capture if I can find a cross platform library for it
- Broadcast traffic for passive discovery and mDNS for active discovery


## SimpleCast Config Keys & Possible Values
| Config Key | Meaning | Value Type | Value Example |
| ---------- | ------- | ---------- | ------------- |
| `serverName` | The name that the server displays and broadcasts | String | "Conference Room 1" |
| `usePINAuthentication` | Force PIN authentication or allow anybody to connect at anytime from anywhere | Boolean | true or false |
| `allowAudioRedirection` | Allow clients to cast audio to the server | Boolean | true or false |
| `allowedPskList` | List of client PSK's that have authority over the server, usually assigned Teachers or equivilent | String array | ["psk1", "psk2"] |
| `slideshowPictures` | List of pictures in backgrounds folder to display, can also be a URL with http locator (Eventually) | String array | ["0.jpg", "1.jpg"] |
| `serverIP` | The IP Address of the primary interface the server uses, forces you to make it static or static lease | String | "10.42.255.249" |
| `shuffleSlideshow` | Either show background slides in sequencial order, or randomly shuffle | Boolean | true or false |
| `connectionScreenScale` | The size of information drawn on the 'open' screen | Float | "low: 0.5", "meduim: 1" or "high: 1.5" or anything else |
| `countDownTime` | How long to wait until a connecting client becomes invalid | Integer | 20 |
| `slideshowAlphaStepdown` | Amount to step down fading slideshow transitions | Integer | 1 - 255, Do 255 for no fading |
| `doBroadcastDiscovery` | Enable or disable subnet broadcast traffic to advertise server | Boolean | true or false |


## TODO
- ✓ Tell client server timeout
- ✓ Make github page for quick downloads (r0nam1.github.io/simplecast, put into link shortener)
    https://bit.ly/simplecast-client -> https://r0nam1.github.io/SimpleCast/
- ✓ TransItion all 'globals' to myGlobals
- ~✓ Add sigint handling (Work's better, issues with AioHTTP and AioRTC, but on 'open' it works)
- ✓ Allow PSK to kick connection
- ✓ Allow PSK to disable/enable casting
- ✓ Fix image resizing on server
- ✓ Do info drawing scaling
- Allow option to make connecting text 'bit.ly link', 'to connect', or just 'info'.

- Website grabbing for slideshow, add thread to do screenshots every 30 seconds
- Allow option to flip info and text on screen every slideshow loop (Amount of I) for burn in protection
- Test all edgecases
- Add debug for server, will show all relevent debug data, time to draw frame, receiver frame, resolution other
- Logging to file in home directory or local directory: Format ## Month/Day/Year 13:00 (Severity) Action
- Add option to replace slideshow with video file, like a cozy fireplace or livestream (Rosa the Sea Otter?) 
- Implement mDNS discovery for browser client
- Finish Browser Extension Clients, glow up and CSS overhaul
  