import glob
import codecs
import re

iterator = glob.iglob('pull#*.txt')

count_males = 0
men = set()
count_females = 0
women = set()
count_unis = 0
unis = set()

for result in iterator:
    f = codecs.open(result, encoding='utf-8')
    for line in f:
        if re.match('[\-]{1}[\[]{1}(.)+[\,]{1}(.)+[\,]{1}(.)+[\]]{1}', line):
            sex = line.split(',')[2].strip().strip(']').lower()
            nick = line.split(',')[0].strip().strip('-[').lower()
            if sex == 'male':
                count_males += 1
                if nick not in men:
                    men.add(nick)
            elif sex == 'female':
                count_females += 1
                if nick not in women:
                    women.add(nick)
            elif sex == 'unisex':
                count_unis += 1
                if nick not in unis:
                    unis.add(nick)
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
