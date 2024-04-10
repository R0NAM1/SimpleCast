// import * as browser from './node_modules/webextension-polyfill/dist/browser-polyfill.js';
// var browser = require("./node_modules/webextension-polyfill/dist/browser-polyfill.js")

var discoveredServerArray = [];
var serverAudioAllowed = false;
var sendClientAudio = true;
var pinAuthRequired = false;
var requestedWidth = 1280;
var requestedHeight = 720;
var pc = null;
var mediaStream;
var generatedPSK = 'none';
var uniqueHostname = 'none';
var doesNicknameExist = false;
var currentConnectionIP = '';
var currentConnectionStatus = '';
var currentConnectionTimeout = 0;
var webRtcActive = false

// false display, true user
var userMediaOrDisplay = false;

// I need to implement dns sd discovery myself, cannot find client only library, plus not sure if I can open udp as an extension -_-

// PSK string generator
function generatePSKRandomString(length = 8) {
    return Math.random().toString(16).substr(2, length);
}

// Wait 300 ms to let array catchup
async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}


async function updateTimeoutWhileAboveZero() {
    await sleep(300)

    currentConnectionTimeout = currentConnectionTimeout - 2;

    try {

        while (currentConnectionTimeout > 0) {
            var updateTimeDiv = document.getElementById('timeoutChange');
            await sleep(1000);

            // Set -1
            currentConnectionTimeout = currentConnectionTimeout - 1;

            // Set element
            updateTimeDiv.innerText = currentConnectionTimeout
        }

        if (webRtcActive == false) {
            console.log("Timer at 0")
            stopCasting()
        }

    }
    catch (error) {
        // Element must not exist, stop all
        console.log("Timer not exist")
        console.log(error)
    }
}

async function startWebRTCMirroring() {

    console.log("Starting WebRTC")
    webRtcActive = true

    var config = {
        sdpSemantics: 'unified-plan', // Modern SDP format.
        iceServers: [{"urls": "stun:" + currentConnectionIP}] //This will be dynamic based on server config later
    };

    pc = new RTCPeerConnection(config); // Set server to config
    
    if (userMediaOrDisplay == false) {
        console.log("Generating getDisplayMedia")
        // Grab MediaStream
        setStatusText("Grabbing getDisplayMedia")
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
    }
    else {
        console.log("Generating getUserMedia")
        // Grab MediaStream, do userMedia eventually?
        setStatusText("Grabbing getUserMedia")

        mediaStream = await navigator.mediaDevices.getUserMedia({
            video: { width: requestedWidth, height: requestedHeight },
            audio: true // Set to true if you want to capture audio as well
        });
    }


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

    var serverIdTextURL = 'http://' + currentConnectionIP + ':4825/sdpOffer'

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
        
        setStatusText("Connection Active")
        
        // Connection is finished, make connection
    
        var allRemove = document.getElementsByClassName('doRemove');
    
        while (allRemove[0]) {
            allRemove[0].remove()
        }

        var connectedText = document.createElement('div');
        connectedText.innerHTML = 'You are <br> connected!';
        connectedText.id = 'youareconnected'

        var surDiv = document.getElementById('selectServerDiv');
        surDiv.appendChild(connectedText);
    })



}

function attemptConnectionWithPIN() {
    // Send HTTP request to server and wait for response,
    // Get serverIdText
    var serverIdTextURL = 'http://' + currentConnectionIP + ':4825/command'

    
    // Define connection data
    if (pinAuthRequired == "False") {
        var postString = ("command:connect|" + "000000")
    }
    else {
        var PINValue = document.getElementById('pinBox').value;
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
            setStatusText("Connection Accepted, Starting WebRTC")
            startWebRTCMirroring()
        }
        else {
            console.log("REJECTED")
            setStatusText("Connection Refused")
            stopCasting()
        }

    })
}

function stopCasting() {
    webRtcActive = false
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

    setStatusText("Stopped Casting")

    console.log("Reseting DIV Elements")

    var mainDiv = document.getElementById('selectServerDiv');
    mainDiv.innerHTML = " Select a server from the browser <br> or add one manually"
    mainDiv.style.marginTop = '35vh';

}

function connectToServer() {

    // Send HTTP request to server and wait for response,
    var serverIdTextURL = 'http://' + currentConnectionIP + ':4825/command'

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
            currentConnectionTimeout = responseDataSplit[3];
        }

    })
}

function sendPauseCommandToServer(pauseButtonElement) {

    var serverIdTextURL = 'http://' + currentConnectionIP + ':4825/command'

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
            setStatusText("Casting Resumed")
            pauseButtonElement.innerHTML = 'Pause Casting'
        }
        else if (responseData.includes('response:paused')) {
            setStatusText("Casting Paused")
            pauseButtonElement.innerHTML = 'Resume Casting'
        }
        else if (responseData.includes('response:notAuthorized')) {
            setStatusText("Pausing Not Authorized")
        }

    })
}

function sendKickCommandToServer() {

    var serverIdTextURL = 'http://' + currentConnectionIP + ':4825/kick'

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

        
        if (responseData == 'response:notConnected') {
            setStatusText("No Connection To Kick")
        }
        else if (responseData == 'response:clientKicked') {
            setStatusText("Connected Client Kicked")
        }
        else if (responseData == 'response:notAuthorized') {
            setStatusText("Not authorized to kick client")
        }
    })
}

function sendToggleCommandToServer() {

    var serverIdTextURL = 'http://' + currentConnectionIP + ':4825/toggle'

    // Define connection data
    var postString = ("command:toggleCast|") + generatedPSK

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

        if (responseData == 'response:enabledCasting') {
            setStatusText("Casting Enabled")
        }
        else if (responseData == 'response:disabledCasting') {
            setStatusText("Casting Disabled")
        }
        else if (responseData == 'response:notAuthorized') {
            setStatusText("Not authorized to toggle casting")
        }

    })
}

function waitToGetHostname() {
    // No hostname was found, show elements and register event listener

    // Switch elements
    var hostnameGhost = document.getElementById('enterNameGhost');
    hostnameGhost.style.display = 'block';

    var mcGhost = document.getElementById('mainControlPanelGhost');
    mcGhost.style.display = 'none';
    

    var submitButton = document.getElementById('enterNameButton');

    submitButton.addEventListener('click', function() {
        
        // If text in box exists, store
        var hostnameBox = document.getElementById('enterNameTextBox');

        if (hostnameBox.value == '') {
            // Do nothing
            console.log("Is empty")
        }
        else {
            window.localStorage.setItem("hostname", hostnameBox.value)

            // Switch elements
            var hostnameGhost = document.getElementById('enterNameGhost');
            hostnameGhost.style.display = 'none';
            
            var mcGhost = document.getElementById('mainControlPanelGhost');
            mcGhost.style.display = 'block';

            // Set div
            var hostText = document.getElementById('hostDisplayElement');
            hostText.innerText = hostnameBox.value
        }

    });

}

function loadStorageVariables() {
    console.log("Loading Variables From Local Storage")
    // Attempt to load PSK, undefined if not set

    // Load PSK
    var pskStorageBit = window.localStorage.getItem("generatedPSK");

    // If undefined, set
    if (pskStorageBit == undefined) {
        // Does not exist, generate
        console.log("No PSK found, generating...");
        generatedPSK = generatePSKRandomString(12);
        console.log("Generated PSK is " + generatedPSK);

        window.localStorage.setItem("generatedPSK", generatedPSK)
    } 
    else {
        // Was found, set
        console.log("PSK Found: " + pskStorageBit)
        generatedPSK = pskStorageBit
    }

    console.log("PSK: " + generatedPSK)

    var pskDisplayElement = document.getElementById('pskDisplayElement');
    pskDisplayElement.innerText = ('PSK: ' + generatedPSK);

    // Attempt to load Hostname, if fails then ghost everything until one exists
    var hostnameStorageBit = window.localStorage.getItem("hostname");

    // If undefined, set
    if (hostnameStorageBit == undefined) {
        console.log("No hostname found, waiting for user submission")
        doesNicknameExist = false;
        waitToGetHostname();
    } 
    else {
        // Load
        console.log("Hostname found: " + hostnameStorageBit)
        uniqueHostname = hostnameStorageBit

        // Set div
        var hostText = document.getElementById('hostDisplayElement');
        hostText.innerText = uniqueHostname
    }

    // Check if any servers are favrioted, if undefined init empty array
    var storageFavroiteServers = window.localStorage.getItem("favServer");
    
    if (storageFavroiteServers == undefined) {
        window.localStorage.setItem("favServer", JSON.stringify([]))
    }

}

function setStatusText(text) {
    var statusElement = document.getElementById('latestStatusText');

    statusElement.innerHTML = 'Status: <br> ' + text
}


async function reloadDnsList() {


    await sleep(300)
    // Remove all dnsListItem, clears list

    var toRemoveItems = document.getElementsByClassName('dnsListItem');

    while (toRemoveItems[0]) {
        toRemoveItems[0].remove();
    }

    var topD = document.getElementById('dns-sd-servers');
    topD.innerHTML = ''

    var favServerArray = JSON.parse(window.localStorage.getItem("favServer"));
    
    for (let itemArray of discoveredServerArray) {

        var dnsItemDiv = document.createElement('div');
        dnsItemDiv.className = 'dnsListItem';
        
        // Item 1 - 
        var serverNameDiv = document.createElement('div');
        serverNameDiv.className = 'serverName';
        serverNameDiv.innerText = itemArray[1];
        
        // Add event listener for selecting 
        serverNameDiv.addEventListener('click', function() {
            loadServerToMain(itemArray[1]);
        })

        dnsItemDiv.appendChild(serverNameDiv);
        
        // Item 2 -
        var favServerImage = document.createElement('img');
        favServerImage.className = 'favServer';

        // Check if itemArray exists in favStorage, if so do filled in
        var isFavr = false;
        for (var iA of favServerArray) {

            var checkArray = [itemArray[1], itemArray[0]];
            if (JSON.stringify(iA) == JSON.stringify(checkArray)) {
                isFavr = true
            }
        }

        if (isFavr == true){
            favServerImage.src = 'star-filled.png';
        }
        else {
            favServerImage.src = 'star-outline.png';
        }

        // Add event listener for star to add to storage

        favServerImage.addEventListener('click', function() {
            
            // If already favroited, remove,
            // else add

            var isFav = false
            // Check, [Name, IP]
            

            // Remove itemArray from storage
            for (var iA of favServerArray) {

                var checkArray = [itemArray[1], itemArray[0]];
                if (JSON.stringify(iA) == JSON.stringify(checkArray)) {
                    isFav = true
                }
            }

            // if false, add to favServer
            if (isFav == false){

                var checkArray = [itemArray[1], itemArray[0]];
                favServerArray.push(checkArray);

                window.localStorage.setItem("favServer", JSON.stringify(favServerArray))

            }
            else {
                // Is True, remove

                var newArray = []
                // Remove itemArray from storage
                for (var iA of favServerArray) {
                    console.log(iA)
                    console.log(itemArray) // redo
    
                    var checkArray = [itemArray[1], itemArray[0]];
                    if (JSON.stringify(iA) == JSON.stringify(checkArray)) {
                        //pass
                    }
                    else {
                        newArray.push(iA);
                    }
                } 

                window.localStorage.setItem("favServer", JSON.stringify(newArray))

            }

            // Reload lists
            reloadDnsList()
            reloadFavList()

        })
        
        dnsItemDiv.appendChild(favServerImage);

        // Add
        var topDiv = document.getElementById('dns-sd-servers');

        topDiv.appendChild(dnsItemDiv);
        
    }
}

function getServerList() {
    
    // Attempt to fetch http://simplecastdiscovery.local:4825/discover
    // console.log("Gathering DNS-SD")
    
    fetch("http://simplecastdiscovery.local:4825/discover", {
        method: 'GET',
        mode: 'cors'
    }).then(function(response) {
        return response.text();
    }).then(function(responseData) {

        // console.log("Got response: ")
        responseData = JSON.parse(responseData)
        // console.log(responseData)

        // Reset discoveredServerArray
        discoveredServerArray = []

        for (let serverItem of responseData) {

            try {

                // Attempt to get status of a server, if cannot don't add
                fetch("http://" + serverItem + ":4825/command", {
                    method: 'POST',
                    mode: 'cors',
                    body: 
                    "command:statusProbe",
                    headers: {
                        'Content-Type': 'text/plain'
                    },
                }).then(function(response) {
                    return response.text();
                }).then(function(responseData) {
                    
                    responseData = responseData.split('|');                    
                    // Got valid response, add to discoveredServerArray
                    var tempServerArray = [serverItem, responseData[0], responseData[1]]
                    // console.log("Adding to global: " + tempServerArray)

                    discoveredServerArray.push(tempServerArray);
                })
            
            }
            catch {
                // Do Nothing
            }
        }

        // Done gathering servers, reloadDnsList()
        reloadDnsList()
    }).catch(function(error) {
        // Cannot reach, set
        console.log(error)
        var topD = document.getElementById('dns-sd-servers');
        topD.innerHTML = 'Cannot <br> reach <br> DNS-SD <br> service'

    });
}


function reloadFavList() {
    // Remove all favListItem, clears list

    var toRemoveItems = document.getElementsByClassName('favListItem');

    while (toRemoveItems[0]) {
        toRemoveItems[0].remove();
    }
    

    // Grab array
    var storageFavroiteServers = JSON.parse(window.localStorage.getItem("favServer"));

    for (let itemArray of storageFavroiteServers) {
   
        var favItemDiv = document.createElement('div');
        favItemDiv.className = 'favListItem';
        
        // Item 1 - 
        var serverNameDiv = document.createElement('div');
        serverNameDiv.className = 'serverName';
        serverNameDiv.innerText = itemArray[0];

        // Add event listener for selecting 
        serverNameDiv.addEventListener('click', function() {
            loadServerToMain(itemArray[0], itemArray[1]);
        })
        
        favItemDiv.appendChild(serverNameDiv);
        
        // Item 2 -
        var favServerImage = document.createElement('img');
        favServerImage.className = 'favServer';
        favServerImage.src = 'star-filled.png';

        // Add event listener for star to remove from storage

        favServerImage.addEventListener('click', function() {
            var newArray = []
            // Remove itemArray from storage
            console.log("Remove: " + itemArray[0])
            for (var iA of storageFavroiteServers) {
                if (JSON.stringify(iA) == JSON.stringify(itemArray)) {

                }
                else {
                    newArray.push(iA);
                }
            }

            // Load into storage
            window.localStorage.setItem("favServer", JSON.stringify(newArray))

            reloadFavList();
            reloadDnsList();
        })
        
        favItemDiv.appendChild(favServerImage);

        // Add
        var topDiv = document.getElementById('favservers');

        topDiv.appendChild(favItemDiv);
        
    }
}

function addServerMain() {

    // Hide mainControlPanelGhost and show addServerGhost

    var addGhost = document.getElementById('addServerGhost');
    addGhost.style.display = 'inline-block';

    var mcGhost = document.getElementById('leftPanel');
    mcGhost.style.display = 'none';

    // Add event listener for elements

    var addServerButtonElement = document.getElementById('addServerButton');

    addServerButtonElement.addEventListener('click', function() {
        
        // Add new server to local storage if does not exist,
        // favServer is [["server1", "10.0.0.1"], ["server2", "10.0.0.2"]]
        // Load array
        var storageFavroiteServers = JSON.parse(window.localStorage.getItem("favServer"));

        // Load text
        var serverName = (document.getElementById('addServerNameBox')).value;

        var serverIp = (document.getElementById('addServerIPBox')).value;

        
        
        if (serverName == '' || serverIp == '' ) {
            console.log("No text in boxes")
        }
        else {
            // Clear
            (document.getElementById('addServerNameBox')).value = '';
            (document.getElementById('addServerIPBox')).value = '';

            // Create array
            var tempArray = [serverName, serverIp];
            var doesExist = false

                // Check if already exists, itterate over array
                for (var serverItem of storageFavroiteServers) {
                    if (JSON.stringify(tempArray) == JSON.stringify(serverItem)) {
                        doesExist = true;
                    }
                }

                if (doesExist == true) {
                    console.log("Server exists, do not add")
                    setStatusText("Already Exists, Cannot Add")
                    // Already exists, do not add
                    // Reset divs 
                    var addGhost = document.getElementById('addServerGhost');
                    addGhost.style.display = 'none';
                    
                    var mcGhost = document.getElementById('leftPanel');
                    mcGhost.style.display = 'inline-block'
                }
                else {
                    console.log("Server does not exists, add")
                    setStatusText("Added Manual Server")
                    // Push
                    storageFavroiteServers.push(tempArray);
                    
                    // Reload into storage
                    window.localStorage.setItem("favServer", JSON.stringify(storageFavroiteServers))
                    
                    // Reset divs 
                    var addGhost = document.getElementById('addServerGhost');
                    addGhost.style.display = 'none';
                    
                    var mcGhost = document.getElementById('leftPanel');
                    mcGhost.style.display = 'inline-block';

                    reloadFavList()
                }
        
        }

    });
}

async function loadServerToMain(serverName, serverIp = undefined) {

    // console.log(serverName)
    // console.log(serverIp)

    var selectServerDivElement = document.getElementById('selectServerDiv');
    selectServerDivElement.innerHTML = '';
    selectServerDivElement.style.marginTop = '5vh';

    // Get IP, STATUS and make global

    if (serverIp != undefined) {
        fetch("http://" + serverIp + ":4825/command", {
                    method: 'POST',
                    mode: 'cors',
                    body: 
                    "command:statusProbe",
                    headers: {
                        'Content-Type': 'text/plain'
                    },
                }).then(function(response) {
                    return response.text();
                }).then(function(responseData) {
                    responseData = responseData.split('|');                    
                    // Got valid response, add to discoveredServerArray
                    var tempServerArray = [serverIp, serverName, responseData[1]]
                    // console.log("Adding to global: " + tempServerArray)

                    discoveredServerArray.push(tempServerArray);
                })
    }

    await sleep(300)

    for (var itemServer of discoveredServerArray) {
        // ip, name, status
        if (itemServer[1] == serverName) {
            currentConnectionIP = itemServer[0];
            currentConnectionStatus = itemServer[2];
        }
    }
  
    // Create label
    var serverLabel = document.createElement('div');
    serverLabel.id = 'serverNameHeader';
    serverLabel.innerText = serverName;

    selectServerDivElement.appendChild(serverLabel);

    // Check server status, if not open, let know

    if (currentConnectionStatus == 'open') {

        // Server is open!
        // Attempt to connect and start webrtc

        connectToServer();
        
        await sleep(500)

        console.log(pinAuthRequired)

        // Depending on if pin auth, show certain elements
        if (pinAuthRequired == "True") {
            // Create pin text, input, button
            var pinText = document.createElement('div');
            pinText.innerText = '--Input PIN on screen--'
            pinText.id = 'pinText';
            pinText.className = 'doRemove';

            selectServerDivElement.appendChild(pinText);

            var pinBox = document.createElement('input');
            pinBox.type = 'text';
            pinBox.id = 'pinBox';
            pinBox.placeholder = '12345';
            pinBox.className = 'doRemove';

            selectServerDivElement.appendChild(pinBox);

            pinBox.focus();
            pinBox.select();

            var pinButton = document.createElement('button');
            pinButton.textContent = 'Submit PIN';
            pinButton.id = 'pinButton';
            pinButton.className = 'doRemove';


            // Add event listener 

            selectServerDivElement.appendChild(document.createElement('br'));
            selectServerDivElement.appendChild(pinButton);


            pinButton.addEventListener('click', function() {
                attemptConnectionWithPIN()
            });


        }
        else {

            // Create pin text, input, button
            var conText = document.createElement('div');
            conText.innerText = '--Connect when ready--'
            conText.id = 'pinText';
            conText.className = 'doRemove';

            selectServerDivElement.appendChild(conText);

            var conButton = document.createElement('button');
            conButton.textContent = 'Connect To Server';
            conButton.id = 'pinButton';
            conButton.className = 'doRemove';

            // Add event listener 

            selectServerDivElement.appendChild(document.createElement('br'));
            selectServerDivElement.appendChild(conButton);


            conButton.addEventListener('click', function() {
                attemptConnectionWithPIN()
            });
        }

        
        // media Select
        
        var mediaText = document.createElement('div');
        mediaText.className = 'doRemove';
        mediaText.innerText = 'Capture Source';
        mediaText.id = "capText";

        selectServerDivElement.appendChild(mediaText);

        var mediaSelect = document.createElement('select');
        mediaSelect.className = 'doRemove';
        mediaSelect.id = "mediaOptions";
        
        // options
        var option1 = document.createElement('option');
        option1.value = 'Display';
        option1.innerText = 'Display';
        
        var option2 = document.createElement('option');
        option2.value = 'Camera';
        option2.innerText = 'Camera';
        
        mediaSelect.appendChild(option1);
        mediaSelect.appendChild(option2);
        
        selectServerDivElement.appendChild(mediaSelect);
        
        
        // Add select event listener
        mediaSelect.addEventListener('change', function() {
            // Change global values depending on selection
            if (mediaSelect.value == 'Display') {
                userMediaOrDisplay = false
            }
            else if (mediaSelect.value == 'Camera') {
                userMediaOrDisplay = true
                
            }
        });
        
        // Res select
        
        // Add resolution control and audio?
        var capResText = document.createElement('div');
        capResText.className = 'doRemove';
        capResText.innerText = 'Capture Resolution';
        capResText.id = "capText";

        selectServerDivElement.appendChild(capResText);
        
        var capResSelect = document.createElement('select');
        capResSelect.className = 'doRemove';
        capResSelect.id = "resolutionOptions";

        // options
        var option1 = document.createElement('option');
        option1.value = '1920x1080';
        option1.innerText = '1920x1080';

        var option2 = document.createElement('option');
        option2.value = '1280x720';
        option2.innerText = '1280x720';

        var option3 = document.createElement('option');
        option3.value = '640x480';
        option3.innerText = '640x480';

        capResSelect.appendChild(option1);
        capResSelect.appendChild(option2);
        capResSelect.appendChild(option3);

        // Add select event listener
        capResSelect.addEventListener('change', function() {
            // Change global values depending on selection
            if (capResSelect.value == '1920x1080') {
                requestedWidth = 1920
                requestedHeight = 1080
            }
            else if (capResSelect.value == '1280x720') {
                requestedWidth = 1280
                requestedHeight = 720
            }
            else if (capResSelect.value == '640x480') {
                requestedWidth = 640
                requestedHeight = 480
            }
        });
    
        // Set default to 720
        capResSelect.value = '1280x720';

        selectServerDivElement.appendChild(capResSelect);

        // Append timer
        var timeoutDiv = document.createElement('div');
        timeoutDiv.className = 'doRemove';
        var timeoutDivText = document.createElement('div');
        var timeoutDivNum = document.createElement('div');

        timeoutDiv.id = 'timeoutDiv'

        timeoutDivText.innerHTML = 'Timeout:'

        timeoutDiv.appendChild(timeoutDivText);

        timeoutDivNum.id = 'timeoutChange';
        
        timeoutDiv.appendChild(timeoutDivNum);

        selectServerDivElement.append(timeoutDiv);

        setStatusText("Connecting to server")

        updateTimeoutWhileAboveZero()        
    }
    else {
        var cannotText = document.createElement('div');
        cannotText.innerHTML = '--Server not open-- <br> --Cannot connect--'
        cannotText.id = 'cannotText';
        setStatusText("Connection Refused")

        selectServerDivElement.appendChild(cannotText);
    }

}

function addEventListenersForAll() {
    
    // Load storage variables
    loadStorageVariables()

    // Button Listeners
    // PSK Listener
    var copyPSKButtonElement = document.getElementById('copyPSKButton');
    copyPSKButtonElement.addEventListener('click', function() {
        // Put into clipboard 
        setStatusText("Copied PSK")
        navigator.clipboard.writeText(generatedPSK)
    });

    // Listen for manual add server button 

    var addServerManButton = document.getElementById('addListItem');

    addServerManButton.addEventListener('click', function() {
        addServerMain()
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
        sendKickCommandToServer()
    });


    var toggleCastButtonElement = document.getElementById('toggleCastButton');

    toggleCastButtonElement.addEventListener('click', function() {
        sendToggleCommandToServer(toggleCastButtonElement)
    });



    reloadFavList()

    // Set interval for getServerList, do immediently
    getServerList();

    setInterval(getServerList, (10 * 1000))

    console.log("SimpleCast Loaded, Event Listeners Registered")
    setStatusText("Client Loaded")
}



window.onload = addEventListenersForAll()