// import * as browser from './node_modules/webextension-polyfill/dist/browser-polyfill.js';
// var browser = require("./node_modules/webextension-polyfill/dist/browser-polyfill.js")

var serverAudioAllowed = false;
var sendClientAudio = true;
var pinAuthRequired = false;
var requestedWidth = 1280;
var requestedHeight = 720;
var pc = null;
var mediaStream;
var generatedPSK = 'none';
var uniqueHostname = 'none';

// PSK string generator
function generatePSKRandomString(length = 8) {
    return Math.random().toString(16).substr(2, length);
}

async function startWebRTCMirroring(serverIP) {

    console.log("Starting WebRTC")

    var config = {
        sdpSemantics: 'unified-plan', // Modern SDP format.
        iceServers: [{"urls": "stun:" + serverIP}] //This will be dynamic based on server config later
    };

    pc = new RTCPeerConnection(config); // Set server to config
    console.log("Generating getDisplayMedia")
    // Grab MediaStream
    mediaStream = await navigator.mediaDevices.getDisplayMedia({
        video: {
            cursor: "always",
            width: { ideal: requestedWidth, max: requestedWidth },
            height: { ideal: requestedHeight, max: requestedHeight }
        },
        audio: true, // Set to true if you want to capture audio as well
        surfaceSwitching: "include", // Allow user to switch displayMedia source
        systemAudio: "include" // Capture system audio, not individual tab audio
    });


    // Attempt to set Codec to use, valid options are VP8, RTX (ReTransmittion) H264 "profile-level-id=42e00d;level-asymmetry-allowed=1;packetization-mode=1" }

    var availableRTCCodecs = RTCRtpSender.getCapabilities('video').codecs

    var codecsToUse = [];

    // Go through available codecs
    for (var codec of availableRTCCodecs) {
        if (codec.mimeType.includes('H264')) {
            console.log("Using Codec: ")
            console.log(codec)
            codecsToUse.push(codec);
        }
        else if (codec.mimeType.includes('rtx')) {
            console.log("Using Codec: ")
            console.log(codec)
            codecsToUse.push(codec);
        }
    }    

    console.log("Adding MediaStream tracks")

    for (var msTrack of mediaStream.getTracks()) {
        if (msTrack.kind == 'video') {
            console.log("Adding video track:")
            console.log(msTrack)
            var thisTransceiver = pc.addTransceiver(msTrack, {direction: 'sendonly'});
            // IF we can change codecs we will
            // if (thisTransceiver.setCodecPreferences) {
            // thisTransceiver.setCodecPreferences(codecsToUse);
            // }
        }
        else if (msTrack.kind == 'audio') {
            console.log("Adding audio track:")
            console.log(msTrack)
            pc.addTransceiver(msTrack, {direction: 'sendonly'});
        }
    }

    var serverIdTextURL = 'http://' + serverIP + ':4825/sdpOffer'

    // Time to negotiate with server
    return pc.createOffer({iceRestart:true}).then(function(offer) {
        console.log("Generated Offer")
        // Attempt to set codec with SDP manipulation if setCodecPreferences is not supported
        
        // if (thisTransceiver.setCodecPreferences) {
        //     console.log(offer)
        // }
        // else {
        //     offer.sdp = offer.sdp.replace('VP8', 'H264')
        //     offer.sdp = offer.sdp.replace('VP9', 'H264')
        //     console.log(offer)
        // }

        return pc.setLocalDescription(offer); // I am the offer.
    }).then(function() {
        // wait for ICE gathering to complete
        return new Promise(function(resolve) {
            if (pc.iceGatheringState === "complete") {
                resolve();
            } else {
                function checkState() {
                    if (pc.iceGatheringState === "complete") {
                        pc.removeEventListener(
                            "icegatheringstatechange",
                            checkState
                        );
                        resolve();
                    }
                }
                pc.addEventListener("icegatheringstatechange", checkState);
            }
        });
    }).then(function() {
        var offer = pc.localDescription; // Send our offer to the server in a JSON format, we expect a raw ANSWER, not encapsulated,
        console.log("Sending Offer")
        return fetch(serverIdTextURL, {
            body: 
                offer.sdp,
            headers: {
                'Content-Type': 'text/plain'
            },
            method: 'POST'
        });
    }).then(function(response) {
        console.log("Received Answer")
        return response.text();
    }).then(function(answer) {
        console.log("Setting Answer From Server")
        console.log(answer)
        var sess = new RTCSessionDescription({sdp: answer, type: 'answer'}) // Set the response to our answer.
        pc.setRemoteDescription(sess);   //Finally, set the remote peers description.
    })
}




function attemptConnectionWithPIN() {
    // Send HTTP request to server and wait for response,
    // Get serverIdText
    var serverIdText = document.getElementById('serverIdText').value;
    var serverIdTextURL = 'http://' + serverIdText + ':4825/command'

    var PINValue = document.getElementById('pinText').value;

    // Define connection data
    if (PINValue == '') {
        var postString = ("command:connect|" + "000000")
    }
    else {
        var postString = ("command:connect|" + PINValue)
    }

    console.log("Sending: " + postString)

    fetch(serverIdTextURL, {
        method: 'POST',
        mode: 'cors',
        headers: {
           'Content-Type': 'text/plain'
        },
        body: postString
       }).then(function(response) {
        return response.text();
    }).then(function(responseData) {

        console.log("Got response: " + responseData)
        
        // Check if accepted or rejected
        if (responseData.includes('response:accepted')) {
            console.log("Connection Accepted! Starting WebRTC")
            startWebRTCMirroring(serverIdText)
        }
        else {
            console.log("REJECTED")
            stopCasting()
        }

    })
}

function showConnectionPanel() {

    var pinConnectingGhostElement = document.getElementById('pinConnectingGhost');
    pinConnectingGhostElement.style.opacity = '100%';
    pinConnectingGhostElement.style.pointerEvents = 'all';

    // Change CSS options for interactableGhost to show correctly
    var interactableGhostDiv = document.getElementById('interactableGhost');
    interactableGhostDiv.style.opacity = '100%';
    interactableGhostDiv.style.pointerEvents = 'all';
}

function connectToServer() {

    // Send HTTP request to server and wait for response,
    // Get serverIdText
    var serverIdText = document.getElementById('serverIdText').value;
    var serverIdTextURL = 'http://' + serverIdText + ':4825/command'

    // Define connection data
    var postString = ("command:attemptConnection|" + uniqueHostname + "|" + generatedPSK)

    fetch(serverIdTextURL, {
        method: 'POST',
        mode: 'cors',
        headers: {
           'Content-Type': 'text/plain'
        },
        body: postString
       }).then(function(response) {
        return response.text();
    }).then(function(responseData) {

        console.log("Got response: " + responseData)
        if (responseData.includes('response')) {
            // Data is a response, split into array
            var responseDataSplit = responseData.split("|")
            console.log(responseDataSplit)
            // Check if PIN auth required
            // 1 pin, 2 audio
            pinAuthRequired = responseDataSplit[1];
            serverAudioAllowed = responseDataSplit[2];

            // Modify Ghost data
            if (pinAuthRequired == "False") {
                var pinRequiredGhostElement = document.getElementById('pinRequiredGhost');
                pinRequiredGhostElement.style.opacity = '50%';
                pinRequiredGhostElement.style.pointerEvents = 'none';

                var pinSubmitButtonElement = document.getElementById('pinSubmitButton');
                pinSubmitButtonElement.innerHTML = 'Connect To Server'

                var pinConnectingGhostElement = document.getElementById('pinConnectingGhost');
                pinConnectingGhostElement.style.opacity = '100%';
                pinConnectingGhostElement.style.pointerEvents = 'all';
            }

            if (serverAudioAllowed == "False") {
                var audioAllowedGhostElement = document.getElementById('audioAllowedGhost');
                audioAllowedGhostElement.style.opacity = '50%';
                audioAllowedGhostElement.style.pointerEvents = 'none';
            }


            showConnectionPanel()
        }

    })
}

function sendPauseCommandToServer(pauseButtonElement) {

    var serverIdText = document.getElementById('serverIdText').value;
    var serverIdTextURL = 'http://' + serverIdText + ':4825/command'

    // Define connection data
    var postString = ("command:pause|")

    // Send command
    fetch(serverIdTextURL, {
        method: 'POST',
        mode: 'cors',
        headers: {
           'Content-Type': 'text/plain'
        },
        body: postString
       }).then(function(response) {
        return response.text();
    }).then(function(responseData) {

        console.log("Got response: " + responseData)
        
        // Toggle Button Text
        if (responseData.includes('response:unpaused')) {
            pauseButtonElement.innerHTML = 'Pause Casting'
        }
        else if (responseData.includes('response:paused')) {
            pauseButtonElement.innerHTML = 'Resume Casting'
        }

    })
}

function sendKickCommandToServer(kickButtonElement) {

    var serverIdText = document.getElementById('serverIdText').value;
    var serverIdTextURL = 'http://' + serverIdText + ':4825/kick'

    // Define connection data
    var postString = ("command:kick|") + generatedPSK

    // Send command
    fetch(serverIdTextURL, {
        method: 'POST',
        mode: 'cors',
        headers: {
           'Content-Type': 'text/plain'
        },
        body: postString
       }).then(function(response) {
        return response.text();
    }).then(function(responseData) {

        console.log("Got response: " + responseData)
        
        // Toggle Button Text
        // if (responseData.includes('response:clientKicked')) {
        // }
        // else if (responseData.includes('response:paused')) {
        //     pauseButtonElement.innerHTML = 'Resume Casting'
        // }

    })
}

function stopCasting() {
    try {
        // Reset JS applet and stop rtc peer
        pc.close()

        // Close mediaStream tracks
        for (var msTrack of mediaStream.getTracks()) {
            msTrack.stop()
        }
    }
    catch (error) {
        console.log(error)
    }
    // Reset CSS DIV Elements

    console.log("Reseting DIV Elements")

    var pinRequiredGhostElement = document.getElementById('pinRequiredGhost');
    pinRequiredGhostElement.style.opacity = '100%';
    pinRequiredGhostElement.style.pointerEvents = 'all';

    var pinSubmitButtonElement = document.getElementById('pinSubmitButton');
    pinSubmitButton.innerHTML = 'Submit PIN'

    // Main ghost 
    var interactableGhostElement = document.getElementById('interactableGhost');
    interactableGhostElement.style.opacity = '50%';
    interactableGhostElement.style.pointerEvents = 'none';

    // Reset PIN
    var pinTextElement = document.getElementById('pinText');
    pinTextElement.value = '';

    var pinConnectingGhostElement = document.getElementById('pinConnectingGhost');
    pinConnectingGhostElement.style.opacity = '50%';
    pinConnectingGhostElement.style.pointerEvents = 'none';

}

function loadStorageVariables() {
    // Attempt to load PSK, undefined if not set

    // Load PSK
    var pskStorageBit = window.localStorage.getItem("generatedPSK");

    // If undefined, set
    if (pskStorageBit == undefined) {
        // Does not exist, generate
        console.log("Generating PSK")
        generatedPSK = generatePSKRandomString(12)

        window.localStorage.setItem("generatedPSK", generatedPSK)
    } 
    else {
        // Was found, set
        console.log("Setting PSK")
        generatedPSK = pskStorageBit
    }

    console.log("PSK: " + generatedPSK)

    var pskDisplayElement = document.getElementById('pskDisplayElement');
    pskDisplayElement.innerText = ('PSK: ' + generatedPSK);

    // Attempt to load Hostname, if fails then ghost everything until one exists
    var hostnameStorageBit = window.localStorage.getItem("hostname");

    // If undefined, set
    if (hostnameStorageBit == undefined) {
        // Does not exist, ghost elements and show hostname submission

        var ghostDiv = document.getElementById('blockIfNoHostname');
        ghostDiv.style.opacity = '0%';
        ghostDiv.style.pointerEvents = 'none';

        var requiredNameDivElement = document.getElementById('requiredNameDiv');

        // Append Text, Button and Input
        var textElement = document.createElement('h5');
        textElement.textContent = "Please give a name for server identification"
        requiredNameDivElement.appendChild(textElement);

        // Input
        var inputElement = document.createElement('input');
        inputElement.type = 'text';
        inputElement.placeholder = 'John Doe';
        inputElement.id = 'inputHostnameID';
        requiredNameDivElement.appendChild(inputElement);

        // Button
        var buttonElement = document.createElement('button');
        buttonElement.textContent = 'Submit Name'
        buttonElement.id = 'inputButtonID'
        requiredNameDivElement.appendChild(buttonElement);

        var buttonElementID = document.getElementById('inputButtonID');


        // Add event listener for buttonElement

        buttonElementID.addEventListener('click', function() {
            // Get input element and set base on that
            var textElementID = document.getElementById('inputHostnameID');

            if (textElementID.value == '') {
                console.log("No Text")
            }
            else {
                window.localStorage.setItem("hostname", textElementID.value)

                uniqueHostname = textElementID.value;
                
                // Reset
                requiredNameDivElement.innerHTML = '';
                ghostDiv.style.opacity = '100%';
                ghostDiv.style.pointerEvents = 'all';
            }
            
        });

    } 
    else {
        // Load
        
        uniqueHostname = hostnameStorageBit
    }

    var pinConnectingGhostElement = document.getElementById('pinConnectingGhost');
    pinConnectingGhostElement.style.opacity = '50%';
    pinConnectingGhostElement.style.pointerEvents = 'none';

    console.log("Hostname: " + uniqueHostname)
}

function addEventListenersForAll() {

    // Button Listeners

    var connectToServerButton = document.getElementById('addServerButton');

    connectToServerButton.addEventListener('click', function() {
        connectToServer()
    });

    var pinEntryButton = document.getElementById('pinSubmitButton');

    pinEntryButton.addEventListener('click', function() {
        attemptConnectionWithPIN()
    });

    var pauseButtonElement = document.getElementById('pauseButton');

    pauseButtonElement.addEventListener('click', function() {
        sendPauseCommandToServer(pauseButtonElement)
    });

    var stopButtonElement = document.getElementById('stopButton');

    stopButtonElement.addEventListener('click', function() {
        stopCasting()
    });

    var kickButtonElement = document.getElementById('kickButton');

    kickButtonElement.addEventListener('click', function() {
        sendKickCommandToServer(kickButtonElement)
    });

    // Resolution select listener
    var resolutionOptionsElement = document.getElementById('resolutionOptions');

    resolutionOptionsElement.addEventListener('change', function() {
        // Change global values depending on selection
        if (resolutionOptionsElement.value == '1920x1080') {
            requestedWidth = 1920
            requestedHeight = 1080
        }
        else if (resolutionOptionsElement.value == '1280x720') {
            requestedWidth = 1280
            requestedHeight = 720
        }
        else if (resolutionOptionsElement.value == '640x480') {
            requestedWidth = 640
            requestedHeight = 480
        }
    });

    // Set default to 720
    resolutionOptionsElement.value = '1280x720';

    // Audio Checkbox listener
    // var audioCheckboxElement = document.getElementById('audioCheckbox');

    // audioCheckboxElement.addEventListener('change', function() {
    //     // Change global values depending on selection
    //     if (audioCheckboxElement == false) {
    //         sendClientAudio = false;
    //     }
    //     else if (audioCheckboxElement === true) {
    //         sendClientAudio = true;
    //     }
    // });

    // PSK Listener
    var copyPSKButtonElement = document.getElementById('copyPSKButton');
    copyPSKButtonElement.addEventListener('click', function() {
        // Put into clipboard 
        navigator.clipboard.writeText(generatedPSK)
    });

    // Load storage variables
    loadStorageVariables()

    console.log("SimpleCast Loaded, Event Listeners Registered")
}

window.onload = addEventListenersForAll()