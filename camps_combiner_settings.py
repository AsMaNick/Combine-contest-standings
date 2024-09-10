def get_folder_by_day_number(day_number):
    return day_number


filenames = [
    f'data/2024_osijek_fall/standings/{i}.pickle' for i in [1, 2, 4, 5, 6, 8, 9]
]
path_to_scripts = '../../../../../'
back_arrow_leads_to = '../'
camp_title = 'Osijek Competitive Programming Camp, 2024 fall'
camp_dates = 'Osijek, Croatia, August 31 - September 8, 2024'
show_oj_rating = ['AtCoder', 'CF']
region_column_name = 'Type'
show_flags = False
statistic_team_number = 4
max_itmo_rating = 200
day_header_name = 'Day'
rating_averaging_method = ['avg', 'except2', 'ucup0.75'][2]
path_to_contest_authors = 'data/2024_osijek_fall/standings/contest_authors.json' # empty for no authors