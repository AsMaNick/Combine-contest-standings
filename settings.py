olympiad_title = 'OCPC, Day 1, Kharkiv Contest'
contest_date = 'August 31, 2024'
problems = 13
problem_names = [
    'Easy Jump',
    'Terrible Additive Number Theory Problem',
    'Race',
    'Candy Machine',
    'The Profiteer',
    'BpbBppbpBB',
    'Dynamic Reachability',
    'Barbecue',
    'Easy Fix',
    'Rounding Master',
    'Resource Calculator',
    'Frog',
    'A=B'
]
problem_ids = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M']

statistic_team_number = 4
path_to_scripts = '../../../../../'
back_arrow_leads_to = '../'
ignore_regions = {'Unofficial'}
show_regions = True
olympiad_date = f'Osijek, Croatia, {contest_date}'
links = [('http://ejudge.khai.edu/ejudge/contest180421.html', 'East')]
region_column_name = 'Type'

round_time = 'UP'
contest_duration = 300
frozen_time = 300

penalty_points = 20
ignore_compilation_error = True
csv_files = ['div1.csv']
regions = ['Ukraine']
path_to_data = f'data/2024_osijek_fall/'
path_to_team_regions = f'{path_to_data}/regions.json' # empty string for ignore
path_to_team_members = '' # empty string for ignore
path_to_unofficial_teams = '' # empty string for ignore
standings_file_name = 'standings'
write_team_members = False
max_itmo_rating = 200 # 0 for no rating
show_oj_rating = ['AtCoder', 'CF'] # [] for no ranking
team_members_format = ['Team: A, B, C', 'Team (A, B, C)'][1]
path_to_oj_info = f'{path_to_data}/oj_info/oj_info.json' # empty string for ignore
show_flags = False
hide_problem_title = False
minutes_in_bin = 6
minutes_per_bin_label = 60
assert contest_duration % minutes_in_bin == 0
