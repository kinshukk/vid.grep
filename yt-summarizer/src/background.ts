chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'summarize') {
    // The native messaging host will be responsible for executing the script.
    chrome.runtime.sendNativeMessage(
      'com.google.chrome.example.echo',
      { text: request.url },
      (response) => {
        if (chrome.runtime.lastError) {
          sendResponse({ error: chrome.runtime.lastError.message });
        } else {
          sendResponse({ summary: response.text });
        }
      }
    );
    return true; // Indicates that the response is sent asynchronously.
  }
});