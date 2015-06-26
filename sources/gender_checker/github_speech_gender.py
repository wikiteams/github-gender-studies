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

version_name = 'version 1.4 codename: Bayes'

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

latin_letters = {}
symbols = (u"абвгдеёзийклмнопрстуфхъыьэАБВГДЕЁЗИЙКЛМНОПРСТУФХЪЫЬЭ",
           u"abvgdeezijklmnoprstufh'y'eABVGDEEZIJKLMNOPRSTUFH'Y'E")
#tr = {ord(a): ord(b) for a, b in zip(*symbols)}
tr = dict()
#moving to python 2.7.3
for a in zip(*symbols):
    for b in zip(*symbols):
        tr.update({ord(a[0]): ord(b[1])})


def cyrillic2latin(input):
    return input.translate(tr)


def is_latin(uchr):
    try:
        return latin_letters[uchr]
    except KeyError:
        return latin_letters.setdefault(uchr,
                                        'LATIN' in unicodedata.name(uchr))


def only_roman_chars(unistr):
    return all(is_latin(uchr)
               for uchr in unistr
               if uchr.isalpha())  # isalpha suggested by John Machin


def StripNonAlpha(s):
    return "".join(c for c in s if c.isalpha())


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
    browser = None

    def __init__(self, threadId, name):
        scream.say('Initiating GeneralGetter, running __init__ procedure.')
        self.threadId = threadId
        threading.Thread.__init__(self)
        self.daemon = True
        self.finished = False
        self.name = name

        #initialize browser the ultimate hacking and web-scrappig TARDIS
        self.my_browser = mechanize.Browser()
        #my_browser.set_all_readonly(False)    # allow everything to be written to
        self.my_browser.set_handle_robots(False)   # ignore robots
        self.my_browser.set_handle_refresh(False)  # can sometimes hang without this
        #end

    def run(self):
        scream.cout('GeneralGetter thread(' + str(self.threadId) + ')' + 'starts working on name ' + str(self.name.encode('utf-8')))
        self.finished = False
        self.get_data(self.name)

    def is_finished(self):
        return self.finished if self.finished is not None else False

    def set_finished(self, finished):
        scream.say('Marking the thread ' + str(self.threadId) + ' as finished..')
        self.finished = finished

    def cleanup(self):
        scream.say('Marking thread on ' + str(self.threadId) + "/" + str(self.name.encode('utf-8')) + ' as definitly finished..')
        self.finished = True
        scream.say('Terminating/join() thread on ' + str(self.threadId) + ' ...')
        self.my_browser.close()

    def get_data(self, first_name):
        global names
        global UNKNOWN
        global MALE
        global FEMALE
        global UNISEX

        scream.say('#ask now internet for gender')
        while True:
            try:
                self.response = self.my_browser.open('http://genderchecker.com/')
                self.response.read()
                break
            except urllib2.URLError:
                scream.ssay('Site genderchecker.com seems to be down' +
                            '. awaiting for 60s before retry')
                time.sleep(60)
        scream.say('Response read. Mechanize selecting form.')
        self.my_browser.select_form("aspnetForm")
        self.my_browser.form.set_all_readonly(False)
        # allow everything to be written

        self.control = self.my_browser.form.find_control("ctl00$TextBoxName")
        if only_roman_chars(first_name):
            self.control.value = StripNonAlpha(first_name.encode('utf-8'))
        else:
            self.control.value = StripNonAlpha(cyrillic2latin(first_name).encode('utf-8'))
        #check if value is enough
        #control.text = first_name
        scream.say('Control value is set to :' + str(self.control.value))
        self.submit_retry_counter = 4
        while True:
            try:
                self.response = self.my_browser.submit()
                self.html = self.response.read()
                break
            except mechanize.HTTPError, e:
                self.submit_retry_counter -= 1
                if self.submit_retry_counter < 1:
                    raise StopIteration
                self.error_message = 'Site genderchecker.com seems to have ' +\
                                     'internal problems. or my request is' +\
                                     ' wibbly-wobbly nonsense. HTTPError ' +\
                                     str(e.code) +\
                                     '. awaiting for 60s before retry'
                scream.say(self.error_message)
                scream.log_error(str(e.code) + ': ' + self.error_message)
                time.sleep(60)
            except:
                self.submit_retry_counter -= 1
                if self.submit_retry_counter < 1:
                    raise StopIteration
                self.error_message = 'Site genderchecker.com seems to have ' +\
                                     'internal problems. or my request is' +\
                                     ' wibbly-wobbly nonsense. ' +\
                                     'awaiting for 60s before retry'
                scream.say(self.error_message)
                scream.log_error(self.error_message)
                time.sleep(60)
        self.local_soup = BeautifulSoup(self.html)
        self.failed = self.local_soup.find("span",
                                           {"id":
                                           "ctl00_ContentPlaceHolder1_" +
                                           "LabelFailedSearchedFor"})
        if self.failed is not None:
            scream.say("Name not found in the gender database")
            names[first_name]['classification'] = UNKNOWN
        self.gender_tag = self.local_soup.find("span",
                                               {"id":
                                               "ctl00_ContentPlaceHolder1_" +
                                               "LabelGenderFound"})
        if ((self.gender_tag is not None) and (self.gender_tag.contents is not None) and (len(self.gender_tag.contents) > 0)):
            self.gender = self.gender_tag.contents[0].string
            scream.say(self.gender)
            if self.gender.lower() == 'male':
                names[first_name]['classification'] = MALE
            elif self.gender.lower() == 'female':
                names[first_name]['classification'] = FEMALE
            elif self.gender.lower() == 'unisex':
                names[first_name]['classification'] = UNISEX
        else:
            scream.log_warning('Something really wrong, on result page there ' +
                               'was no not-found label neither a proper result', True)
            names[first_name]['classification'] = UNKNOWN
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
    #cursor.execute(r'select distinct name from selected_developers_merged where (name is not NULL) and ( (gender not in (1, 2, 3) or (gender is NULL) ) )')
    cursor.execute(r'select * from github_discussions oder by login desc')
    # if you are interested in how this table was created, you will probably need to read our paper and contact us as well
    # because we have some more tables with aggregated data compared to standard GitHub Torrent collection
    row = cursor.fetchone()
    iterator = float(0)

    while row is not None:
        fullname = unicode(row[0])
        scream.log("  Fullname is: " + str(fullname.encode('unicode_escape')))
        iterator += 1.0
        print "[Progress]: " + str((iterator / record_count) * 100) + "% -----------"
        if len(fullname) < 2:
            scream.log_warning("--Found too short name field (" + str(fullname.encode('utf-8')) + ") from DB. Skipping..", True)
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

    cursor.close()
    print "Finished getting gender data, moving to database update..."

    for key in names.keys():
        collection = names[key]
        gender = collection['classification']
        for fullname in names[key]['persons']:
            cursor = first_conn.cursor()
            update_query = r'UPDATE selected_developers_merged SET gender = {0} where name = "{1}"'.format(gender,
                                                                                                           fullname.encode('utf-8').replace('"', '\\"'))
            print update_query
            cursor.execute(update_query)
            cursor.close()

    first_conn.close()
