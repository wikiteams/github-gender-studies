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
import logmissed
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
from bs4 import BeautifulSoup
import unicodedata
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="verbose messaging ? [True/False]", action="store_true")
    args = parser.parse_args()
    if args.verbose:
        scream.intelliTag_verbose = True
        scream.say("verbosity turned on")

    # init connection to database
    first_conn = MSQL.connect(host="10.4.4.3", port=3306, user=open('mysqlu.dat', 'r').read(),
                              passwd=open('mysqlp.dat', 'r').read(), db="github", connect_timeout=50000000)
    print 'Testing mySql connection...'
    print 'Pinging database: ' + (str(first_conn.ping(True)) if first_conn.ping(True) is not None else 'NaN')
    cursor = first_conn.cursor()
    cursor.execute(r'SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = "%s"' % 'github')
    rows = cursor.fetchall()
    print 'There are: ' + str(rows[0][0]) + ' table objects in the local GHtorrent copy'
    cursor.close()
    first_conn.close()
    scream.say("Database seems to be working. Move on to getting list of users.")

    # populate list of users to memory

    # start the workers