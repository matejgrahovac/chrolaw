#!/usr/bin/python3
#
# Chrome Extension with Database Backend (chrolaw), project by Matej Grahovac
# www.matejgrahovac.de
#
# An extension for Chrome, that recognizes references to German laws or bills
# and displays the quotes in an injected sidebar.
#
# this script takes the *.json files in data/, and downlaods the *.zip file and
# extracts the *.xml file for each law

import os # for common pathname manipulations, here to create paths
import io # core tools for working with streams, here to create zipfile from
# downloaded content
import json # working with json files
import shutil # High-level file operations, here to remove *.zip file

import requests # library for opening urls, here to downlaod files
import zipfile # wirking with zip archives, here for unzipping

# downloading each law and checking for errors
def download(laws):
    urlbase = 'https://www.gesetze-im-internet.de'
    path = 'laws/'
    total = float(len(laws))
    print("Laws to download: {}".format(len(laws)))
    for i, law in enumerate(laws):
        print("-----------------")
        print('Nr. {}, Law: {}'.format(i, law))
        url = '{}/{}/xml.zip'.format(urlbase, law)
        # downlad zip file data
        zipdata = requests.get(url)
        print('download complete')
        try:
            # create zip file from downloaded data
            zipf = zipfile.ZipFile(io.BytesIO(zipdata.content))
            # create path to unzip
            law_path = os.path.join(path, law[0], law)
            # remove old zip file data from previous download
            shutil.rmtree(law_path, ignore_errors=True)
            # create new law path
            os.makedirs(law_path)
            # extract all files in zipfile
            for name in zipf.namelist():
                zipf.extract(name, law_path)
            print('zipfile extracted')
        # informing user if bad zip file
        except zipfile.BadZipfile:
            print("{} is bad zip file".format(law))

# open all data/*.json files and send all laws to download function
folder_names = "ABCDEFGHIJKLMNOPQRSTUVWYZ123456789"
all = []
for folder in folder_names:
    with open("data/{}.json".format(folder)) as json_file:
        data = json.load(json_file)
    for dat in data:
        all.append(data[dat][1])

download(all)
