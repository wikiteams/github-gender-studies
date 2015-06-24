# coding=UTF-8
import scream
import urllib2
import mechanize
import time
from bs4 import BeautifulSoup
import threading
import unicodedata
from unique import NamesCollection
# import ElementTree based on the python version
try:
    import elementtree.ElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


names = NamesCollection.names

MALE = 1
FEMALE = 2
UNISEX = 3
UNKNOWN = 99


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
