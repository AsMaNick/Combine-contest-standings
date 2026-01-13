import json
from bs4 import BeautifulSoup
from collections import defaultdict


def extract_numbers(s):
    res = []
    last = None
    for c in s:
        if not c.isdigit():
            if last is not None:
                res.append(int(last))
                last = None
            continue
        if last is None:
            last = ''
        last += c
    if last is not None:
        res.append(last)
    return res


def process_submissions(is_first_run):
    global problem_id_by_name, team_external_ids
    all_verdicts = set()
    all_submissions = []
    total_submissions = defaultdict(int)
    # MANUAL FIX FOR INCONSISTENT TIME
    ce = {
        ('1115042', 1): 3,
        ('1119791', 6): 1,
        ('1115034', 6): 0
    }
    # MANUAL FIX FOR INCONSISTENT TIME
    run_id = 0
    for team_id, team_data in data.items():
        team_external_id = team_id[team_id.find('-') + 1:]
        team_external_ids.add(team_external_id)
        for problem_id, (problem_name, submissions) in enumerate(team_data.items()):
            assert problem_name.startswith('problem-')
            problem_name = problem_name[len('problem-'):]
            if problem_name not in problem_id_by_name:
                problem_id_by_name[problem_name] = problem_id
            assert problem_id_by_name[problem_name] == problem_id
            # print(team_id, problem_id, problem_name, type(submissions), len(submissions))
            if is_first_run:
                continue
            for submission_num, submission in enumerate(submissions[::-1]):
                if submission['time'] == 'After contest':
                    continue
                if submission_num == ce.get((team_external_id, problem_id)):
                    continue
                verdict = submission['verdict']
                verdict = verdict[verdict.rfind('">') + 2:verdict.rfind('</span>')]
                all_verdicts.add(verdict)
                assert verdict in ['pending', 'correct', 'too-late', 'rejected'], verdict
                status = 'OK' if verdict == 'correct' else 'RJ'
                total_submissions[(team_external_id, problem_id)] += 1
                if (team_external_id, problem_id) in successful_submissions and status != 'OK':
                    if total_submissions[(team_external_id, problem_id)] == successful_submissions[(team_external_id, problem_id)][1]:
                        status = 'OK'
                        t = submission['time']
                        hh = int(t[0])
                        mm = int(t[2:4])
                        if hh * 60 + mm != successful_submissions[(team_external_id, problem_id)][0]:
                            print(f'Inconsistent time (\'{team_external_id}\', {problem_id})', successful_submissions[(team_external_id, problem_id)][0], submission['time'], team_name_by_external_id[team_external_id], chr(ord('A') + problem_id))
                run_id += 1
                all_submissions.append((submission['time'], run_id, team_name_by_external_id[team_external_id], chr(ord('A') + problem_id), status))
    if not is_first_run:
        print(all_verdicts)
        for problem_name in problem_id_by_name.keys():
            print(f'    \'{problem_name.replace("-", " ").title()}\',')
    all_submissions.sort()
    with open('logs.csv', 'w', encoding='utf-8') as wf:
        print('Run_Id;User_Name;Prob;Dur_Hour;Dur_Min;Dur_Sec;Stat_Short;', file=wf)
        for submission in all_submissions:
            t = submission[0]
            hh = int(t[0])
            mm = int(t[2:4])
            ss = 0
            row = 0, submission[2], submission[3], hh, mm, ss, submission[4]
            print(';'.join(map(str, row)), file=wf)


submissions_filename = 'sources/dom_judge.json'
standings_filename = 'sources/standings.html'

data = json.load(open(submissions_filename, 'r', encoding='utf-8'))['submissions']
problem_id_by_name = dict()
team_external_ids = set()
process_submissions(True)

soup = BeautifulSoup(open(standings_filename, 'r', encoding='utf-8').read(), 'html.parser')
successful_submissions = dict()
team_name_by_external_id = dict()
regions = dict()
for team_external_id in team_external_ids:
    team_elem = soup.find('tr', {'data-team-external-id': team_external_id})
    country_flag = team_elem.find('img', {'class': 'countryflag'})
    team_name = team_elem.get('data-team-name')
    team_name_by_external_id[team_external_id] = team_name
    regions[team_name] = country_flag.get('title').replace('Türkiye', 'Turkey')
    for problem_name, problem_id in problem_id_by_name.items():
        problem_elem = team_elem.find('a', {'data-problem-id': problem_name})
        if problem_elem is None:
            continue
        problem_elem = problem_elem.find('div', {'class': 'score_correct'})
        if problem_elem is None:
            continue
        numbers = extract_numbers(problem_elem.get_text().strip())
        assert len(numbers) == 2
        successful_submissions[(team_external_id, problem_id)] = numbers
process_submissions(False)
json.dump(regions, open('regions.json', 'w', encoding='utf-8'))
