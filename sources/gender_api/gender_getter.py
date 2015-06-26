# coding=UTF-8
from logger import scream
import urllib3
import random
import time
import json
import threading
from unique import NamesCollection
import pkg_resources
try:
    import elementtree.ElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


names = NamesCollection.names

MALE = 1
FEMALE = 2


def get_random_auth():
    secrets = []
    with open(pkg_resources.resource_filename('sources.gender_api', 'credentials.dat'), 'r') as passfile:
        for line in passfile:
            secrets.append(line)
    return random.choice(secrets)


def StripNonAlpha(s):
    return "".join(c for c in s if c.isalpha())


class GeneralGetter(threading.Thread):

    finished = False
    batch = None

    def __init__(self, threadId, batch):
        scream.say('Initiating GeneralGetter, running __init__ procedure.')
        self.threadId = threadId
        threading.Thread.__init__(self)
        urllib3.disable_warnings()
        self.daemon = True
        self.finished = False
        self.batch = batch

    def run(self):
        scream.definitely_say('GeneralGetter thread(' + str(self.threadId) + ')' + 'starts working on batch of ' + str(len(self.batch)) + ' names')
        self.finished = False
        self.get_data(self.batch)

    def is_finished(self):
        return self.finished if self.finished is not None else False

    def set_finished(self, finished):
        scream.say('Marking the thread ' + str(self.threadId) + ' as finished..')
        self.finished = finished

    def cleanup(self):
        scream.say('Marking thread on ' + str(self.threadId) + ' as definitly finished..')
        self.finished = True
        scream.say('Terminating/join() thread on ' + str(self.threadId) + ' ...')
        self.my_browser.close()

    def get_data(self, all_names):
        global names
        global MALE
        global FEMALE

        self.http = urllib3.PoolManager()

        scream.say('#Ask now the gender-api for names gender')
        self.oauth = get_random_auth()

        while True:
            try:
                self.adress = ur'https://gender-api.com/get?name={unpack_names}&key={oauth}'.format(
                              unpack_names=';'.join([StripNonAlpha(name) for name in all_names]),
                              oauth=self.oauth)
                self.r = self.http.request('GET', self.adress.encode('utf-8'))
                if self.r.data is None:
                    scream.say("No answer in http response body!")
                    time.sleep(60)
                    continue
                error_messages = ['errno', '30', 'errmsg', 'limit reached']
                if all(x in self.r.data for x in error_messages):
                    scream.say("Limit reached! Retry after a minute.")
                    scream.say(self.adress)
                    scream.say(self.r.data)
                    time.sleep(60)
                    continue
                break
            except urllib3.exceptions.ConnectionError:
                scream.definitely_say('Site gender-api.com seems to be down' +
                                      '. awaiting for 60s before retry')
                time.sleep(60)
            except Exception as exc:
                scream.definitely_say('Some other error: ')
                scream.definitely_say(str(exc))
                time.sleep(60)

        #scream.say('Response read. Parsing json.')
        #scream.say('--------------------------')
        #scream.say(str(self.r.data))
        #scream.say('--------------------------')

        self.result_json = json.loads(self.r.data)

        for idx, val in enumerate(self.result_json['result']):
            self.found_name = val['name']
            self.found_gender = val['gender']
            self.found_accuracy = val['accuracy']

            if self.found_gender.lower() == 'female':
                names[all_names[idx]]['classification'] = FEMALE
            else:
                names[all_names[idx]]['classification'] = MALE

            #scream.say('Response read. Parsing json.')
            #scream.say('+++++++++++++++++++++++++++++++++++')
            #scream.say(str(all_names[idx]) + ' ' + str(val['name']) + ' ' + str(val['gender']))
            #scream.say('+++++++++++++++++++++++++++++++++++')

            names[all_names[idx]]['accuracy'] = self.found_accuracy

        self.set_finished(True)
