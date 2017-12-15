// Chrome Extension with Database Backend (chrolaw), project by Matej Grahovac
// www.matejgrahovac.de
//
// An extension for Chrome, that recognizes references to German laws or bills
// and displays the quotes in an injected sidebar.
//
// this is the chrome extension contentscript which is injected into each page
// matching the pattern in the manifest.json file
// https://developer.chrome.com/extensions/content_scripts

var contentScript = {

  // part of the webpage DOM to be searched
  webPart: document.body,

  // state of sidebar, false == closed
  sidebar: false,

  // event listener for messages from the extensions background script
  // (here: background.js)
  // https://developer.chrome.com/apps/runtime#event-onMessage
  listener: function() {
    chrome.runtime.onMessage.addListener(function (message, sender, response) {
      if ((message.from === 'background') && (message.subject === 'content')) {
        // data from backend is received and sidebar content can be created
        console.log("Quotes found:");
        console.log(message.content)
        contentScript.sidebarCont(message.content);
      }
    });
  },

  // usage of https://markjs.io/ plugin (in lib/) for quote highlighting.
  // and collection of quote data for backend
  search: function() {
      // regular expression to find law quotes
      //starts with §/§§/art/ART/aRt, ends with sth. like Foo234-BaaR 2000/XI
      // other and older regex patterns for testing purpose
      // to test regex yourself check out: https://regex101.com
      // var regex = /(§§?|[aA][Rr][Tt]\.?) ?(\d+[a-z]?) ?([aA][Bb][Ss][.]? ?(\d*)|([iIvVxX]*))? ?.*?([0-9A-Z-]+[0-9a-zA-ZöäüÖÄÜ-]*[A-Z]+[0-9a-zA-ZöäüÖÄÜ-]*( [IVX\d]+)*)/g;
      // var regex = /(§§?|[aA][Rr][Tt]\.?) ?(\d+[a-z]?) ?.*?[\dA-ZÜÖÄ]{1}[\w-]*[A-ZÖÜÄ]{1}( [IVX\d]+)*/g;
      // var regex = /(§§?|[aA][Rr][Tt]\.?) .*?([0-9A-Z-]+[0-9a-zA-ZöäüÖÄÜ-]*[A-Z]+[0-9a-zA-ZöäüÖÄÜ-]*( [IVX\d]+)*)/g;
      var regex = /(§|§§|[Aa][rr][Tt])\.? ?(\d+[a-z]?) ?([Aa][Bb][Ss]\.? ?(\d+[a-z]?))? ?.*?([A-ZÜÖÄ]{1}[\w-]*[A-ZÖÜÄ]{1}( [IVX\d]+)*)/g;
      var instance = new Mark(contentScript.webPart);
      var counter = 1;
      var nodeArray = [];
      instance.markRegExp(regex, {
        "element": "span",
        "className": "chrolawMark",
        // collection of quotes (node.innerText) as object in array (nodeArray)
        "each": function(node){
          var nodeObj = {'id': counter, 'markText': node.innerText}
          nodeArray.push(nodeObj);
          // giving each <span> element unique ID for later identification
          node.id = 'chrolawMark' + counter;
          counter++;
        }
      });
      // sinding nodeArray as message
      console.log("References:");
      console.log(nodeArray);
      contentScript.message("mafou", nodeArray)
    },

  // prototype function for sending messages (here: to background script)
  // https://developer.chrome.com/apps/runtime#method-sendMessage
  message: function(subject, content) {
    chrome.runtime.sendMessage({
      from:    'contentScript',
      subject: subject,
      content: content
    });
  },

  // creating webpage DOM element for sidebar
  // help from: https://www.w3schools.com/howto/howto_js_sidenav.asp
  sidebarInit: function() {
    // creating sidebar DOM element
    var sidebar = document.createElement('div');
    sidebar.id = "chrolawSidebar";

    // creating close button DOM element for sidebar (X)
    var closeBtn = document.createElement('div');
    closeBtn.id = ('chrolawSidebarCloseBtn');
    closeBtn.innerText = "X"
    // making close button clickable
    closeBtn.onclick = function(){contentScript.sidebarClose()};
    sidebar.appendChild(closeBtn);

    document.body.appendChild(sidebar);
  },

  // function for closing sidebar by changing css of DOM body and sidebar
  sidebarClose: function() {
    document.getElementById('chrolawSidebar').style.width = "0";
    document.body.style.marginRight = "0";
    contentScript.sidebar = false;
  },

  // function for opening sidebar
  sidebarOpen: function(id) {
    document.getElementById('chrolawSidebar').style.width = "250px";
    document.body.style.marginRight = "250px";
    // passing of quote ID so that quote fulltext opens in sidebar when clicking
    // highlighted quote
    if (id)
      contentScript.sidebarDrop(document.getElementById("chrolawSidebTitle" +
                                                                          id));
    contentScript.sidebar = true;
  },

  // creating content of sidebar
  sidebarCont: function(nodeArray) {
    var sidebContNode = document.createElement('div');
    sidebContNode.id = "chrolawSidebCont";

    nodeArray = contentScript.sort(nodeArray)

    // iterating through quotes Data and creaing each title and fulltext for
    // sidebar
    nodeArray.forEach(function(node, i) {
      // sidebShow is True when it is unique so that no duplicates are shown
      if (node.sidebShow) {

        // create sidebar Titles
        var nodeTitle = document.createElement('p');
        nodeTitle.id = "chrolawSidebTitle" + (node.id);
        // giving title element class identification
        nodeTitle.className = "chrolawSidebTitles";
        nodeTitle.innerText = node.markText;
        nodeTitle.onclick = function() {contentScript.sidebarDrop(this)};
        sidebContNode.appendChild(nodeTitle);

        // create each sidebar quote fulltext content
        var nodeInner = document.createElement('div');
        nodeInner.id = "chrolawSidebInner" + (node.id);
        nodeInner.className = "chrolawSidebInners";
        // adding each passage of fulltext to sidebar and giving each a <span>
        // element, so that the quoted one can be highlighted
        for (var abs in node.fullNorm) {
          var absHTML = document.createElement('span');
          absHTML.id = "chrolaw" + node.dictKey + "_" + abs;
          absHTML.innerHTML = node.fullNorm[abs];
          // node.abs is quoted passage
          if (abs === node.abs) {absHTML.style.color = "#bfac31"}
          // if abs is none then whole paragraph highlighted
          if (node.abs === null) {absHTML.style.color = "#bfac31"}
          nodeInner.appendChild(absHTML);
        }

        // if fulltext in sidebar is clicked, the source is opened in new tab or
        // window
        url = contentScript.findURL(node.markText, node.para, node.fURL);
        nodeInner.onclick = function(){window.open(url,'_blank')};

        sidebContNode.appendChild(nodeInner);
      }

      // highlighted quotes are beeing adjusted and made clickable
      // if fulltext was found or not
      // node.sidebLink is True when there is a matching sidebar entry
      if (node.sidebLink) {
        var chrolawMark = document.getElementById('chrolawMark' + node.id)
        chrolawMark.onclick = function(){
          contentScript.sidebarOpen(node.sidebDest);
        }
        chrolawMark.className = 'chrolawMarkGreen'
      } else {
        var chrolawMark = document.getElementById('chrolawMark' + node.id)
        chrolawMark.className = 'chrolawMarkRed'
      }
    });

    document.getElementById('chrolawSidebar').appendChild(sidebContNode);
  },

  // sorting algorithm for entrys in sidebar
  // https://stackoverflow.com/a/13820874
  sort: function(nodeArray) {
    function compare(a,b) {
     if (a.gesetz === b.gesetz) {
         if (a.para === b.para) {
             return (a.abs < b.abs) ? -1 : (a.abs > b.abs) ? 1 : 0;
         } else {
             return (a.para < b.para) ? -1 : 1;
         }
     } else {
          return (a.gesetz < b.gesetz) ? -1 : 1;
     }
   }
    return nodeArray.sort(compare);
  },

  // function for creating url path of quoted fulltext source
  findURL: function(markText, para, fURL) {
    if (markText.slice(0, 3).toLowerCase() === "art")
      var urlPart = "art_" + para
    else
      var urlPart = "__" + para
    var url =   "https://www.gesetze-im-internet.de/" +
                fURL + "/" + urlPart + ".html"

    return url
  },

  // executed when title in sidebar is clicked to show fulltext
  sidebarDrop: function(norm) {
    norm.classList.toggle("active");
    var panel = norm.nextElementSibling;
    if (panel.style.display === "block") {
        panel.style.display = "none";
    } else {
        panel.style.display = "block";
    }
  }


}

contentScript.listener();
contentScript.search();
contentScript.sidebarInit();
