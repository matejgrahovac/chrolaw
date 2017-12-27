// Chrome Extension with Database Backend (chrolaw), project by Matej Grahovac
// www.matejgrahovac.de
//
// An extension for Chrome, that recognizes references to German laws or bills
// and displays the quotes in an injected sidebar.
//
// this is the chrome extension background script which runs idle in the
// background until its needed
// https://developer.chrome.com/extensions/background_pages

var background = {

  // event listener for messages from the extensions content script
  // (here: contentScript.js)
  // https://developer.chrome.com/apps/runtime#event-onMessage
  listener: function() {
    chrome.runtime.onMessage.addListener(function (message, sender, response) {
      if ((message.from === 'contentScript') && (message.subject === 'mafou')) {
        // highlighted matches are sent to backend server
        background.sendJson(message.content);
      }
    });
  },

  // prototype function for sending messages (here: to content script)
  // https://developer.chrome.com/apps/runtime#method-sendMessage
  message: function(subject, content) {
    // when messages are beeing sent from background to content script,
    // the active tab needs to be identified
    // https://developer.chrome.com/extensions/tabs#method-query
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs){
      console.log(tabs[0].id)
      chrome.tabs.sendMessage(tabs[0].id, {
        from:    'background',
        subject: subject,
        content: content
      })
    })
  },

  // highlighted matches are being sent to backend server via AJAX request as
  // JSON file, https://www.w3schools.com/js/js_json_http.asp
  sendJson: function(data) {
    var xhr = new XMLHttpRequest();
    url = "hlkahsjdflkjasdfljkxxxxx00/receivejson"
    // url of server with port and route (here: flask app route)
    // url = "http://127.0.0.1:5000/receivejson"
    xhr.open("POST", url, true);
    xhr.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
    // array of objects converted into JSON file
    xhr.send(JSON.stringify(data));
    console.log(data)
    // callback function which receives results from backend server
    xhr.onreadystatechange = function() {
      if(xhr.readyState === 4 && this.status == 200) {
        receivedContent = JSON.parse(this.responseText)
        console.log(receivedContent);
        background.message("content", receivedContent);
      }
    };
  }

}

background.listener();
