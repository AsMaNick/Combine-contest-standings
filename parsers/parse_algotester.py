import requests
import json
from datetime import datetime
import sys
import os
from tqdm import tqdm
from collections import defaultdict


class Submission:
    def __init__(self, run_id, user_name, problem_id, hour, minute, second, verdict):
        self.run_id = run_id
        self.user_name = user_name
        self.problem_id = problem_id
        self.hour = hour
        self.minute = minute
        self.second = second
        self.verdict = verdict
        
    def write(self, f):
        print('{};{};{};{};{};{};{}'.format(self.run_id, self.user_name, self.problem_id, self.hour, self.minute, self.second, self.verdict), file=f)
        
    def __lt__(self, other):
        return (self.hour, self.minute, self.second) < (other.hour, other.minute, other.second)
        
    
def get_verdict(verdict):
    if verdict.find('Wrong Answer') != -1 or verdict.find('Неправильна відповідь') != -1:
        return 'WA'
    if verdict.find('Time Limit') != -1 or verdict.find('Ліміт часу') != -1:
        return 'TL'    
    if verdict.find('Memory Limit') != -1 or verdict.find('Ліміт пам\'яті') != -1:
        return 'ML'    
    if verdict.find('Run Time Error') != -1 or verdict.find('Помилка часу виконання') != -1:
        return 'RE'  
    if verdict.find('Compilation Error') != -1 or verdict.find('Помилка компілювання') != -1:
        return 'CE'  
    if verdict.find('Accepted') != -1 or verdict.find('Зараховано') != -1:
        return 'OK'
    print('Unsupported verdict:', verdict)
    exit(1)    
    
        
def update(user_name):
    if user_name in team_members:
        user_name = team_members[user_name][:team_members[user_name].find(' (')]
    return user_name

    
team_members = {} # json.load(open('data/uzhgorod/team_members1.txt', 'r'))


def parse_time_hms(t):
    h = int(t[:2])
    m = int(t[3:5])
    s = int(t[6:8])
    return h * 3600 + m * 60 + s
    

def process(input_file):
    time_start_hms = parse_time_hms('07:00:00Z')
    ouf = open(input_file[:input_file.rfind('.')] + '.csv', 'w', encoding='utf8')
    print('Run_Id;User_Name;Prob;Dur_Hour;Dur_Min;Dur_Sec;Stat_Short;', file=ouf)
    data = json.load(open(input_file, 'r', encoding='utf-8'))['rows']
    if input_file.endswith('.json'):
        with open(input_file[:-5] + '_indent.json', 'w', encoding='utf-8') as wf:
            json.dump(data, wf, indent=2)
    submissions = []
    problem_names = defaultdict(set)
    for submission in tqdm(data):
        run_id = submission['Id']
        user_name = submission['Contestant']['Text'].strip()
        problem_name = submission['Problem']['Text'].strip()
        user_name = user_name
        user_name = update(user_name)
        user_name = '"' + user_name.replace('"', '""') + '"' # to work with teams with '"' in name
        problem_id = submission['Problem']['Text'][:1] # only letter
        assert problem_name[:4] == f'{problem_id} - '
        problem_name = problem_name[4:].strip()
        problem_names[problem_id].add(problem_name)
        if True:
            timestamp = parse_time_hms(submission['TimeCreated'][-9:])
            t = timestamp - time_start_hms
        else:
            time_start = datetime(2024, 9, 28, 10, 00, 0)
            timestamp = int(submission['TimeCreated'][6:-2])
            timestamp = datetime.fromtimestamp(timestamp / 1e3) - time_start
            t = timestamp.seconds
        hour = t // 3600
        minute = (t % 3600) // 60
        second = (t % 3600) % 60
        if t > 3600 * 5:
            print(t, hour, minute, second)
        verdict = get_verdict(submission['Result']['Text'])
        submissions.append(Submission(run_id, user_name, problem_id, hour, minute, second, verdict))
    submissions.sort()
    for submission in submissions:
        submission.write(ouf)
    ouf.close()
    for problem_id, names in sorted(problem_names.items()):
        names = list(names)
        print(problem_id, names)
        assert len(names) == 1
    for problem_id, names in sorted(problem_names.items()):
        names = list(names)
        print(f"    '{names[0]}',")


process('data/2025_1/sources/logs_algotester.json')
