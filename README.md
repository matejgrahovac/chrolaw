# Chrolaw

An extension for Chrome that recognizes references to German laws or bills and displays the quotes in an injected sidebar.

When reading court decisions online, looking up references to bills or laws can become very annoying and time consuming. My project tackles this problem with a helpful extension for Chrome. It searches for references in web pages you visit, and looks them up in a dedicated database. The results are been displayed in an injected sidebar. This project seems simple, but involves important tools many modern web applications use today. JavaScript, HTML5 + CSS, regular expressions, Ajax, web scraping (Beautifulsoup 4), XML, Python3, Flask, Apache2, Ubuntu Server, SQL, ariaDB and some more... For a brief overview, check out my youtube video, or dive into my beautifully commented code.

https://youtu.be/op3U4b1GevU

## Testing

To test it yourself, download/fork the folder named "extension" from chrolaw.matejgrahovac.de, go to "manage extensions" in Chrome, enable developer mode and add the extension folder. Then, go to testchrolaw.matejgrahovac.de or any other web page with references to German bills. Please keep in mind, that the extension's pattern matching isn't perfect, yet.
