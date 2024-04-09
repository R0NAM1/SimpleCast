let extensionWindowId = null; // Store the window ID of your extension's window

chrome.action.onClicked.addListener(() => {
 // Check if the extension's window is already open
 chrome.windows.getAll({}).then(windows => {
    const extensionWindow = windows.find(window => window.id === extensionWindowId);

    if (extensionWindow) {
      // If the window is open, close it
      chrome.windows.remove(extensionWindow.id);
      extensionWindowId = null; // Reset the window ID
    } else {
      // If the window is not open, open a new one
      chrome.windows.create({
        url: chrome.runtime.getURL("client.html"),
        type: "popup",
       width: 900, // Desired width
        height: 700, // Desired height
      }).then(window => {
        extensionWindowId = window.id; // Store the new window ID
      });
    }
 });
});
