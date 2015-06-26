# coding=UTF-8
'''
Puts information on gender estimation of GitHub users
into our GitHub Torrent MySQL mirror
@version 1.4 "Angry Dairyman"
@author Oskar Jarczyk
@since 1.0
@update 4.04.2015
'''

import scream
import sys
from gender_first_getter import GeneralGetter
from unique import NamesCollection
import time
import argparse
# import ElementTree based on the python version
try:
    import elementtree.ElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
try:
    import MySQLdb as MSQL
except ImportError:
    import _mysql as MSQL

version_name = 'version 1.4 codename: Angry Dairyman'

record_count = None
IP_ADDRESS = "10.4.4.3"  # Be sure to update this to your needs


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

names = NamesCollection.names


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


def execute_check():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="verbose messaging ? [True/False]", action="store_true")
    args = parser.parse_args()
    if args.verbose:
        scream.intelliTag_verbose = True
        scream.say("verbosity turned on")

    threads = []

    # init connection to database
    first_conn = MSQL.connect(host=IP_ADDRESS, port=3306, user=open('mysqlu.dat', 'r').read(),
                              passwd=open('mysqlp.dat', 'r').read(),
                              db="github", connect_timeout=50000000,
                              charset='utf8', init_command='SET NAMES UTF8',
                              use_unicode=True)
    print 'Testing MySql connection...'
    print 'Pinging database: ' + (str(first_conn.ping(True)) if first_conn.ping(True) is not None else 'NaN')
    cursor = first_conn.cursor()
    cursor.execute(r'SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = "%s"' % 'github')
    rows = cursor.fetchall()
    print 'There are: ' + str(rows[0][0]) + ' table objects in the local GHtorrent copy'
    cursor.execute(r'SELECT table_name FROM information_schema.tables WHERE table_schema = "%s"' % 'github')
    rows = cursor.fetchall()
    if (u'users', ) and (u'projects', ) in rows:
        print 'All neccesary tables are there.'
    else:
        print 'Your database does not fit a typical description of a GitHub Torrent copy..'
        sys.exit(0)

    sample_tb_name = raw_input("Please enter table/view name (of chosen data sample): ")
    cursor.execute(r'select count(distinct name) from ' + str(sample_tb_name) + ' where ((name is not NULL) and (gender is NULL))')
    rows = cursor.fetchall()
    record_count = rows[0][0]
    cursor.close()

    scream.say("Database seems to be working. Move on to getting list of users.")

    # populate list of users to memory
    cursor = first_conn.cursor()
    is_locked_tb = raw_input("Should I update [users] table instead of [" + str(sample_tb_name) + "]? [y/n]: ")
    is_locked_tb = True if is_locked_tb in ['yes', 'y'] else False
    print 'Querying all names from the observations set.. This can take around 25-30 sec.'

    cursor.execute(r'select distinct name from ' + str(sample_tb_name) + ' where ((name is not NULL) and (gender is NULL))')
    # if you are interested in how this table was created, you will probably need to read our paper and contact us as well
    # because we have some more tables with aggregated data compared to standard GitHub Torrent collection
    row = cursor.fetchone()
    iterator = 1.0

    min_name_length = 2
    print 'We hypothetize that minimum name length are ' \
        + str(min_name_length) + ' characters, like Ho, Sy, Lu'
    # http://www.answers.com/Q/What_is_the_shortest_name_in_the_world

    while row is not None:
        fullname = unicode(row[0])
        scream.log("\tFullname is: " + str(fullname.encode('unicode_escape')))
        iterator += 1
        print "[Progress]: " + str((iterator / record_count) * 100) + "% ----------- "  # [names] size: " + str(len(names))
        if len(fullname) < min_name_length:
            scream.log_warning("--Found too short name field (" + str(fullname.encode('utf-8')) + ") from DB. Skipping..", True)
            row = cursor.fetchone()
            continue
        name = fullname.split()[0]
        # I find it quite uncommon to seperate name from surname with something else than a space
        # it does occur, but it's not in my interest to detect such human-generated dirty data at the moment
        scream.log("\tName is: " + str(name.encode('unicode_escape')))
        if name in names:
            if fullname in names[name]['persons']:
                scream.say("\tSuch fullname already classified! Rare, but can happen. Move on.")
            else:
                scream.say("\tAdding fullname to already classified name. Move on")
                names[name]['persons'].append(fullname)
        else:
            scream.say("\tNew name. Lets start classification.")
            names[name] = {'persons': list(), 'classification': None}
            names[name]['persons'].append(fullname)
            scream.say("\tStart the worker on name: " + str(name.encode('utf-8')) + " as deriven from: " + str(fullname.encode('utf-8')))
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
            update_query = r'UPDATE {2} SET gender = {0} where name = "{1}"'.format(gender,
                fullname.encode('utf-8').replace('"', '\\"'), 'users' if is_locked_tb else sample_tb_name)
            print update_query
            cursor.execute(update_query)
            cursor.close()

    first_conn.close()
