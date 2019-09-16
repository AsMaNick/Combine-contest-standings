import requests
import json
import dis
import codecs
import sys
import os
from tqdm import tqdm


class Submission:
    def __init__(self, run_id, user_name, prob, hour, minute, second, status):
        self.run_id = run_id
        self.user_name = user_name
        self.prob = prob
        self.hour = hour
        self.minute = minute
        self.second = second
        self.status = status
        
    def write(self, f):
        print('{};{};{};{};{};{};{}'.format(self.run_id, self.user_name, self.prob, self.hour, self.minute, self.second, self.status), file=f)
        
    def __lt__(self, other):
        return (self.hour, self.minute, self.second) < (other.hour, other.minute, other.second)
        

def get_wa_times(last, cnt):
    coef = 0.9
    if cnt >= 3:
        coef = 0.8
    elif cnt >= 7:
        coef = 0.7
    elif cnt >= 15:
        coef = 0.6
    else:
        coef = 0.5
    first = last * coef
    res = []
    for k in range(1, cnt + 1):
        t = min(300, int(first + (last - first) * k / (k + 1)))
        h = t // 60
        m = t % 60
        res.append((h, m))
    return res
        
    
def process(input_file):
    parse_regions = True
    inf = open(input_file + '.html', 'rb')
    ouf = open(input_file + '.csv', 'w', encoding='utf8')
    ouf_regions = open(input_file + '_regions.json', 'w', encoding='utf8')
    keys = ['Run_Id', 'User_Name', 'Prob', 'Dur_Hour', 'Dur_Min', 'Dur_Sec', 'Stat_Short']
    for key in keys:
        print(key, end=';', file=ouf)
    print('', file=ouf)
    text = inf.read()
    text = codecs.decode(text, 'utf-8-sig')
    pos = text.find('<tr>') + 1
    pos = text.find('<tr>') + 1
    pos = text.find('<tr>') + 1
    pos = text.find('<tr>') + 1
    submissions = []
    team_regions = dict()
    while True:
        pos = text.find('<tr>', pos)
        if pos == -1:
            break
        pos = text.find('<td', pos) + 1
        pos = text.find('<td', pos) + 1
        
        if parse_regions:
            user_name = text[pos + 3:text.find('</td>', pos)]
            pos = text.find('<td', pos) + 1
            region = text[pos + 3:text.find('</td>', pos)]
            team_regions[user_name] = region
            continue
            
        pos = text.find('<p>', pos)
        pos_to = text.find('</p>', pos)
        user_name = text[pos + 3:pos_to].replace('&amp;', '&').replace('&quot;', '"').replace('&sp&', ' ')
        if user_name.find('Total') != -1:
            break
        pos = pos_to
        for i in range(problems):
            pos = text.find('<p', pos)
            pos = text.find('>', pos) + 1
            if text[pos] == '+':
                pos += 1
                cnt = 0
                while '0' <= text[pos] <= '9':
                    cnt = cnt * 10 + ord(text[pos]) - ord('0')
                    pos += 1
                pos = text.find('<p', pos)
                pos = text.find('>', pos) + 1
                time = text[pos:pos + 6]
                h = int(time[1])
                m = int(time[3:5])
                s = 0
                wa_times = get_wa_times(h * 60 + m, cnt)
                for wa in wa_times:
                    submissions.append(Submission(len(submissions), user_name, chr(ord('A') + i), wa[0], wa[1], 0, 'WA'))
                submissions.append(Submission(len(submissions), user_name, chr(ord('A') + i), h, m, s, 'OK'))
            elif text[pos] == '-':
                pos += 1
                cnt = 0
                while '0' <= text[pos] <= '9':
                    cnt = cnt * 10 + ord(text[pos]) - ord('0')
                    pos += 1
                wa_times = get_wa_times(299, cnt)
                for wa in wa_times:
                    submissions.append(Submission(len(submissions), user_name, chr(ord('A') + i), wa[0], wa[1], 0, 'WA'))
    json.dump(team_regions, ouf_regions)
    submissions.sort()
    for submission in submissions:
        submission.write(ouf)
    inf.close()
    ouf.close()
    

problems = 12
process('data/2019_2/results')