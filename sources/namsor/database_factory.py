import pkg_resources
import sys
import warnings
import threading
from logger.scream import say
try:
    import MySQLdb as MSQL
except ImportError:
    import _mysql as MSQL


IP_ADDRESS = "10.4.4.3"  # Be sure to update this to your needs
threads = []

connection = None


def deprecated(func):
    '''This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used.'''
    def new_func(*args, **kwargs):
        warnings.warn("Call to deprecated function {}.".format(func.__name__),
                      category=DeprecationWarning)
        return func(*args, **kwargs)
    new_func.__name__ = func.__name__
    new_func.__doc__ = func.__doc__
    new_func.__dict__.update(func.__dict__)
    return new_func


def init():
    global connection
    connection = MSQL.connect(host=IP_ADDRESS, port=3306, user=pkg_resources.resource_string('sources.gender_api', 'mysqlu.dat'),
                              passwd=pkg_resources.resource_string('sources.gender_api', 'mysqlp.dat'),
                              db="github", connect_timeout=5 * 10**7,
                              charset='utf8', init_command='SET NAMES UTF8',
                              use_unicode=True)
    return connection


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
        print 'Did you forgot to create users_ext table?'
        print 'Program will exit now'
        sys.exit(0)


def get_record_count(cursor, sample_tb_name, limit):
    cursor.execute(r'select count(*) from ' + str(sample_tb_name)
                   + ' where (type = "USR") and (name rlike "[a-zA-Z]+( [a-zA-Z]+)?"){optional}'.format(optional=" limit 500" if limit else ""))
    rows = cursor.fetchall()
    return rows[0][0]


@deprecated
def batch_update_database(connection, names, is_locked_tb, sample_tb_name):
    cursor = connection.cursor()
    for key in names.keys():
        collection = names[key]
        for fullname in names[key]['persons']:
            update_query = r'UPDATE {table} SET gender = {gender} , accuracy = {accuracy} where full_name = "{fullname}"'.format(
                           gender=collection['classification'],
                           fullname=fullname.encode('utf-8').replace('"', '\\"'),
                           table='users_ext' if is_locked_tb else sample_tb_name,
                           accuracy=collection['accuracy'])
            say(update_query)
            cursor.execute(update_query)
    cursor.close()


def update_record_threaded(connection, classification, is_locked_tb=True, sample_tb_name="users"):
    if (classification[2] == 2):
        thread = threading.Thread(target=update_single_record, args=(connection, classification, is_locked_tb, sample_tb_name))
        threads.append(thread)
        thread.start()
    else:
        pass


def update_single_record(connection, classification, is_locked_tb, sample_tb_name):
    cursor = connection.cursor()
    fullname, accuracy, gender = classification
    update_query = r'UPDATE {table} t1 JOIN {sample_tb_name} t2 ON t1.id = t2.id SET t1.gender = {gender} , t1.accuracy = {accuracy} WHERE t2.name = "{fullname}"'.format(
                   gender=gender, fullname=fullname.encode('utf-8').replace('"', '\\"'), table='users_ext' if is_locked_tb else sample_tb_name,
                   accuracy=accuracy, sample_tb_name=sample_tb_name)
    say(update_query)
    cursor.execute(update_query)
    cursor.close()
    return
