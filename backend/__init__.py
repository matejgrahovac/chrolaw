#!/usr/bin/python3
#
# Chrome Extension with Database Backend (chrolaw), project by Matej Grahovac
# www.matejgrahovac.de
#
# An extension for Chrome, that recognizes references to German laws or bills
# and displays the quotes in an injected sidebar.
#
# this is the backend application which searches for matches in the mariaDB
# database and sends them back to the extensions background script
# this web app runs on flask
# http://flask.pocoo.org/
# and is serverd by wsgi
# http://modwsgi.readthedocs.io/en/develop/
# to an apache2 webserver.
# flask and python is installed in a virtual environment
# https://docs.python.org/3/tutorial/venv.html

import json
from flask import Flask, render_template, jsonify, request
import re

# setting path for pymysql.cursors module
import sys
#sys.path.insert(0,"/var/www/flaskApps/chrolaw/venv/lib/python3.5/site-packages")
import pymysql.cursors

app = Flask(__name__)

class helpers(object):

    # connectoin to mariaDB database https://github.com/PyMySQL/PyMySQL
    def dbconnect():
        # helpers.connection = pymysql.connect(   host='localhost',
        #                                         user='xxxxx',
        #                                         password='xxxxx',
        #                                         db='Gesetze',
        #                                         cursorclass=pymysql.cursors.DictCursor)



    # closing connection to database
    def dbclose():
        helpers.connection.close()

    # execution of SQL command to search for fulltext in database
    def sqlexec(BJNR, norm):
        try:
            with helpers.connection.cursor() as cursor:
                sql = "SELECT * FROM `{}` WHERE para = '{}'".format(BJNR, norm)
                cursor.execute(sql)
                helpers.connection.commit()
                data = cursor.fetchall()
                data = data[0]
                tmp = {}
                # creating objext for passages in paragraph
                for dat in data:
                    if not (dat == "para" or data[dat] == ""):
                        tmp[dat] = data[dat]
                data = tmp;
        except:
            pass
        return(data)

    # serching for database table name and url short of law in data/*.json file
    # (StGB = BJNR001270871 and stgb)
    def findBJNRfURL(gesetz):
        firstletter = gesetz[0]
        #with open("/var/www/flaskApps/chrolaw/data/{}.json".format(firstletter.upper())) as json_file:
        with open("data/{}.json".format(firstletter.upper())) as json_file:
            data = json.load(json_file)
        BJNRfURL = {}
        try:
            BJNRfURL['BJNR'] = data[gesetz][3]
            BJNRfURL['fURL'] = data[gesetz][1]
        except:
            BJNRfURL['BJNR'] = False;
            BJNRfURL['fURL'] = False;
        return BJNRfURL

# script to be executed when called by extension backend script
@app.route('/receivejson', methods=['POST'])
def receivejson():

    app.logger.debug("JSON received...")
    # storing received json in new list
    nodeList = request.get_json()
    nodesDict = {}
    sidebLinkList = []
    # regulat expression to be used later
    # absatz : [Aa][Bb][Ss]\.? ?(\d+[a-z]?)
    # (§|§§|[Aa][rr][Tt])\.? ?(\d+[a-z]?) [Aa][Bb][Ss]\.? ?(\d+[a-z]?)

    regex = re.compile('(§|§§|[Aa][rr][Tt])\.? ?(\d+[a-z]?)? ?([Aa][Bb][Ss]\.? ?(\d+[a-z]?))? ?.*?([A-ZÜÖÄ]{1}[\w-]*[A-ZÖÜÄ]{1}( [IVX\d]+)*)')
    # regex = re.compile('(§§?|[aA][Rr][Tt]\.?) ?(\d+[a-z]?) ?([aA][Bb][Ss][.]? ?(\d*)|([iIvVxX]*))? ?.*?([0-9A-Z-]+[0-9a-zA-ZöäüÖÄÜ-]*[A-Z]+[0-9a-zA-ZöäüÖÄÜ-]*( [IVX\d]+)*)')
    helpers.dbconnect()
    for node in nodeList:
        # using regex to split matches into its parts
        # (§ 14a Abs. 3 BGB -> 14a, 3, BGB)
        m = regex.match(node['markText'])
        node['para'] = m.group(2)
        node['gesetz'] = m.group(5)

        # there's no group 4 when whole paragraph is quoted
        try:
            node['abs'] = m.group(4)
        except:
            node['abs'] = ''


        # formatting match to look consistent in sidebar
        # https://stackoverflow.com/a/2400577
        markRep =   {
                        'Abs ':'Abs. ', 'abs ':'Abs. ', 'Art ':'Art. ', 'art ':'Art. ',
                        'S':'Satz', 's':'Satz'
                    }
        pattern = re.compile(r'\b(' + '|'.join(markRep.keys()) + r')\b')
        node['markText'] = pattern.sub(lambda x: markRep[x.group()], node['markText'])

        # changing law names to be found in data/*.json
        # e.g. SGB VII to SGB 5
        romans =    {
                        'I':'1', 'II':'2', 'III':'3', 'IV':'4',
                        'V':'5', 'VI':'6', 'VII':'7', 'VIII':'8',
                        'IX':'6', 'X':'10', 'XI':'11', 'XII':'12'
                    }
        pattern = re.compile(r'\b(' + '|'.join(romans.keys()) + r')\b')
        node['gesetz'] = pattern.sub(lambda x: romans[x.group()], node['gesetz'])

        # constructing key so that double matches can be identified
        dictKey = str(node['para']) + '_' + str(node['abs']) + '_' + str(node['gesetz'])
        node['dictKey'] = dictKey

        # creating logical value if match needs to be shown in sidebar
        node['sidebLink'] = True

        # using object keys to identify duplicate matches
        try:
            node['sidebDest'] = nodesDict[dictKey]
            node['sidebShow'] = False
            continue
        except:
            nodesDict[dictKey] = node['id']
            node['sidebDest'] = node['id']

        tmp = helpers.findBJNRfURL(node['gesetz'])
        node['BJNR'] = tmp['BJNR']
        node['fURL'] = tmp['fURL']

        # not show match if BJNR not found and using sidebLinkList that it can
        # be applied to duplicates, later
        if not node['BJNR']:
            node['sidebShow'] = False
            node['sidebLink'] = False
            sidebLinkList.append(dictKey)

        # searching databse for fulltext of match and handling exceptions
        try:
            node['fullNorm'] = helpers.sqlexec(node['BJNR'], node['para'])
            node['sidebShow'] = True
            if node['fullNorm'] == () or [] or "":
                node['sidebShow'] = False
                node['sidebLink'] = False
                sidebLinkList.append(dictKey)
        except:
            node['sidebShow'] = False
            node['sidebLink'] = False
            sidebLinkList.append(dictKey)

    # apply exceptions to all duplicate matches
    for node in nodeList:
        if node['dictKey'] in sidebLinkList:
            node['sidebLink'] = False

    # close connection to database
    helpers.dbclose()
    return jsonify(nodeList)


if __name__ == "__main__":
    app.run()
