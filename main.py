import requests
import json
import dis
import codecs
import sys
import os
from tqdm import tqdm

statistic_team_number = 10
path_to_scripts = '../../'
ignore_regions = {'School'}
show_regions = True
olympiad_title = 'All-Ukrainian Collegiate Programming Contest'
olympiad_date = '3<sup>rd</sup> Stage Ukraine, October 20, 2018'
links = [('http://ejudge.khai.edu/ejudge/contest180421.html', 'East'),
	('http://194.105.136.86/kyiv501.php', 'Kyiv'),
	#('http://olymp.franko.lviv.ua/', 'West'),
	('http://olimp.tnpu.edu.ua/standing2018/students.html', 'South-West'),
	('http://olimp.tnpu.edu.ua/standing2018/schools.html', 'School'),
	('http://194.105.136.86/center500.php', 'Center')
]
links = [('http://olymp.sumdu.edu.ua:8080/final2018.php', ''), 
	#('http://olymp.moippo.org.ua/standings/standings2104.html', 'South')
]

problems = 11
penalty_points = 20
max_length_place = '7771777'

f = open('created_tables/standings.html', 'w')
all_successful_submits = {}

if os.path.exists('runs.csv'):
	import pandas as pd

	print('<div id="submissionsLog"><!--', file=f)
	data = pd.read_csv('runs.csv', ';')
	all_status = {}
	for it, row in tqdm(data.iterrows()):
		user_name = str(row['User_Name']).replace(' ', '&sp&', 1000000000)
		if row['Prob'][0] == '!':
			print(it, row['Run_Id'], row['Prob'], user_name)
			continue
		prob_id = ord(row['Prob']) - ord('A')
		hour = row['Dur_Hour']
		minute = row['Dur_Min']
		second = row['Dur_Sec']
		if second != 0:
			minute += 1
			if minute == 60:
				hour += 1
				minute = 0
		time = '({}:{}{})'.format(hour, minute // 10, minute % 10)
		status = row['Stat_Short']
		if status == 'CE':
			continue
		p = (user_name, prob_id)
		wrong_attempts = 0
		if p in all_successful_submits:
			continue
		if p in all_status:
			wrong_attempts = all_status[p]
		if status == 'OK':
			result = '+'
			if wrong_attempts != 0:
				result += str(wrong_attempts)
			wrong_attempts = -1
			all_successful_submits[p] = time
			if p[0].find('Energy') != -1:
				print('#', p)
		else:
			wrong_attempts += 1
			result = '-' + str(wrong_attempts)
			all_status[p] = wrong_attempts
		print(user_name, prob_id, time, result, file=f)
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
	

class Result:
	def __init__(self, name, region, problem_results, problem_times, total, penalty):
		self.name = name
		self.problem_results = problem_results
		self.problem_times = problem_times
		self.total = int(total)
		self.penalty = int(penalty)
		self.region = region
		
	def __lt__(self, other):
		return self.total > other.total or (self.total == other.total and self.penalty < other.penalty)
		
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
		
	def write(self, place, open_times, f):
		print('<tr class="participant_result">', file=f)
		print('<td class="st_place"><input style="width: 100%; outline: none; border:none" readonly type="text" value={}></input></td>'.format(place), file=f)
		print('<td class="st_team">{}</td>'.format(self.name), file=f)
		print('<td class="st_extra">{}</td>'.format(self.region), file=f)
		for prob_res, prob_time, open_time in zip(self.problem_results, self.problem_times, open_times):
			background = ''
			if len(prob_res) > 0:
				if prob_res[0] == '+':
					background = '#e0ffe0'
					if prob_time == open_time:
						background = '#b0ffb0'
				elif prob_res[0] == '-':
					background = '#ffd0d0'
			if background != '':
				background = 'background: ' + background
			print('<td style="{}" class="st_prob">{}'.format(background, prob_res, prob_time), end='', file=f)
			if prob_time != '':
				print('<div class="st_time">{}</div>'.format(prob_time), end='', file=f)
			print('</td>', file=f)
		print('<td class="st_total"><input style="width: 100%; outline: none; border:none" readonly type="text" value={}></input></td>'.format(self.total), file=f)
		print('<td class="st_pen"><input style="width: 100%; outline: none; border:none" readonly type="text" value={}></input></td>'.format(self.penalty), file=f)
		print('<td class="st_pen"><input style="width: 100%; outline: none; border:none" readonly type="text" value={:.2f}></input></td>'.format(self.get_dirt()), file=f)
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
				elif prob_res[0] == '-':
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
		print('<td  class="st_place"><output style="color: transparent">{}</output></td>'.format(max_length_place), file=f)
		print('<td  class="st_team">Submissions:</td>', file=f)
		print('<td  class="st_team">&nbsp;</td>', file=f)
		for x in self.get_total():
			print('<td  class="st_prob">{}</td>'.format(x), file=f)
		print('<td  class="st_pen"><output style="color: transparent">9999</output></td>', file=f)
		print('<td  class="st_pen"><output style="color: transparent">0.99</output></td>', file=f)
		print('</tr>', file=f)
		
		print('<tr class="submissions_statistic">', file=f)
		print('<td  class="st_place"></td>', file=f)
		print('<td  class="st_team">Accepted:</td>', file=f)
		print('<td  class="st_team">&nbsp;</td>', file=f)
		for x in self.get_ok():
			print('<td  class="st_prob">{}</td>'.format(x), file=f)
		print('<td  class="st_team">&nbsp;</td>', file=f)
		print('<td  class="st_team">&nbsp;</td>', file=f)
		print('</tr>', file=f)
		
		print('<tr class="submissions_statistic">', file=f)
		print('<td  class="st_place">&nbsp;</td>', file=f)
		print('<td  class="st_team">%:</td>', file=f)
		print('<td  class="st_team">&nbsp;</td>', file=f)
		for total, ok in zip(self.get_total(), self.get_ok()):
			perc = 0
			if total > 0:
				perc = 100 * ok / total
			print('<td  class="st_prob">{:.0f}%</td>'.format(perc), file=f)
		print('<td  class="st_team">&nbsp;</td>', file=f)
		print('<td  class="st_team">&nbsp;</td>', file=f)
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
		return region, teams, problems_solved / min(statistic_team_number, teams), sum_place / min(statistic_team_number, teams), solved_by_twentiest_team
		
	def write_regions(self, f):
		print('''<table class="region_statistic" width="50%"> <tr> <th>Show</th> <th>Region</th><th>Teams</th> <th>Average problems solved by top {} teams</th> <th>Average place taken by top {} teams</th> <th>Problems solved by {}<sup>th</sup> team </th> </tr>'''.format(statistic_team_number, statistic_team_number, statistic_team_number), file=f)
		regions = set()
		for result in self.all_results:
			regions.add(result.region)
		all_regions = []
		all_teams = 0
		for region in regions:
			all_regions.append(self.get_region_statistic(region))
		all_regions = sorted(all_regions, key=lambda region: region[3])
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
			print('<td class="st_region" align="center">{}</td>'.format(region[0]), file=f)
			print('<td class="st_region" align="center">{}</td>'.format(region[1]), file=f)
			print('<td class="st_region" align="center">{:.1f}</td>'.format(region[2]), file=f)
			print('<td class="st_region" align="center">{:.1f}</td>'.format(region[3]), file=f)
			print('<td class="st_region" align="center">{}</td>'.format(region[4]), file=f)
			print('</tr>', file=f)
		print('</table>', file=f)
		
	def write(self, f=sys.stdout):
		if True:
			print('<link rel="stylesheet" href="{}styles/unpriv.css" type="text/css" />'.format(path_to_scripts), file=f)
			print('<link rel="stylesheet" href="{}styles/unpriv3.css" type="text/css" />'.format(path_to_scripts), file=f)
			print('<link rel="stylesheet" href="{}styles/animate.css" type="text/css" />'.format(path_to_scripts), file=f)
			print('<style id="styles"> table.standings td { height: 40px; } </style>', file=f)
		else:
			print('<link rel="stylesheet" href="http://ejudge.khai.edu/ejudge/unpriv.css" type="text/css" />', file=f)
			print('<link rel="stylesheet" href="http://ejudge.khai.edu/ejudge/unpriv3.css" type="text/css" />', file=f)
		print('<body onload=loadResults()>', file=f)
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
		print('<table class="region_statistic" width="50%"> <tr> <th> Start time </th> <th> Contest speed </th> <th>Penalty for wrong submission</th> <th> Start the contest </th> <th> Finish the contest </th> <th> Suspend the contest </th> </tr>', file=f)
		print('<tr>', file=f)
		print('<td class="st_region" align="center"> <input type="text" id="contest_start_time" value="0:00:00" maxlength=7 style="width:100%"> </input> </td>', file=f)
		print('<td class="st_region" align="center"> <input type="range" id="contest_speed" min="1" max="60" value="10"> </input> </td>', file=f)
		print('<td class="st_region" align="center"> <input style="width: 50px" type="number" id="penalty_points" min="1" max="20" value="{}"> </input> </td>'.format(penalty_points), file=f)
		print('<td class="st_region" align="center"> <button onclick=go()> Start </button> </td>', file=f)
		print('<td class="st_region" align="center"> <button onclick=finish()> Finish </button> </td>', file=f)
		print('<td class="st_region" align="center"> <button id="pause" onclick=pause()>Pause</button> </td>', file=f)
		print('</tr>', file=f)
		print('</table>', file=f)

		print('<center style="font-size: 25px" id="standings_time"> Standings [5:00:00] </center>', file=f)
		print('<table style="border-collapse: separate; border-spacing: 1px;" width="100%" class="standings">', file=f)
		print('<tr>', file=f)
		print('<th class="st_place">{}</th>'.format('Place'), file=f)
		print('<th class="st_team">{}</th>'.format('User'), file=f)
		print('<th class="st_extra">{}</th>'.format('Region'), file=f)
		for prob_id in range(problems):
			print('<th class="st_prob">{}</th>'.format(chr(ord('A') + prob_id)), file=f)
		print('<th  class="st_total">{}</th>'.format('Total'), file=f)
		print('<th  class="st_pen">{}</th>'.format('Penalty'), file=f)
		print('<th  class="st_pen">{}</th>'.format('Dirt'), file=f)
		print('</tr>', file=f)
		open_times = ['(9:99)' for i in range(problems)]
		for place, result in enumerate(self.all_results):
			num = 0
			for prob_res, prob_time in zip(result.problem_results, result.problem_times):
				if len(prob_res) > 0 and prob_res[0] == '+':
					open_times[num] = min(open_times[num], prob_time)
				num += 1
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
			
		place = 0
		for place, result in zip(places, self.all_results):
			if result.region in self.ignore_regions:			
				result.write('-', open_times, f)
			else:
				result.write(place, open_times, f)
			if True:
				num = 0
				for prob_res, prob_time in zip(result.problem_results, result.problem_times):
					if len(prob_res) > 0 and prob_res[0] == '+' and open_times[num] == prob_time:
						open_times[num] = '(9:99)'
					num += 1
		self.write_stats(f)
		print('</table>', file=f)
		print('</div>', file=f)
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
		

team_names = dict()


def get_team_names():
	f = open('replace.txt', 'r')
	for l in f:
		if len(l) == 0 or l[0] == '#':
			continue
		team, name = l.split()
		team_names[team] = name
	f.close()
	

def get_penalty_by_time(t):
	return int(t[1]) * 60 + int(t[3:5])
	
	
standings_title = '<p align="center" style="font-family: times-new-roman"> <font size="7"> {} </font> </p> <p align="center" style="font-family: times-new-roman"> <font size="7"> {} </font> </p>'.format(olympiad_title, olympiad_date)
get_team_names()
standings = Standings(show_regions=show_regions, ignore_regions=ignore_regions)
if not os.path.exists('runs.csv'):
	for link, region in links:
		print('Processing {}'.format(link))
		r = requests.post(link)
		process(r.content, region)
else:
	all_teams = {x[0] for x in all_status}
	for x in all_successful_submits:
		all_teams.add(x[0])
	for team in all_teams:
		if team.lower() == 'nan':
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
				else:
					results.append('-' + str(all_status[p]))
					times.append('')
			else:
				results.append('')
				times.append('')
		team_res = Result(team.replace('&sp&', ' '), '', results, times, solved, penalty)
		standings.add(team_res)
standings.sort()
standings.write(f)
