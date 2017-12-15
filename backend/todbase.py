#!/usr/bin/python3
#
# Chrome Extension with Database Backend (chrolaw), project by Matej Grahovac
# www.matejgrahovac.de
#
# An extension for Chrome, that recognizes references to German laws or bills
# and displays the quotes in an injected sidebar.
#
# this script takes all *.xml files in laws/, creates a table for each law,
# excerpts each paragraph and writes them into the table


from lxml import etree # for using xpath on *.xml files
import os # for getting all the *.xml files from laws/
# python MySQL client https://github.com/PyMySQL/PyMySQL
import pymysql.cursors

class main(object):

    # storing table rows according to max number of passages
    max_length = 1

    # connection to database
    def db_connect():
        main.connection = pymysql.connect(host=input('Database host:'),
                                          user=input('Database user:'),
                                          password=input('Database password:'),
                                          db=input('Database:'),
                                          cursorclass=pymysql.cursors.DictCursor)


    # closing connection to database
    def db_close():
        main.connection.close()

    # get max table rows according to max number of passages
    def table_length(length):
        if length > main.max_length:
            main.max_length = length

    # reading *.xml and returning list of paragraphs
    def getit(pathtoxml):
        # parsing *.xml file
        tree = etree.parse(pathtoxml)
        root = tree.getroot()
        lawlist = []
        # filtering paragraphs out of *.xml files and handling some exceptions
        # more info on xpath syntax https://www.w3schools.com/xml/xpath_examples.asp
        for child in root.xpath('norm[contains(@doknr,"BJNE")]/metadaten/enbez[contains(text(),"Art ") or contains(text(), "§ ")]'):
            para = {}
            # paragraphs start with §, articles with Art.
            if child.text[:3] == 'Art':
                para['0'] = child.text[4:]
            else:
                para['0'] = child.text[2:]
            if child.xpath('../titel/text()') == ['(weggefallen)']:
                para['1'] = '(weggefallen)'
                para['0'] = child.text
            else:
                # getting max number of paragraphs and storing each in list
                content = child.xpath('../../textdaten//Content[1]/P[not(FnR)]')
                main.table_length(len(content))
                for i, child0 in enumerate(content):
                    string_para = str(etree.tostring(child0))
                    para[str(i + 1)] = string_para[2:-1]
            lawlist.append(para)
        return lawlist

    # crating sql command to create table relative to max table rows
    # e.g.:
    # CREATE TABLE `BJNR513400953` (`para` varchar(20) NOT NULL,`1`)
    # ENGINE=InnoDB ROW_FORMAT=COMPRESSED KEY_BLOCK_SIZE=8
    def sqltable_creator(law, abscount):
        sql  = ("CREATE TABLE `{}` (".format(law))
        sql += "`para` varchar(50) NOT NULL,"
        for i in range(abscount):
            if i + 1 == abscount:
                sql += ("`{}` longtext NOT NULL".format(i + 1))
            else:
                sql += ("`{}` longtext NOT NULL,".format(i + 1))
        # ROW_FORMAT=COMPRESSED KEY_BLOCK_SIZE=8 added because of error
        # https://stackoverflow.com/a/15585700
        sql += ") ENGINE=InnoDB ROW_FORMAT=COMPRESSED KEY_BLOCK_SIZE=8"
        return sql

    # creating sql command to insert paragraphs into table
    # INSERT INTO `BJNR101900996` (`para`, `1`, `2`, `3`, `4`, `5`)
    # VALUES (%(0)s, %(1)s, '', '', '', '')
    def sqltable_insert(tablename, tablelength, paralength):
        sql  = ("INSERT INTO `{}` (`para`, ".format(tablename))
        for i in range(tablelength):
            sql += "`{}`".format(i + 1)
            if(i + 1 == tablelength):
                sql += ") VALUES ("
            else:
                sql += ", "
        for i in range(tablelength + 1):
            if(i + 1 <= paralength):
                # for insertion of dict by key (’0’, ’1’, ’2’, ’3’ ,...)
                sql += ("%({})s".format(i))
            else:
                sql += "''"
            if(i == tablelength):
                sql += ")"
            else:
                sql += ", "
        return sql

    # execution of sql command
    # https://stackoverflow.com/a/41538711
    def sql_exec(sql, para, message):
        try:
            with main.connection.cursor() as cursor:
                # print("Writing {}".format(message))
                if para == "-":
                    cursor.execute(sql)
                else:
                    cursor.execute(sql, para)
                main.connection.commit()
        # except mariadb.Error as err:
        except pymysql.err.InternalError as e:
            code, msg = e.args
            print("-------------------")
            print("Error in sql execution:")
            print(code)
            print(message)
            print(msg)
            print("-------------------")

    # iterating through lawlist sending to sql_exec function
    def lawiter(filename, pathtoxml, counter):
        lawlist = main.getit(pathtoxml)
        tablelength = main.max_length
        # remove ".xml" for table name
        tablename = filename[:-4]
        # creating sql command for creating table
        sql = main.sqltable_creator(tablename, tablelength)
        # executing sql command
        main.sql_exec(sql, "-", pathtoxml)
        print("-------------------")
        print("Nr. {}, Table {} created.".format(counter, tablename))
        for para in lawlist:
            # creating sql command for inserting into table
            sql = main.sqltable_insert(tablename, tablelength, len(para))
            # executing sql command
            main.sql_exec(sql, para, "{} {}".format(para['0'], tablename))
            main.max_length = 0
        print("paragraphs inserted")

    # finding all *.xml files in laws/ and sending to lawiter function
    def allxml():
        main.db_connect()
        counter = 1
        for root, dirs, files in os.walk('laws/'):
            for file1 in files:
                if file1.endswith(".xml"):
                    filename = file1
                    pathtoxml = "{}/{}".format(root, filename)
                    main.lawiter(filename, pathtoxml, counter)
                    main.max_length = 1
                    counter += 1
        main.db_close()


main.allxml()
