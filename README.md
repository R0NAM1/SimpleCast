SimpleCast is a Python based transmission and receiver software that will probably support Google Cast, Airplay and Miracast, but does display mirroring and audio redirection over http (most likely).
It usese its own UI to show the found recievers on the same subnet using broadcast traffic, then when you try to connect it grabs the server settings and checks if a PIN is required, if so the reciever will display it.
If not then it says who is about to connect with the hostname, and the client will have the option to redirect audio.
Each client has a Pre-Shared Key that can be used to bypass PIN authentication. While mirroring you can blank your display and mute your audio. Other clients cannot boot you off, you stay connected until you disconnect.
If need be, the keypress 'q' on the receiver can stop a client connection.
