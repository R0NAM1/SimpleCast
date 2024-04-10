A file that highly details the exact process of reaching out to a server and establishing a WebRTC connection with HTTP text commands.

## MAIN FLOW

Client -> server:4825/command | "attemptConnection|hostname|PSK"
server -> Client      | "response|False|audioAllowed|timeoutInteger"

Client -> server:4825/command | "command:connect|000000" or "command:connect|inputtedPinInteger"
server -> Client      | "response:accepted" or "response:rejected"

Client -> server:4825/sdpOffer | "sdpOfferText"
server -> Client      | "sdpAnswerText"

WebRTC and casting is now active

## COMMANDS

# Get status
Client -> server:4825/command | "command:statusProbe"
server -> Client      | "serverName|status"

# Pause
Client -> server:4825/command | "command:pause"
server -> Client      | "response:paused" or "response:unpaused"

# Kick
Client -> server:4825/kick | "command:kick|generatedPSK"
server -> Client      | "response:clientKicked"

# Toggle Casting
Client -> server:4825/toggle | "command:toggleCast|generatedPSK"
server -> Client      | "response:enabledCasting" or "response:disabledCasting"

# Get discovered servers
Client -> server:4825/discover | "GET"
server -> Client      | Array Of IP Addresses