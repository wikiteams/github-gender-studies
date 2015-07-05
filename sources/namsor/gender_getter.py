# coding=UTF-8
from logger.scream import say, definitely_say
import database_factory as DatabaseFactory
import string_utils as StringUtil
import urllib3
import time
import json
import threading
from unique import NamesCollection
try:
    import elementtree.ElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


names = NamesCollection.names

MALE = 1
FEMALE = 2


def gender_object(gender):
    if gender.lower() == 'female':
        return FEMALE
    else:
        return MALE


class GeneralGetter(threading.Thread):

    finished = False
    batch = None
    fullname = None

    def __init__(self, threadId, batch, fullname):
        say('Initiating GeneralGetter, running __init__ procedure.')
        self.threadId = threadId
        threading.Thread.__init__(self)

        # urllib 3 is a successor to urllib 2, it better handles concurency and it's thread safe
        urllib3.disable_warnings()
        self.daemon = True
        self.finished = False
        self.batch = batch
        self.fullname = fullname

    def run(self):
        definitely_say('GeneralGetter thread(' + str(self.threadId) + ')' + 'starts working on batch of ' + str(len(self.batch)) + ' informations')
        self.finished = False
        self.get_data(self.batch, self.fullname)

    def is_finished(self):
        return self.finished if self.finished is not None else False

    def set_finished(self, finished):
        say('Marking the thread ' + str(self.threadId) + ' as finished..')
        self.finished = finished

    def cleanup(self):
        say('Marking thread on ' + str(self.threadId) + ' as definitly finished..')
        self.finished = True
        say('Terminating/join() thread on ' + str(self.threadId) + ' ...')
        # self.my_browser.close()

    def get_data(self, person_tuple, fullname):
        global names
        global MALE
        global FEMALE

        self.http = urllib3.PoolManager()

        say('#Ask now the namsor gender API for classification')

        name, surname, country_code = person_tuple

        self.network_attempts = 0
        while True:
            try:
                self.adress = ur'http://api.namsor.com/onomastics/api/json/gendre/{name}/{surname}/{country_code}'.format(
                              name=StringUtil.StripNonAlpha(name, False), surname=StringUtil.StripNonAlpha(surname, True),
                              country_code=country_code if country_code is not None else "")
                self.r = self.http.request('GET', self.adress.encode('utf-8'))
                self.network_attempts += 1
                if self.r.status >= 300:
                    say("Server response with HTTP code higher than or eq. 300, which means failure!")
                    time.sleep(30)
                    continue
                if self.r.data is None:
                    say("No answer in HTTP response body!")
                    time.sleep(60)
                    continue
                error_messages = ['Apache Tomcat', '7.0.52', 'Error report', 'Status report']
                if all(x in self.r.data for x in error_messages):
                    say("HTTP error returned by WWW server. Try again, max 10 times.")
                    say(self.adress)
                    say(self.r.data)
                    time.sleep(60)
                    if self.network_attempts < 10:
                        continue
                break
            except urllib3.exceptions.ConnectionError:
                definitely_say('Site api.namsor.com seems to be down' +
                               '. awaiting for 60s before retry')
                time.sleep(60)
            except Exception as exc:
                definitely_say('Some other error: ')
                definitely_say(str(exc))
                time.sleep(60)

        try:
            self.result_json = json.loads(self.r.data)
        except ValueError:
            self.set_finished(True)
            return

        self.found_gender = self.result_json["gender"]
        self.found_accuracy = int(float(self.result_json["scale"]) * 100)

        names[name]['classification'] = gender_object(self.found_gender)
        names[name]['accuracy'] = self.found_accuracy

        DatabaseFactory.update_record_threaded(DatabaseFactory.connection,
                                               (fullname, self.found_accuracy, gender_object(self.found_gender)))

        self.set_finished(True)
