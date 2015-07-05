import pkg_resources
import sys
from logger.scream import say
try:
    import MySQLdb as MSQL
except ImportError:
    import _mysql as MSQL


IP_ADDRESS = "10.4.4.3"  # Be sure to update this to your needs


def init():
    return MSQL.connect(host=IP_ADDRESS, port=3306, user=pkg_resources.resource_string('sources.gender_api', 'mysqlu.dat'),
                        passwd=pkg_resources.resource_string('sources.gender_api', 'mysqlp.dat'),
                        db="github", connect_timeout=5 * 10**7,
                        charset='utf8', init_command='SET NAMES UTF8',
                        use_unicode=True)


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


def update_database(connection, names, is_locked_tb, sample_tb_name):
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
