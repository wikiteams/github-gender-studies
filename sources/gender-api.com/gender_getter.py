# coding=UTF-8
import scream
import urllib3
import random
import time
import json
import threading
from unique import NamesCollection
# import ElementTree based on the python version
try:
    import elementtree.ElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


names = NamesCollection.names

MALE = 1
FEMALE = 2


def get_random_auth():
    secrets = []
    with open('credentials.dat', 'r') as passfile:
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
        scream.cout('GeneralGetter thread(' + str(self.threadId) + ')' + 'starts working on batch of ' + str(len(self.batch)) + ' names')
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

        scream.say('#Ask now the Internet for name gender')
        self.oauth = get_random_auth()

        while True:
            try:
                self.r = self.http.request('GET',
                                           r'https://gender-api.com/get?name={1}&key={2}'.format(
                                           str(StripNonAlpha(name) + ';' for name in all_names).rstrip(';'), self.oauth))
                if self.r.data is None:
                    scream.say("No answer in http response body!")
                    time.sleep(60)
                    continue
                error_messages = ['errno', '30', 'errmsg', 'limit reached']
                if all(x in self.r.data for x in error_messages):
                    scream.say("Limit reached! Retry after a minute.")
                    time.sleep(60)
                    continue
                break
            except urllib3.URLError:
                scream.ssay('Site gender-api.com seems to be down' +
                            '. awaiting for 60s before retry')
                time.sleep(60)
            except Exception as exc:
                scream.ssay('Some other error: ')
                scream.ssay(str(exc))
                time.sleep(60)

        scream.say('Response read. Parsing json.')

        result_json = json.loads(self.r.data)

        for idx, val in enumerate(result_json):
            self.found_name = val['name']
            self.found_gender = val['name']
            self.found_accuracy = val['accuracy']

            if self.found_gender.lower() == 'female':
                names[all_names[idx]]['classification'] = FEMALE
            else:
                names[all_names[idx]]['classification'] = MALE

            names[all_names[idx]]['accuracy'] = self.found_accuracy

        self.set_finished(True)