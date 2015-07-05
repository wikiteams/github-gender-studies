# coding=UTF-8
'''
Puts information on gender estimation of GitHub users
into our GitHub Torrent MySQL mirror
@version 2.0 "Happy Days"
@author Oskar Jarczyk
@since 1.0
@update 25.06.2015
'''

import sys
from logger.scream import say, definitely_say, log, log_warning, log_debug
from gender_getter import GeneralGetter
from unique import NamesCollection
import string_utils as StringUtil
import location_utils as LocationUtils
import database_factory as DatabaseFactory
import time
try:
    import elementtree.ElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


version_name = 'version 2.0 codename: Happy Days'


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


def execute_check(limit):
    threads = []

    # Initialize connection to database #open('mysqlu.dat', 'r').read(),
    connection = DatabaseFactory.init()
    definitely_say('Testing MySql connection...')
    cursor = DatabaseFactory.test_database(connection)
    DatabaseFactory.check_database_consistency(cursor)

    sample_tb_name = raw_input("Please enter table/view name (where to get users from): ")
    record_count = DatabaseFactory.get_record_count(cursor, sample_tb_name, limit)
    cursor.close()

    definitely_say("Database seems to be working. Move on to getting list of users.")

    # populate list of users to memory
    cursor = connection.cursor()
    is_locked_tb = raw_input("Should I update [users_ext] table instead of [" + str(sample_tb_name) + "]? [y/n]: ")
    is_locked_tb = True if is_locked_tb in ['yes', 'y'] else False
    definitely_say('Querying all names from the observations set.. This can take around 25-30 sec in LAN.')

    cursor.execute(r'select name, location from ' + str(sample_tb_name)
                   + ' where (type = "USR") and (name rlike "[a-zA-Z]+( [a-zA-Z]+)?"){optional}'.format(optional=" limit 500" if limit else ""))
    # if you are interested in how this table was created, you will probably need to read our paper and contact us as well
    # because we have some more tables with aggregated data compared to standard GitHub Torrent collection
    row = cursor.fetchone()
    iterator = 1.0

    min_name_length = 2
    say('We hypothetize that minimum name length are '
        + str(min_name_length) + ' characters, like Ho, Sy, Lu')
    # http://www.answers.com/Q/What_is_the_shortest_name_in_the_world

    while row is not None:
        fullname, location = unicode(row[0]), unicode(row[1])
        log("\tFullname is: " + str(fullname.encode('unicode_escape')))
        iterator += 1
        say("[Progress]: " + str((iterator / record_count) * 100) + "% ----------- ")

        if len(fullname) < min_name_length:
            log_warning("--Found too short name field (" + str(fullname.encode('utf-8')) + ") from DB. Skipping..", True)
            row = cursor.fetchone()
            continue

        name, surname = StringUtil.split(fullname, na="encoded_space")
        country_code = LocationUtils.get_code(location)

        if name in names:
            if fullname in names[name]['persons']:
                say("\tSuch fullname already classified! Rare, but can happen. Move on.")
            else:
                say("\tAdding a new fullname to already classified name. Move on")
                names[name]['persons'].append(fullname)
                DatabaseFactory.update_record_threaded(connection, (fullname, names[name]['accuracy'], names[name]['classification']),
                                                       is_locked_tb, sample_tb_name)
        else:
            say("\tNew name. Lets start classification.")
            names[name] = {'persons': list(), 'classification': None, 'accuracy': None}
            names[name]['persons'].append(fullname)
            say("\t[Batch load] added new name: " + str(name.encode('utf-8')) + " as deriven from: " + str(fullname.encode('utf-8')))
            job = GeneralGetter(int(iterator), (name, surname, country_code), fullname)
            say('Creating instance of [GeneralGetter] complete')
            say('Appending thread to collection of threads')
            threads.append(job)
            say('Append complete, threads[] now have size: ' + str(len(threads)))
            log_debug('Starting thread ' + str(int(iterator)-1) + '....', True)
            job.start()
            while (num_working(threads) > 4):
                time.sleep(0.25)  # sleeping for 250 ms - there are already 4 active threads..
        row = cursor.fetchone()

    cursor.close()
    definitely_say("Finished getting gender data, waiting for processes to finish...")

    while (not all_finished(threads)):
        time.sleep(1.00)  # wait for all 4 threads to finish

    #DatabaseFactory.update_database(connection, names, is_locked_tb, sample_tb_name)

    for t in DatabaseFactory.threads:
        if t.isAlive():
            t.join()

    connection.close()
