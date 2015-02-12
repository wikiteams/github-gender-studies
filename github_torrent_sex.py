# coding=UTF-8
'''
Puts information on gender estimation of GitHub users
into our GitHub Torrent MySQL mirror
@version 1.3
@author Oskar Jarczyk
@since 1.0
@update 12.02.2015
'''

version_name = 'version 1.3 codename: Dżęder'

import csv
import scream
import logmissed
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
from bs4 import BeautifulSoup
import unicodedata