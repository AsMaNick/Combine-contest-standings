import os
import sys
import dis
import math
import json
import pickle
import codecs
import requests
import pyperclip
from utils import *
from tqdm import tqdm
from settings import *
from collections import defaultdict
from camps_combiner import CompressedStandings


def bad_user(user_name):
    return user_name in ['Judge_Main', 'nan', 'judge13', 'ejudge&sp&administrator']


def dump_problem_stats(stats_by_problem):
    with open('created_tables/problem_stats.json', 'w') as problem_stats_f:
        json.dump(stats_by_problem, problem_stats_f, indent=2)
    with open('created_tables/problem_stats.txt', 'w') as problem_stats_f:
        for problem_id, stats in sorted(stats_by_problem.items()):
            for stat in sorted(stats.keys()):
                print(problem_id, stat, file=problem_stats_f)
                if stat == 'binned_verdicts':
                    keys = ['AC', 'WA', 'RE', 'TL', 'ML', 'CE', 'FAILURE']
                    print('', *keys, sep='\t', file=problem_stats_f)
                    print(0, *([0] * len(keys)), sep='\t', file=problem_stats_f)
                    for bin_id, row in enumerate(stats[stat]):
                        for key in row.keys():
                            assert key in keys, key
                        data = [row[key] for key in keys]
                        label = ''
                        if (bin_id + 1) * minutes_in_bin % minutes_per_bin_label == 0:
                            label = (bin_id + 1) * minutes_in_bin
                        print(label, *data, sep='\t', file=problem_stats_f)
                else:
                    if stat == 'verdicts':
                        iter_keys = ['AC', 'TL', 'WA', 'RE', 'ML', 'FAILURE']
                        for key in stats[stat].keys():
                            assert key in iter_keys, key
                    else:
                        iter_keys = sorted(stats[stat].keys())
                    for key in iter_keys:
                        print(key, stats[stat][key] if stats[stat][key] else '', sep='\t', file=problem_stats_f)
            print(file=problem_stats_f)


assert problems == len(problem_names)
assert (show_oj_rating != []) == (path_to_oj_info != '')
assert contest_duration % minutes_in_bin == 0

max_length_place = '7771777'

f = open('created_tables/{}.html'.format(standings_file_name), 'w', encoding='utf8')
all_successful_submits = {}
all_submissions = {}

team_regions = dict()
problem_openers = ['' for i in range(problems)]
time_openers = [1e9 for i in range(problems)]

team_members = {}
if path_to_team_members != '':
    team_members = {key.replace(' ', '&sp&') : value for key, value in json.load(open(path_to_team_members, 'r')).items()}

team_members_with_oj_info = {}
if path_to_oj_info != '':
    team_members_with_oj_info = json.load(open(path_to_oj_info, 'r'))

print('<div id="standingsSettings"><!--', file=f)
print('contestDuration {}'.format(contest_duration), file=f)
print('maxItmoRating {}'.format(max_itmo_rating), file=f)
print('--></div>', file=f)
if len(csv_files) > 0:
    bins_in_contest = contest_duration // minutes_in_bin
    import pandas as pd
    print('<div id="submissionsLog"><!--', file=f)
    all_status = {}
    all_frozen = {}
    assert len(csv_files) == len(regions), f'{len(csv_files)}, {len(regions)}'
    solved_problems_including_upsolving = defaultdict(set)
    stats_by_problem = {
        problem_id: {
            'verdicts': defaultdict(int),
            'langs': defaultdict(int),
            'binned_verdicts': [defaultdict(int) for bin_id in range(bins_in_contest)]
        } for problem_id in problem_ids
    }
    for csv_file, region in zip(csv_files, regions):
        data = pd.read_csv(path_to_data + csv_file, sep=';')
        for it, row in tqdm(data.iterrows()):
            user_name = str(row['User_Name']).strip().replace(' ', '&sp&')
            if row['Prob'][0] == '!' or bad_user(user_name):
                print('Ignoring', it, row['Run_Id'], row['Prob'], user_name)
                continue
            user_name = user_name.replace('[Bucharest_site]&sp&', '')
            if user_name in team_members:
                user_name = team_members[user_name]
            user_name = user_name.replace(' ', '&sp&')
            prob_id = problem_ids.index(row['Prob'])
            hour = int(row['Dur_Hour'])
            minute = int(row['Dur_Min'])
            second = int(row['Dur_Sec'])
            dur_day = int(row['Dur_Day']) if 'Dur_Day' in row else 0
            time_in_seconds = dur_day * 3600 * 24 + hour * 3600 + minute * 60 + second
            status = row['Stat_Short']
            if status == 'OK' and (frozen_time == contest_duration or time_in_seconds <= frozen_time * 60):
                solved_problems_including_upsolving[user_name.replace('&sp&', ' ')].add(prob_id)
            if time_in_seconds > contest_duration * 60:
                # print(user_name, prob_id, hour, minute, row['Stat_Short'])
                # assert False, 'Exiting due to large time'
                continue
            if (second != 0 and round_time == 'UP') or (second > 30 and round_time == 'CLOSEST'):
                minute += 1
                if minute == 60:
                    hour += 1
                    minute = 0
            time = '({}:{}{})'.format(hour, minute // 10, minute % 10)
            team_regions[user_name] = region
            if status == 'IG' or (status == 'CE' and ignore_compilation_error):
                continue
            p = (user_name, prob_id)
            wrong_attempts = 0
            if p in all_successful_submits:
                continue
            if 'Stat_Full' in row:
                stats_by_problem[row['Prob']]['verdicts'][row['Stat_Full']] += 1
                stats_by_problem[row['Prob']]['binned_verdicts'][min(time_in_seconds, contest_duration * 60 - 1) // (minutes_in_bin * 60)][row['Stat_Full']] += (1 if row['Stat_Full'] == 'AC' else -1)
            if 'Lang' in row:
                lang = row['Lang']
                if lang.find('python:3') != -1:
                    lang = 'Python 3'
                elif lang.find('cpp:20') != -1:
                    lang = 'C++ 20'
                elif lang.find('cpp:17') != -1:
                    lang = 'C++ 17'
                elif lang.find('java:') != -1:
                    lang = 'Java ' + lang[5:]
                else:
                    lang = row['Lang'].capitalize()
                stats_by_problem[row['Prob']]['langs'][lang] += 1
            if p in all_status:
                wrong_attempts = all_status[p]
            if time_in_seconds > frozen_time * 60:
                wrong_attempts += 1
                result = '?' + str(wrong_attempts)
                all_status[p] = wrong_attempts
                all_frozen[p] = (time, wrong_attempts)
            elif status == 'OK':
                if time_openers[prob_id] > time_in_seconds:
                    time_openers[prob_id] = time_in_seconds
                    problem_openers[prob_id] = user_name.replace('&sp&', ' ')
                result = '+'
                if wrong_attempts != 0:
                    result += str(wrong_attempts)
                wrong_attempts = -1
                all_successful_submits[p] = time
            else:
                wrong_attempts += 1
                result = '-' + str(wrong_attempts)
                all_status[p] = wrong_attempts
            if user_name not in all_submissions:
                all_submissions[user_name] = []
            all_submissions[user_name].append((prob_id, time, result))
    dump_problem_stats(stats_by_problem)
    print('--></div>', file=f)
    
def get_value(text, pattern, pos):
    '''
    if pattern == '"st_team">':
        print(text[pos:pos+80])
    '''
    pos = text.find(pattern, pos)
    pos += len(pattern)
    res = ''
    while pos < len(text) and text[pos] != '<':
        res += text[pos]
        pos += 1
    res = res.replace('&#36;', '$', 1000)
    return res, pos


def is_digit(x):
    return '0' <= x <= '9'


def get_problem_title(problem_id):
    if problem_id < len(problem_names):
        if hide_problem_title:
            return problem_ids[problem_id]
        return problem_ids[problem_id] + ' - ' + problem_names[problem_id]
    return ''


def get_time_str(time):
    h = time // 60
    m = time % 60
    return '{:1d}:{:02d}:00'.format(h, m)


def get_colored_class(oj, rating):
    if oj == 'AtCoder':
        if rating >= 2800:
            return 'user-red-atcoder'
        elif rating >= 2400:
            return 'user-orange-atcoder'
        elif rating >= 2000:
            return 'user-yellow-atcoder'
        elif rating >= 1600:
            return 'user-blue-atcoder'
        elif rating >= 1200:
            return 'user-cyan-atcoder'
        elif rating >= 800:
            return 'user-green-atcoder'
        elif rating >= 400:
            return 'user-brown-atcoder'
        elif rating > 0:
            return 'user-gray-atcoder'
        return 'user-unrated-atcoder'
    elif oj == 'CF':
        if rating >= 2400:
            return 'user-red'
        elif rating >= 2100:
            return 'user-orange'
        elif rating >= 1900:
            return 'user-violet'
        elif rating >= 1600:
            return 'user-blue'
        elif rating >= 1400:
            return 'user-cyan'
        elif rating >= 1200:
            return 'user-green'
        elif rating > 0:
            return 'user-gray'
        return 'user-black'


def get_nutella_name(name, rating):
    if rating >= 3000:
        return f'<span class="legendary-user-first-letter">{name[0]}</span>{name[1:]}'
    return name


def get_colored_name(info, oj):
    if oj not in info['info']:
        return info['name']
    handle = info['info'][oj]['handle']
    rating = info['info'][oj]['rating']
    if oj == 'AtCoder':
        return f'<a href="https://atcoder.jp/users/{handle}"  title="{handle}, {rating}" class="user-atcoder {get_colored_class(oj, rating)}">{info["name"]}</a>'
    elif oj == 'CF':
        return f'<a href="https://codeforces.com/profile/{handle}" title="{handle}, {rating}" class="user-cf {get_colored_class(oj, rating)}">{get_nutella_name(info["name"], rating)}</a>'
    else:
        raise NotImplementedError


def get_colored_rating(rating, oj):
    if oj == 'AtCoder':
        return f'<a class="user-atcoder {get_colored_class(oj, rating)}">{rating}</a>'
    elif oj == 'CF':
        return f'<a class="user-cf {get_colored_class(oj, rating)}">{get_nutella_name(str(rating), rating)}</a>'
    else:
        raise NotImplementedError


def get_team_rating(team_ratings):
    if len(team_ratings) == 0:
        return 0
    def get_win_probability(ra, rb):
        return 1 / (1 + 10 ** ((rb - ra) / 400.0))
    left = 0
    right = 1e4
    for it in range(100):
        r = (left + right) / 2
        r_wins_probability = 1
        for team_member_rating in team_ratings:
            r_wins_probability *= get_win_probability(r, team_member_rating)
        rating = math.log10(1 / (r_wins_probability) - 1) * 400 + r
        if rating > r:
            left = r
        else:
            right = r
    return int((left + right) / 2)


class Result:
    def __init__(self, name, region, problem_results, problem_times, total, penalty, all_submissions):
        self.name = name
        self.problem_results = problem_results
        self.problem_times = problem_times
        self.total = int(total)
        self.penalty = int(penalty)
        self.region = region
        self.all_submissions = all_submissions
        
    def __lt__(self, other):
        return self.get_comparator_key() < other.get_comparator_key()

    def __eq__(self, other):
        return self.get_comparator_key() == other.get_comparator_key()

    def get_comparator_key(self):
        return -self.total, self.penalty, self.name, self.region

    def get_dirt(self):
        dirt = 0
        for res in self.problem_results:
            if len(res) > 1 and res[0] == '+':
                dirt += int(res[1:])
        if dirt == 0:
            return 0
        return dirt / (dirt + self.total)
        
    def try_problems(self):
        res = 0
        for prob_res in self.problem_results:
            if len(prob_res) > 0 and (prob_res[0] == '+' or prob_res[0] == '-' or prob_res[0] == '?'):
                res += 1
        return res
        
    def solved_problems(self):
        res = 0
        for prob_res in self.problem_results:
            if len(prob_res) > 0 and prob_res[0] == '+':
                res += 1
        return res

    def solved_problems_during_freezing(self, freezing_time):
        return len([
            1 for prob_res, prob_t in zip(self.problem_results, self.problem_times)
            if len(prob_res) > 0 and prob_res[0] == '+' and prob_t and prob_t >= freezing_time
        ])

    def get_name_with_oj_info(self):
        assert team_members_format in ['Team: A, B, C', 'Team (A, B, C)']

        def get_name_without_oj_info(name):
            if team_members_format == 'Team: A, B, C':
                pos = name.rfind(': ')
                if pos != -1:
                    return f'{name[:pos]} ({name[pos + 2:]})'
            return name

        if len(show_oj_rating) == 0:
            return get_name_without_oj_info(self.name), ''
        last_symbol_before_names = ':' if team_members_format == 'Team: A, B, C' else '('
        if self.name.rfind(last_symbol_before_names) == -1:
            return get_name_without_oj_info(self.name), ''
            print(f'Could not extract team name: {self.name}')
            exit(47)
        team_name = self.name[:self.name.rfind(last_symbol_before_names)].strip()
        if team_name not in team_members_with_oj_info:
            return get_name_without_oj_info(self.name), ''
        json_info = {
            'team': team_name,
            'members': []
        }
        if True: # update existing names
            team_members_last_char = (len(self.name) if team_members_format == 'Team: A, B, C' else -1)
            team_members = self.name[self.name.rfind(last_symbol_before_names) + 1:team_members_last_char].strip().split(', ')
            updated_names = []
            taken_name = [False for i in range(len(team_members_with_oj_info[team_name]))]
            for name in team_members:
                name = name.strip()
                # name = ' '.join([name_part.capitalize() for name_part in name.split()])
                name_id = -1
                for i, member in enumerate(team_members_with_oj_info[team_name]):
                    if not taken_name[i] and name == member['name']:
                        name_id = i
                        break
                if name_id == -1:
                    updated_names.append(name)
                    json_info['members'].append({'name': name, 'info': {}})
                else:
                    taken_name[name_id] = True
                    info = team_members_with_oj_info[team_name][name_id]
                    updated_names.append(get_colored_name(info, show_oj_rating[0]))
                    json_info['members'].append(info)
            # team_name += last_symbol_before_names + ' '
            team_name += ' ('
            team_name += ', '.join(updated_names)
            json_info['rating'] = {
                oj : get_team_rating([info['info'][oj]['rating'] for info in json_info['members'] if oj in info['info']]) for oj in show_oj_rating
            }
            team_name += ')'
            if show_oj_rating[0] in json_info['rating'] and json_info['rating'][show_oj_rating[0]] > 0:
                team_name += ', total = ' + get_colored_rating(json_info['rating'][show_oj_rating[0]], show_oj_rating[0])
            return team_name, json.dumps(json_info)
        else: # use full info from json
            raise NotImplementedError

    def write(self, place, open_times, problem_openers, max_solved_problems, cnt_official_teams, f, elapsed_times):
        submissions_log = '<!--' + '\n'.join([f'{problem_id} {time} {result}' for problem_id, time, result in self.all_submissions]) + '-->'
        print('<tr class="participant_result">', file=f)
        print('<td class="st_place"><input style="width: 100%; outline: none; border:none" readonly type="text" value={}></input></td>'.format(place), file=f)
        team_title = self.name
        if self.name in team_members:
            team_title = team_members[self.name]
        name_with_oj_info, json_with_oj_info = self.get_name_with_oj_info()
        json_with_oj_info_div = ''
        if len(show_oj_rating):
            json_with_oj_info_div = f'<div class="teamInfoJson"><!--{json_with_oj_info}--></div>'
        print('<td class="st_team" title="{}"><div class="displayedTeamName">{}</div><div class="teamSubmissionsLog">{}</div>{}</td>'.format('', name_with_oj_info, submissions_log, json_with_oj_info_div), file=f)
        updated_region = self.region
        if show_flags:
            updated_region = update_region_with_flag(updated_region, 'country_flag_small')
        print(f'<td class="st_extra">{updated_region}</td>', file=f)
        if elapsed_times is not None:
            elapsed_time = elapsed_times.get(self.name, '?:??:??')
            if isinstance(elapsed_time, int):
                assert elapsed_time >= 0
                elapsed_time = min(elapsed_time, contest_duration * 60)
                if elapsed_time == contest_duration * 60:
                    elapsed_time = 'Finished'
                else:
                    elapsed_time = f'{elapsed_time // 3600}:{(elapsed_time % 3600) // 60:02d}:{elapsed_time % 60:02d}'
                    if contest_live_time == contest_duration:
                        elapsed_time = f'<strong>{elapsed_time}</strong>'
            print(f'<td class="st_extra">{elapsed_time}</th>', file=f)
        for prob_res, prob_time, open_time, problem_opener in zip(self.problem_results, self.problem_times, open_times, problem_openers):
            background = ''
            if len(prob_res) > 0:
                if prob_res[0] == '+':
                    background = '#e0ffe0'
                    if (problem_opener == '' and prob_time == open_time) or self.name == problem_opener:
                        background = '#b0ffb0'
                elif prob_res[0] == '-':
                    background = '#ffd0d0'
                elif prob_res[0] == '?':
                    background = '#fcffaa'
            if background != '':
                background = 'background: ' + background
            print('<td style="{}" class="st_prob">{}'.format(background, prob_res, prob_time), end='', file=f)
            if prob_time != '':
                print('<div class="st_time">{}</div>'.format(prob_time), end='', file=f)
            print('</td>', file=f)
        print('<td class="st_total"><input style="width: 100%; outline: none; border:none" readonly type="text" value={}></input></td>'.format(self.total), file=f)
        print('<td class="st_pen"><input style="width: 100%; outline: none; border:none" readonly type="text" value={}></input></td>'.format(self.penalty), file=f)
        print('<td class="st_pen"><input style="width: 100%; outline: none; border:none" readonly type="text" value={:.2f}></input></td>'.format(self.get_dirt()), file=f)
        if max_itmo_rating:
            if place != '-':
                itmo_rating = get_rating_itmo(max_itmo_rating, self.solved_problems(), place, max_solved_problems, cnt_official_teams)
            else:
                itmo_rating = ''
            if itmo_rating =='':
                print('<td class="st_pen"><input style="width: 100%; outline: none; border:none" readonly type="text"></input></td>', file=f)
            else:
                print('<td class="st_pen"><input style="width: 100%; outline: none; border:none" readonly type="text" value={:.2f}></input></td>'.format(itmo_rating), file=f)
        #print('<td  class="st_total">{}</td>'.format(self.total), file=f)
        #print('<td  class="st_pen">{}</td>'.format(self.penalty), file=f)
        #print('<td  class="st_pen">{:.2f}</td>'.format(self.get_dirt()), file=f)
        print('</tr>', file=f)
        print(file=f)


class Standings:
    def __init__(self, show_regions, ignore_regions):
        self.show_regions = show_regions
        self.ignore_regions = ignore_regions
        self.all_results = []
        self.problem_openers = None
        
    def set_problem_openers(self, problem_openers):
        self.problem_openers = problem_openers
    
    def add(self, result):
        self.all_results.append(result)
        
    def sort(self):
        self.all_results = sorted(self.all_results)
    
    def get_total(self):
        total = [0] * problems
        for res in self.all_results:
            for num, prob_res in enumerate(res.problem_results):
                if len(prob_res) == 0:
                    continue
                if prob_res[0] == '+':
                    total[num] += 1
                    if len(prob_res) > 1:
                        total[num] += int(prob_res[1:])
                elif prob_res[0] == '-' or prob_res[0] == '?':
                    total[num] += int(prob_res[1:])
        total.append(sum(total))
        return total
    
    def get_ok(self):
        total = [0] * problems
        for res in self.all_results:
            for num, prob_res in enumerate(res.problem_results):
                if len(prob_res) == 0:
                    continue
                if prob_res[0] == '+':
                    total[num] += 1
        total.append(sum(total))
        return total
        
    def write_stats(self, f=sys.stdout):
        print('<tr class="submissions_statistic">', file=f)
        print('<td class="st_place"><output style="color: transparent">{}</output></td>'.format(max_length_place), file=f)
        print('<td class="st_team">Submissions:</td>', file=f)
        print('<td class="st_extra">&nbsp;</td>', file=f)
        if 'path_to_virtual_time' in globals():
            print('<td class="st_extra">&nbsp;</td>', file=f)
        for problem_id, x in enumerate(self.get_total()):
            print('<td title="{}" class="st_prob">{}</td>'.format(get_problem_title(problem_id), x), file=f)
        print('<td class="st_pen"><output style="color: transparent">9999</output></td>', file=f)
        print('<td class="st_pen"><output style="color: transparent">0.99</output></td>', file=f)
        if max_itmo_rating:
            print('<td class="st_pen"><output style="color: transparent">200.00</output></td>', file=f)
        print('</tr>', file=f)
        
        print('<tr class="submissions_statistic">', file=f)
        print('<td class="st_place"></td>', file=f)
        print('<td class="st_team">Accepted:</td>', file=f)
        print('<td class="st_extra">&nbsp;</td>', file=f)
        if 'path_to_virtual_time' in globals():
            print('<td class="st_extra">&nbsp;</td>', file=f)
        for problem_id, x in enumerate(self.get_ok()):
            print('<td title="{}" class="st_prob">{}</td>'.format(get_problem_title(problem_id), x), file=f)
        print('<td class="st_team">&nbsp;</td>', file=f)
        print('<td class="st_team">&nbsp;</td>', file=f)
        if max_itmo_rating:
            print('<td class="st_team">&nbsp;</td>', file=f)
        print('</tr>', file=f)
        
        print('<tr class="submissions_statistic">', file=f)
        print('<td class="st_place">&nbsp;</td>', file=f)
        print('<td class="st_team">%:</td>', file=f)
        print('<td class="st_extra">&nbsp;</td>', file=f)
        if 'path_to_virtual_time' in globals():
            print('<td class="st_extra">&nbsp;</td>', file=f)
        for problem_id, (total, ok) in enumerate(zip(self.get_total(), self.get_ok())):
            perc = 0
            if total > 0:
                perc = 100 * ok / total
            print('<td title="{}" class="st_prob">{:.0f}%</td>'.format(get_problem_title(problem_id), perc), file=f)
        print('<td class="st_team">&nbsp;</td>', file=f)
        print('<td class="st_team">&nbsp;</td>', file=f)
        if max_itmo_rating:
            print('<td class="st_team">&nbsp;</td>', file=f)
        print('</tr>', file=f)
        
    def get_region_statistic(self, region):
        teams = 0
        problems_solved = 0
        sum_place = 0
        solved_by_twentiest_team = 0
        for place, result in enumerate(self.all_results):
            if result.region == region or region == 'All':
                teams += 1
                if teams <= statistic_team_number:
                    problems_solved += result.total
                    sum_place += place + 1
                if teams <= statistic_team_number:
                    solved_by_twentiest_team = result.total
        denominator = max(1, min(statistic_team_number, teams))
        return region, teams, problems_solved / denominator, sum_place / denominator, solved_by_twentiest_team
        
    def write_regions(self, f):
        print('''<table class="region_statistic" width="50%"> <tr> <th>Show</th> <th>{}</th><th>Teams</th> <th>Average problems solved by top {} teams</th> <th>Average place taken by top {} teams</th> <th>Problems solved by {}<sup>th</sup> team </th> </tr>'''.format(region_column_name, statistic_team_number, statistic_team_number, statistic_team_number), file=f)
        regions = set()
        for result in self.all_results:
            regions.add(result.region)
        all_regions = []
        all_teams = 0
        for region in regions:
            all_regions.append(self.get_region_statistic(region))
        all_regions = sorted(all_regions, key=lambda region: (region[3], -region[2], -region[4], -region[1], region[0]))
        all_regions.append(self.get_region_statistic('All'))
        for region in all_regions:
            if region[0] == '':
                pass
                #continue
            print('<tr class="row_region">', file=f)
            if region[0] == 'All':
                print('<td class="st_region" id="region_all" align="center"> <input type="checkbox" checked onchange="checkAll()"> </input> </td>', file=f)
            else:
                print('<td class="st_region" align="center"> <input type="checkbox" checked onchange="filter()"> </input> </td>', file=f)
            updated_region = region[0]
            region_align = 'center'
            if show_flags:
                updated_region = update_region_with_flag(updated_region, 'country_flag_medium')
                region_align = 'left'
            print(f'<td class="st_region" align="{region_align}">{updated_region}</td>', file=f)
            print('<td class="st_region" align="center">{}</td>'.format(region[1]), file=f)
            print('<td class="st_region" align="center">{:.1f}</td>'.format(region[2]), file=f)
            print('<td class="st_region" align="center">{:.1f}</td>'.format(region[3]), file=f)
            print('<td class="st_region" align="center">{}</td>'.format(region[4]), file=f)
            print('</tr>', file=f)
        print('</table>', file=f)

    def get_places(self):
        places = []
        real_place = 0
        cur_res = 0
        while cur_res < len(self.all_results):
            start_real_place = real_place
            cur = cur_res
            while cur < len(self.all_results) and (self.all_results[cur].region in self.ignore_regions or (self.all_results[cur].total == self.all_results[cur_res].total and self.all_results[cur].penalty == self.all_results[cur_res].penalty)):
                if self.all_results[cur].region not in self.ignore_regions:
                    real_place += 1
                cur += 1
            place = str(start_real_place + 1)
            if start_real_place + 1 != real_place:
                place += '-' + str(real_place)
            for i in range(cur_res, cur):
                places.append(place)
            cur_res = cur
        return places, real_place

    def write(self, f=sys.stdout):
        if True:
            print('<link rel="stylesheet" href="{}styles/unpriv.css" type="text/css" />'.format(path_to_scripts), file=f)
            print('<link rel="stylesheet" href="{}styles/unpriv3.css" type="text/css" />'.format(path_to_scripts), file=f)
            print('<link rel="stylesheet" href="{}styles/animate.css" type="text/css" />'.format(path_to_scripts), file=f)
            print('<link rel="stylesheet" href="{}styles/styles.css" type="text/css" />'.format(path_to_scripts), file=f)
            print('<link rel="stylesheet" href="{}styles/cf_styles.css" type="text/css" />'.format(path_to_scripts), file=f)
            print('<link rel="stylesheet" href="{}styles/atcoder_styles.css" type="text/css" />'.format(path_to_scripts), file=f)
            print('<style id="styles"> table.standings td { height: 40px; } </style>', file=f)
        else:
            print('<link rel="stylesheet" href="http://ejudge.khai.edu/ejudge/unpriv.css" type="text/css" />', file=f)
            print('<link rel="stylesheet" href="http://ejudge.khai.edu/ejudge/unpriv3.css" type="text/css" />', file=f)
        print('<body onload="updateSliderFill(); loadResults();">', file=f)
        print('<script type="text/javascript" src="{}scripts/jquery.js"> </script>'.format(path_to_scripts), file=f)
        print('<script type="text/javascript" src="{}scripts/filter_regions.js"> </script>'.format(path_to_scripts), file=f)
        print('<script type="text/javascript" src="{}scripts/animate.js"> </script>'.format(path_to_scripts), file=f)
        print('<script type="text/javascript" src="{}scripts/parse_submissions.js"> </script>'.format(path_to_scripts), file=f)
        print('<div id="main-cont">', file=f)
        print('<div id="container">', file=f)
        print(standings_title, file=f)
        print('<div id="l13">', file=f)
        print('<div class="l14" id="contestTable" />', file=f)
        if self.show_regions:
            self.write_regions(f)
        
        #contest managing
        show_ranking_col = ''
        if len(show_oj_rating):
            show_ranking_col = '<th>Show Ranking</th>'
        print(f'<table class="region_statistic" width="50%"> <tr> <th> Start time </th> <th> Contest speed </th> <th>Penalty for wrong submission</th> <th> Start the contest </th> <th> Finish the contest </th> <th> Suspend the contest </th> {show_ranking_col}</tr>', file=f)
        print('<tr>', file=f)
        print('<td class="st_region" align="center"> <input type="text" id="contest_start_time" value="0:00:00" maxlength=7 style="width:100%"> </input> </td>', file=f)
        print('<td class="st_region" align="center"> <input type="range" id="contest_speed" min="1" max="60" value="1"> </input> </td>', file=f)
        print('<td class="st_region" align="center"> <input style="width: 50px" type="number" id="penalty_points" min="1" max="20" value="{}"> </input> </td>'.format(penalty_points), file=f)
        print('<td class="st_region" align="center"> <button onclick=go()> Start </button> </td>', file=f)
        print('<td class="st_region" align="center"> <button disabled="true" onclick=finish()> Finish </button> </td>', file=f)
        print('<td class="st_region" align="center"> <button disabled="true" id="pause" onclick=pause()>Pause</button> </td>', file=f)
        if len(show_oj_rating):
            print('<td class="st_region" align="center"> <select id="show_ranking_select" onchange=updateTeamRating()>', file=f)
            print('\n'.join([f'<option>{option_name}</option>' for option_name in show_oj_rating + ['None']]), file=f)
            print('</td>', file=f)
        print('</tr>', file=f)
        print('</table>', file=f)

        slider_value = globals().get('contest_live_time', contest_duration)
        print('<center style="font-size: 25px" id="standings_time"> Standings [{}] </center>'.format(get_time_str(slider_value)), file=f)

        print('<input type="range" min="0" max="{}" value="{}" class="slider" id="slider" oninput="updateSliderFill()" onchange="updateSliderFill()" onmousedown="sliderMouseDown()" onmouseup="sliderMouseUp()">'.format(contest_duration, slider_value), file=f)
        
        print('<table style="border-collapse: separate; border-spacing: 1px;" width="100%" class="standings">', file=f)
        print('<tr>', file=f)
        print('<th class="st_place">{}</th>'.format('Place'), file=f)
        print('<th class="st_team" style="min-width: 185px">{}</th>'.format('User'), file=f)
        print('<th class="st_extra">{}</th>'.format(region_column_name), file=f)
        elapsed_times = None
        if 'path_to_virtual_time' in globals():
            elapsed_times = json.load(open(globals()['path_to_virtual_time'], encoding='utf-8'))
            print('<th class="st_extra">Time</th>', file=f)
        for prob_id in range(problems):
            print('<th title="{}" class="st_prob" style="min-width: 32px">{}</th>'.format(get_problem_title(prob_id), problem_ids[prob_id]), file=f)
        print('<th  class="st_total">{}</th>'.format('Total'), file=f)
        print('<th  class="st_pen">{}</th>'.format('Penalty'), file=f)
        print('<th  class="st_pen">{}</th>'.format('Dirt'), file=f)
        if max_itmo_rating:
            print('<th  class="st_pen">{}</th>'.format('Rating'), file=f)
        print('</tr>', file=f)
        open_times = ['(9:99)' for i in range(problems)]
        for place, result in enumerate(self.all_results):
            num = 0
            for prob_res, prob_time in zip(result.problem_results, result.problem_times):
                if len(prob_res) > 0 and prob_res[0] == '+':
                    open_times[num] = min(open_times[num], prob_time)
                num += 1
        places, cnt_official_teams = self.get_places()
        place = 0
        max_solved_problems = 0
        for place, result in zip(places, self.all_results):
            if result.region not in self.ignore_regions:
                max_solved_problems = result.solved_problems()
                break
        text_to_copy = ''
        for place, result in zip(places, self.all_results):
            if result.region in self.ignore_regions:
                result.write('-', open_times, self.problem_openers, max_solved_problems, cnt_official_teams, f, elapsed_times)
            else:
                result.write(place, open_times, self.problem_openers, max_solved_problems, cnt_official_teams, f, elapsed_times)
                text_to_copy += f'{result.region}\t{result.name}\t{result.total}\t{result.penalty}\n'
            if True:
                num = 0
                for prob_res, prob_time in zip(result.problem_results, result.problem_times):
                    if len(prob_res) > 0 and prob_res[0] == '+' and open_times[num] == prob_time:
                        open_times[num] = '(9:99)'
                    num += 1
        if 'copy_to_compare' in globals():
            pyperclip.copy(text_to_copy)
        self.write_stats(f)
        print('</table>', file=f)
        print('</div>', file=f)
        print('<div id="footer" style="text-align: center; margin-bottom: 5px"></div>', file=f)
        print('<script type="text/javascript" src="{}scripts/footer.js" onload="loadFooter()"></script>'.format(path_to_scripts), file=f)
        print('</div>', file=f)
        print('</div>', file=f)
        print('</div>', file=f)


def process(content, region):
    text = codecs.decode(content, 'utf-8-sig')
    pos = text.find('class="standings"')
    pos += len('class="standings"')
    pos = text.find('<tr', pos) + 1
    region_column_exist = region == '' and text[pos:pos + 100].find('"st_extra">Region') != -1
    has_time = text[pos:pos + 2000].find('st_time') != -1
    print(has_time)
    while True:
        pos = text.find('<tr', pos)
        if pos == -1:
            break
        place, pos = get_value(text, '"st_place">', pos)
        team, pos = get_value(text, '"st_team">', pos)
        real_region = region
        if team[0] == 'П':
            real_region = 'School'
        if team[:4] == 'team' and len(team) == 6 and (69 <= int(team[4:]) <= 89):
            real_region = 'School'
        if team in team_names:
            team = team_names[team]
        if not is_digit(place[0]) and place[0] != '-':
            break
        if region_column_exist:
            real_region, pos = get_value(text, '"st_extra">', pos)
        if real_region != 'School' and team[0] == 's':
            real_region = 'School'
        if real_region == '':
            real_region = 'School'
        if real_region == 'South-Eastern': # only for 2018 stage 2
            real_region = 'SouthWest'
        #real_region = ''
        problem_results = []
        problem_times = []
        for prob_id in range(problems):
            prob_res, pos = get_value(text, '"st_prob">', pos)
            prob_res = prob_res.replace(' ', '')
            prob_time = ''
            if prob_res[0] == '+':
                if has_time:
                    prob_time, pos = get_value(text, '"st_time">', pos)
                else:
                    prob_time = '(0:00)'
                    try_look = (team.replace(' ', '&sp&', 1000000000), prob_id)
                    if try_look in all_successful_submits:
                        prob_time = all_successful_submits[try_look]
            problem_results.append(prob_res)
            problem_times.append(prob_time)
        total, pos = get_value(text, '"st_total">', pos)
        penalty, pos = get_value(text, '"st_pen">', pos)
        team_res = Result(team, real_region, problem_results, problem_times, total, penalty)
        if team_res.try_problems() == 0:
            continue
        standings.add(team_res)


def get_penalty_by_time(t):
    return int(t[1]) * 60 + int(t[3:5])


def starts_with(s, t):
    return s[:len(t)] == t


def get_unofficial_teams(path):
    f = open(path, 'r')
    teams = f.read().split('\n')
    return {team for team in teams}


def update_region_with_flag(region, img_class):
    flags = {
        'Ukraine': 'ua.png',
        'Romania': 'ro.png',
        'North Macedonia': 'mk.png',
        'Serbia': 'rs.png',
        'Turkey': 'tr.png',
        'Cyprus': 'cy.png',
        'Bulgaria': 'bg.png',
        'Greece': 'gr.png',
        'Moldova': 'md.png'
    }
    if region in flags:
        img_height = 8 if img_class == 'country_flag_small' else 9.5
        return f'<img height="{img_height}" src="{path_to_scripts}images/flags/{flags[region]}" alt="{region}" class="{img_class}">&nbsp;&nbsp;{region}'
    return region


unofficial_teams = []
if path_to_unofficial_teams != '':
    unofficial_teams = get_unofficial_teams(path_to_unofficial_teams)
if path_to_team_regions != '':
    team_regions_add = json.load(open(path_to_team_regions, 'r', encoding='utf8'))
    for team, region in team_regions_add.items():
        team_regions[team] = region
        team_regions[team.replace(' ', '&sp&')] = region
    for team, update_team in team_members.items():
        if team.replace('&sp&', ' ') in team_regions:
            team = team.replace('&sp&', ' ')
        if team in team_regions:
            team_regions[update_team] = team_regions[team]
standings_title = '<p align="center" style="font-family: times-new-roman"> \
    <a style="position: absolute; left: 0; margin: 13px; padding-left: 7px" href="{}"> <img width="30px" src="{}images/back_arrow.png"></a> \
    <font size="7"> {} </font> </p> <p align="center" style="font-family: times-new-roman"> <font size="7"> {} </font> </p>'.format(back_arrow_leads_to, path_to_scripts, olympiad_title, olympiad_date)
standings = Standings(show_regions=show_regions, ignore_regions=ignore_regions)
if len(csv_files) == 0:
    for link, region in links:
        print('Processing {}'.format(link))
        r = requests.post(link)
        process(r.content, region)
else:
    team_regions['GeorgianSU'] = 'Georgia'
    res_team_regions = dict()
    all_teams = {x[0] for x in all_status}
    for x in all_successful_submits:
        all_teams.add(x[0])
    for team in all_teams:
        if team.lower() == 'nan' or starts_with(team, 'ejudge'):
            continue
        results = []
        times = []
        solved = 0
        penalty = 0
        for prob_id in range(problems):
            p = (team, prob_id)
            if p in all_status or p in all_successful_submits:
                if p in all_successful_submits:
                    result = '+'
                    if p in all_status:
                        result += str(all_status[p])
                        penalty += penalty_points * all_status[p]
                    results.append(result)
                    times.append(all_successful_submits[p])
                    solved += 1
                    penalty += get_penalty_by_time(all_successful_submits[p])
                elif p in all_frozen:
                    results.append('?' + str(all_frozen[p][1]))
                    times.append(all_frozen[p][0])
                else:
                    results.append('-' + str(all_status[p]))
                    times.append('')
            else:
                results.append('')
                times.append('')
        region = 'Ukraine'
        #print(team[:team.find('&sp&(')], team[:team.find('&sp&(')] in team_regions)
        if team in team_regions:
            region = team_regions[team]
        elif team.replace('&sp&', ' ') in team_regions:
            region = team_regions[team.replace('&sp&', ' ')]
        elif team[:team.find('&sp&(')] in team_regions:
            region = team_regions[team[:team.find('&sp&(')]]
        for word in []:
            if team.find(word) != -1:
                region = 'Other'
                break
        team_name = team.replace('&sp&', ' ')
        if team_name[:11] == '_____*Polit':
            continue
        if team_name in unofficial_teams:
            region = 'Unofficial'
        team_res = Result(team_name, region, results, times, solved, penalty, all_submissions[team])
        print(team_name, region)
        res_team_regions[team_name] = region
        standings.add(team_res)
    json.dump(res_team_regions, open('created_tables/dumped_team_regions.json', 'w'))
standings.set_problem_openers(problem_openers)
standings.sort()
standings.write(f)
print(problem_openers)
print(time_openers)
with open(f'created_tables/{standings_file_name}.pickle', 'wb') as wf:
    compressed_standings = CompressedStandings(standings, contest_duration, max_itmo_rating, olympiad_title, solved_problems_including_upsolving, day_number=globals().get('contest_stage'))
    pickle.dump(compressed_standings, wf)
