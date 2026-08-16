def parse_problem(line):
    line = line.removeprefix('@p ')
    problem_id, *data = line.split(',')
    problem_name = ','.join(data[:-2])
    return problem_id, problem_name


def parse_team(line):
    line = line.removeprefix('@t ')
    team_id, *data = line.split(',')
    team_name = ','.join(data[2:]).strip('"')
    return team_id, team_name


def parse_submission(line):
    line = line.removeprefix('@s ')
    team_id, problem_id, _, time, verdict = line.split(',')
    time = int(time)
    return team_id, problem_id, time, verdict


def load_data(filename):
    problems = dict()
    teams = dict()
    submissions = []
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if line.startswith('@p '):
                problem_id, problem_name = parse_problem(line)
                problems[problem_id] = problem_name
            elif line.startswith('@t '):
                team_id, team_name = parse_team(line)
                teams[team_id] = team_name
            elif line.startswith('@s '):
                team_id, problem_id, time, verdict = parse_submission(line)
                submissions.append((team_id, problem_id, time, verdict))
    return problems, teams, submissions


def get_short_verdict(verdict):
    if verdict in ['OK', 'AC']:
        return 'OK'
    elif verdict in ['CE']:
        return 'CE'
    return 'RJ'


def get_full_verdict(verdict):
    if verdict in ['OK', 'AC']:
        return 'AC'
    if verdict in ['RT', 'RE']:
        return 'RE'
    return verdict


def convert_to_csv(filename):
    problems, teams, submissions = load_data(filename)
    with open(filename + '.csv', 'w', encoding='utf-8') as wf:
        print('Run_Id;User_Name;Prob;Dur_Hour;Dur_Min;Dur_Sec;Stat_Short;Stat_Full', file=wf)
        for run_id, (team_id, problem_id, time, verdict) in enumerate(submissions):
            t = teams[team_id]
            assert problem_id in problems
            hh = time // 3600
            mm = (time // 60) % 60
            ss = time % 60
            row = run_id, t, problem_id, hh, mm, ss, get_short_verdict(verdict), get_full_verdict(verdict)
            print(';'.join(map(str, row)), file=wf)


convert_to_csv('data/2026_osijek_summer/original_logs/6/ghost.dat')
