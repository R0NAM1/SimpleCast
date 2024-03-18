<img src="logo-pallete.png" alt="SimpleCast Logo, a smiling face using the WiFi symbol as a wink" width="200"/> <br />

This is a simple AioRTC based software that takes your current screen and audio buffer and sends them over the network via the WebRTC standard to 'cast' to another display. Completely complient with WebRTC and HTTP standards, so implementing a custom client is easy.

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
- Tell client server timeout
- Allow PSK to kick connection, disable/enable casting
- Make github page for quick downloads (r0nam1.github.io/simplecast, put into link shortener)
- Finish Browser Extension Clients, maybe finish native OS client in the future?
- Website grabbing for slideshow, every slideshow loop flip info to act as screensaver
- Test edgecases
- Add sigint handling
- Add debug for server, will show all relevent debug data, time to draw frame, receiver frame, resolution other
- Logging to file in home directory or local directory: Format ## Month/Day/Year 13:00 (Severity) Action
- Add option to replace slideshow with video file, like a cozy fireplace or livestream (Rosa the Sea Otter?) 
- Implement mDNS discovery for browser client