#!/usr/bin/python3
#
# Chrome Extension with Database Backend (chrolaw), project by Matej Grahovac
# www.matejgrahovac.de
#
# An extension for Chrome, that recognizes references to German laws or bills
# and displays the quotes in an injected sidebar.
#
# this script crawls these sites https://www.gesetze-im-internet.de/aktuell.html
# to get the necessary information on each law and store them in data/*.json

from urllib.request import urlopen # to open and download webpages
from bs4 import BeautifulSoup as soup # access to webpage DOM
import json # create json files

master_url = "https://www.gesetze-im-internet.de/Teilliste_{}.html"
chars = "ABCDEFGHIJKLMNOPQRSTUVWYZ123456789" # no laws with X
counter = 1;

for char in chars:
    data = {}
    print("Downloading all laws beginning with {}:".format(char))

    client = urlopen(master_url.format(char))
    html = client.read()
    client.close()
    # parse downladed html
    html = soup(html, "html.parser")
    # select all <p> elements in div id paddingLR12
    linklist = html.select("#paddingLR12")[0].select("p")

    # creating dict of lists for each site
    for link in linklist:
        url = link.a["href"][2:-11]
        titel = link.a.abbr['title']
        gesetz = link.a.text[1:-1]

        # going one link deeper to get BJNR info
        # because xml files are named by their BJNR
        client = urlopen("https://www.gesetze-im-internet.de/{}/index.html".format(url))
        html_0 = client.read()
        client.close()
        html_0 = soup(html_0, "html.parser")
        BJNR = html_0.h2.a['href'][:-5]

        data[gesetz] = [counter, url, titel, BJNR]

        # printing some info on each law on screen
        print("Nr. " + str(counter))
        print("Gesetz: {}".format(gesetz))
        print("Url: https://www.gesetze-im-internet.de/{}/index.html".format(url))
        print("Titel: {}".format(titel))
        print("BJNR: {}".format(BJNR))
        print("---------------------------")

        counter += 1

    # storing dict as json file
    with open("data/{}.json".format(char), 'w') as jasonfile:
        json.dump(data, jasonfile)
