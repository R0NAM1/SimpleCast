<img src="logo-pallete.png" alt="SimpleCast Logo, a smiling face using the WiFi symbol as a wink" width="200"/> <br />

Client Downloads:
https://r0nam1.github.io/SimpleCast/

SimpleCast is an AioRTC based software that takes your current screen and audio buffer and sends them over the network via the WebRTC standard to 'cast' to another display. Completely complient with WebRTC and HTTP standards, so implementing a custom client is easy.

For use anywhere that wireless casting akin to a ChromeCast is wanted, but with more management and the ability to do pin authentication.
Not a replacement for an HDMI cable if one can be ran. Depending on hardware ran on it might be able to display 4K, it cannot STREAM 4k,
has a hard time with 1080p, defaults to 720p for balance between framerate and resolution. 

Try different display resolutions between 720p, 1080p and 4K and see what the debug FPS is to see what your hardware can handle.

Features include:
- Showing a slideshow by default, with the option of a screenshot of a webpage
- Pin Authentication, with a PSK bypass for certain clients
    ( For instance, Students have to type in a PIN, while Teachers can auto connect)
- PSK clients can kick other clients and toggle castability to the server
- Optional Audio Redirection
- Ability to pause casting
- Browser based clients (Maybe OS based in the future)
- Broadcast traffic for passive discovery and mDNS for active discovery (May make broadcast obselete)


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
| `infoScreenConnectionText` | What connect text should the 'open' screen show | String | "link" to show bit.ly link, "name" for just the server name, "default" for default text |
| `infoTextAlignment` | Should the info text on open flip every 120 seconds, or be statically left or right | String | "flip", "left", "right" |
| `displayDebugStats` | Display debug stats on screen | Boolean | true or false |


## TODO
- Implement mDNS discovery for browser client
- Finish Browser Extension Clients, glow up and CSS overhaul
- README overhaul
  