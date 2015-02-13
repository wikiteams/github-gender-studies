# coding=UTF-8
'''
Puts information on gender estimation of GitHub users
into our GitHub Torrent MySQL mirror
@version 1.3
@author Oskar Jarczyk
@since 1.0
@update 12.02.2015
'''

import csv
import scream
import codecs
import cStringIO
import os
import sys
import urllib
import urllib2
import simplejson
import hashlib
import mechanize
import time
import argparse
from bs4 import BeautifulSoup
import re
import unicodedata
import threading
# import ElementTree based on the python version
try:
    import elementtree.ElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
try:
    import MySQLdb as MSQL
except ImportError:
    import _mysql as MSQL

version_name = 'version 1.3 codename: Dżęder'

MALE = 1
FEMALE = 2
UNISEX = 3
UNKNOWN = 99

record_count = 37248

"""
The MIT License (MIT)

Copyright (c) 2015 WikiTeams.pl

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

names = dict()


def is_win():
    return sys.platform.startswith('win')


def all_finished(threads):
    are_finished = True
    for thread in threads:
        if not thread.is_finished():
            return False
    return are_finished


def num_working(threads):
    are_working = 0
    for thread in threads:
        if not thread.is_finished():
            are_working += 1
        else:
            thread.cleanup()
    return are_working


class GeneralGetter(threading.Thread):

    finished = False
    name = None

    def __init__(self, threadId, name):
        scream.say('Initiating GeneralGetter, running __init__ procedure.')
        self.threadId = threadId
        threading.Thread.__init__(self)
        self.daemon = True
        self.finished = False
        self.name = name

    def run(self):
        scream.cout('GeneralGetter thread(' + str(self.threadId) + ')' + 'starts working on name ' + str(self.name))
        self.finished = False
        self.get_data(self.name)

    def is_finished(self):
        return self.finished if self.finished is not None else False

    def set_finished(self, finished):
        scream.say('Marking the thread ' + str(self.threadId) + ' as finished..')
        self.finished = finished

    def cleanup(self):
        scream.say('Marking thread on ' + str(self.threadId) + "/" + str(self.name) + ' as definitly finished..')
        self.finished = True
        scream.say('Terminating/join() thread on ' + str(self.threadId) + ' ...')
        #self.join()

    def get_data(self, name):
        
        self.set_finished(True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="verbose messaging ? [True/False]", action="store_true")
    args = parser.parse_args()
    if args.verbose:
        scream.intelliTag_verbose = True
        scream.say("verbosity turned on")

    threads = []

    # init connection to database
    first_conn = MSQL.connect(host="10.4.4.3", port=3306, user=open('mysqlu.dat', 'r').read(),
                              passwd=open('mysqlp.dat', 'r').read(), db="github", connect_timeout=50000000,
                              charset='utf8', init_command='SET NAMES UTF8', use_unicode=True)
    print 'Testing mySql connection...'
    print 'Pinging database: ' + (str(first_conn.ping(True)) if first_conn.ping(True) is not None else 'NaN')
    cursor = first_conn.cursor()
    cursor.execute(r'SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = "%s"' % 'github')
    rows = cursor.fetchall()
    print 'There are: ' + str(rows[0][0]) + ' table objects in the local GHtorrent copy'
    cursor.close()
    scream.say("Database seems to be working. Move on to getting list of users.")

    # populate list of users to memory
    cursor = first_conn.cursor()
    print 'Querying all names from the observations set.. This can take around 25-30 sec.'
    cursor.execute(r'select distinct name from selected_developers_merged where name is not NULL')
    # if you are interested in how this table was created, you will probably need to read our paper and contact us as well
    # because we have some more tables with aggregated data compared to standard GitHub Torrent collection
    row = cursor.fetchone()
    iterator = float(0)

    while row is not None:
        fullname = unicode(row[0])
        scream.log("  Fullname is: " + str(fullname.encode('unicode_escape')))
        iterator += 1.0
        print "[Progress]: " + str( (iterator / record_count) * 100 ) + "% -----------"
        if len(fullname) < 2:
            scream.log_warning("--Found too short name field from DB. Skipping..", True)
            row = cursor.fetchone()
            continue
        name = fullname.split()[0]
        # name = re.split('\s|,|.', fullname)[0]
        scream.log("  Name is: " + str(name.encode('unicode_escape')))
        if name in names:
            if fullname in names[name]['persons']:
                scream.say("  Such fullname already classified! Rare, but can happen. Move on.")
            else:
                scream.say("  Adding fullname to ALREADY classified name. Move on")
                names[name]['persons'].append(fullname)
        else:
            scream.say("  New name. Lets start classification.")
            names[name] = {'persons': list(), 'classification': None}
            names[name]['persons'].append(fullname)
            scream.say("  Start the worker on name: " + str(name.encode('utf-8')) + " as deriven from: " + str(fullname.encode('utf-8')))
            # start the worker
            gg = GeneralGetter(int(iterator), name)
            scream.say('Creating instance of GeneralGetter complete')
            scream.say('Appending thread to collection of threads')
            threads.append(gg)
            scream.say('Append complete, threads[] now have size: ' + str(len(threads)))
            scream.log_debug('Starting thread ' + str(int(iterator)-1) + '....', True)
            gg.start()
            while (num_working(threads) > 3):
                time.sleep(0.2)  # sleeping for 200 ms - there are already 3 active threads..
        row = cursor.fetchone()
    first_conn.close()
