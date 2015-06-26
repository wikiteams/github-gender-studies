# coding=UTF-8
'''
Puts information on gender estimation of GitHub users
into our GitHub Torrent MySQL mirror
@version 2.0 "Happy Days"
@author Oskar Jarczyk
@since 1.0
@update 25.06.2015
'''

from logger import scream
import sys
import gender_stacker as GetterJobs
from unique import NamesCollection
import time
import pkg_resources
try:
    import elementtree.ElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
try:
    import MySQLdb as MSQL
except ImportError:
    import _mysql as MSQL

version_name = 'version 2.0 codename: Happy Days'

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


def test_database(connection):
    print 'Pinging database: ' + (str(connection.ping(True)) if connection.ping(True) is not None else 'feature unavailable')
    cursor = connection.cursor()
    cursor.execute(r'SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = "%s"' % 'github')
    rows = cursor.fetchall()
    print 'There are: ' + str(rows[0][0]) + ' table objects in the local GHtorrent copy'
    return cursor


def check_database_consistency(cursor):
    cursor.execute(r'SELECT table_name FROM information_schema.tables WHERE table_schema = "%s"' % 'github')
    rows = cursor.fetchall()
    if (u'users', ) and (u'users_ext', ) in rows:
        print 'All neccesary tables are there.'
    else:
        print 'Your database does not fit a typical description of a GitHub Torrent copy..'
        print 'Program will exit now'
        sys.exit(0)


def execute_check():
    threads = []

    # Initialize connection to database #open('mysqlu.dat', 'r').read(),
    first_conn = MSQL.connect(host=IP_ADDRESS, port=3306, user=pkg_resources.resource_string('sources.gender_api', 'mysqlu.dat'),
                              passwd=pkg_resources.resource_string('sources.gender_api', 'mysqlp.dat'),
                              db="github", connect_timeout=5 * 10**7,
                              charset='utf8', init_command='SET NAMES UTF8',
                              use_unicode=True)
    print 'Testing MySql connection...'
    cursor = test_database(first_conn)
    check_database_consistency(cursor)

    sample_tb_name = raw_input("Please enter table/view name (where to get users from): ")
    cursor.execute(r'select count(distinct name) from ' + str(sample_tb_name) + ' where (type = "USR") and (name rlike "[a-zA-Z]+( [a-zA-Z]+)?")')
    rows = cursor.fetchall()
    record_count = rows[0][0]
    cursor.close()

    scream.say("Database seems to be working. Move on to getting list of users.")

    # populate list of users to memory
    cursor = first_conn.cursor()
    is_locked_tb = raw_input("Should I update [users_ext] table instead of [" + str(sample_tb_name) + "]? [y/n]: ")
    is_locked_tb = True if is_locked_tb in ['yes', 'y'] else False
    print 'Querying all names from the observations set.. This can take around 25-30 sec.'

    cursor.execute(r'select distinct name from ' + str(sample_tb_name) + ' where (type = "USR") and (name rlike "[a-zA-Z]+( [a-zA-Z]+)?")')
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
        print "[Progress]: " + str((iterator / record_count) * 100) + "% ----------- "
        if len(fullname) < min_name_length:
            scream.log_warning("--Found too short name field (" + str(fullname.encode('utf-8')) + ") from DB. Skipping..", True)
            row = cursor.fetchone()
            continue
        name = fullname.split()[0]
        # I find it quite uncommon to seperate name from surname with something else than a space
        # In some cultures first name comes after surname, but very often for the sake of westerners,
        # this is reversed-back (source: https://en.wikipedia.org/wiki/Surname#Order_of_names)
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
            scream.say("\t[Batch load] added new name: " + str(name.encode('utf-8')) + " as deriven from: " + str(fullname.encode('utf-8')))
            # start the worker when stack is full
            jobLoad = GetterJobs.stackWith(int(iterator), name)
            if jobLoad is not None:
                scream.say('Creating instance of [GeneralGetter] complete')
                scream.say('Appending thread to collection of threads')
                threads.append(jobLoad)
                scream.say('Append complete, threads[] now have size: ' + str(len(threads)))
                scream.log_debug('Starting thread ' + str(int(iterator)-1) + '....', True)
                jobLoad.start()
            while (num_working(threads) > 4):
                time.sleep(0.2)  # sleeping for 200 ms - there are already 4 active threads..
        row = cursor.fetchone()

    cursor.close()
    print "Finished getting gender data, moving to database update..."

    for key in names.keys():
        collection = names[key]
        for fullname in names[key]['persons']:
            cursor = first_conn.cursor()
            update_query = r'UPDATE {table} SET gender = {gender} , accuracy = {accuracy} where name = "{fullname}"'.format(
                           gender=collection['classification'],
                           fullname=fullname.encode('utf-8').replace('"', '\\"'),
                           table='users' if is_locked_tb else sample_tb_name,
                           accuracy=collection['accuracy'])
            print update_query
            cursor.execute(update_query)
            cursor.close()

    first_conn.close()
