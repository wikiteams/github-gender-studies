import glob
import codecs
import re
from ast import literal_eval as make_tuple

iterator = glob.iglob('pull#*.txt')
langfiles = glob.iglob('*.one.lang')

count_males = 0
men = set()
names_men = list()
freq_names_men = dict()
count_females = 0
women = set()
names_women = list()
freq_names_women = dict()
count_unis = 0
unis = set()
names_unis = list()
freq_names_unis = dict()

for result in langfiles:
    f = open(result)
    for line in f:
        lang = make_tuple(line)
        print 'in file: ' + result + ' language detected is: ' + lang[0] + ' with probability: ' + str(lang[1])

for result in iterator:
    f = codecs.open(result, encoding='utf-8')
    for line in f:
        if re.match('[\-]{1}[\[]{1}(.)+[\,]{1}(.)+[\,]{1}(.)+[\]]{1}', line):
            sex = line.split(',')[2].strip().strip(']').lower()
            nick = line.split(',')[0].strip().strip('-[').lower()
            name = line.split(',')[1].strip().split()[0].lower()
            if sex == 'male':
                count_males += 1
                if nick not in men:
                    men.add(nick)
                    names_men.append(name)
            elif sex == 'female':
                count_females += 1
                if nick not in women:
                    women.add(nick)
                    names_women.append(name)
            elif sex == 'unisex':
                count_unis += 1
                if nick not in unis:
                    unis.add(nick)
                    names_unis.append(name)
            #print repr(line)
        #elif re.match('[\-]{1}[\[]{1}(.)+[\,]{1}(.)+[\]]{1}', line):
            #print repr(line)
    print 'moving to file: ' + result

print 'count_utterance_unis ' + str(count_unis)
print 'count_utterance_males ' + str(count_males)
print 'count_utterance_females ' + str(count_females)

print 'count_unis ' + str(len(unis))
print 'count_males ' + str(len(men))
print 'count_females ' + str(len(women))

print 'Men:'
freqsm = [(item, names_men.count(item)) for item in names_men]
freqsm.sort(key=lambda tup: tup[1])
print(freqsm)
print 'Women:'
freqsw = [(item, names_women.count(item)) for item in names_women]
freqsw.sort(key=lambda tup: tup[1])
print(freqsw)
print 'Unisex:'
freqsu = [(item, names_unis.count(item)) for item in names_unis]
freqsu.sort(key=lambda tup: tup[1])
print(freqsu)
