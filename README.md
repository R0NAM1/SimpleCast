<img src="logo-pallete.png" alt="SimpleCast Logo, a smiling face using the WiFi symbol as a wink" width="200"/> <br />

This is a simple AioRTC based software that takes your current screen and audio buffer and sends them over the network via the WebRTC standard to 'cast' to another display. 

Features (will) include:
- Show a slideshow by default, will be customizable to either show a static image or a screenshot of a webpage, like AP NEWS headlines
- Pin Authentication, with a PSK bypass for certain clients
( For instance, Students have to type in a PIN, while Teachers can auto connect)
- Optional Audio Redirection
- Ability to pause casting
- Windows, Mac and Linux clients (Python Script Bundled into Native Execution Format)
- Chrome Extension (Eventually, so it can be used on ChromeOs devices)

## TODO
- Show IP
- Connecting timeout, 20 seconds, allow cancel
- Allow Pausing
- Allow PSK to kick connection, disable/enable casting
- Make github page for quick downloads (r0nam1.github.io/simplecast)
- Finished client
- Website grabbing for slideshow, every slideshow loop flip info to act as screensaver
- Test edgecases