import json
import pickle
from utils import *
from collections import defaultdict
from camps_combiner_settings import *


def calculate_rating_itmo(max_itmo_rating, n_solved_problems, place, max_solved_problems, cnt_official_teams):
    if place == None:
        return 0
    return get_rating_itmo(max_itmo_rating, n_solved_problems, place, max_solved_problems, cnt_official_teams)


def get_day_number(title, day_number):
    if day_number is not None:
        return day_number
    pos = title.lower().find('day ')
    assert pos != -1
    pos += 4
    day = ''
    while pos < len(title) and title[pos].isdigit():
        day += title[pos]
        pos += 1
    return int(day)


class CompressedResult:
    def __init__(self, result, contest_duration, rating_itmo, is_official_team, solved_problems_including_upsolving):
        self.n_solved_problems = result.solved_problems()
        assert self.n_solved_problems == 0 or result.name in solved_problems_including_upsolving, result.name
        assert len(solved_problems_including_upsolving[result.name]) >= self.n_solved_problems
        self.n_upsolved_problems = len(solved_problems_including_upsolving[result.name]) - self.n_solved_problems
        freezing_time = contest_duration * 4 // 5
        freezing_time = f'({freezing_time // 60}:{freezing_time % 60:02d})'
        self.n_solved_problems_during_freezing = result.solved_problems_during_freezing(freezing_time)
        self.penalty = result.penalty
        self.dirt = result.get_dirt()
        self.region = result.region
        self.raw_name = result.name
        self.displayed_name, self.json_oj_info = result.get_name_with_oj_info()
        self.rating_itmo = rating_itmo
        self.is_official_team = is_official_team

    def get_info(self):
        return f'{self.n_solved_problems} {self.penalty} {self.n_solved_problems_during_freezing} {self.dirt:.2f} {self.n_upsolved_problems}'


class CompressedStandings:
    def __init__(self, standings, contest_duration, max_itmo_rating, title, solved_problems_including_upsolving, day_number=None):
        self.title = title
        self.day_number = get_day_number(title, day_number)
        self.n_problems = len(standings.problem_openers)
        places, cnt_official_teams = standings.get_places()
        official_results = [result.solved_problems() for result in standings.all_results if result.region not in standings.ignore_regions]
        max_solved_problems = max([0] + official_results)
        assert(cnt_official_teams == len(official_results))
        self.all_results = [CompressedResult(result, contest_duration, 
                                             calculate_rating_itmo(max_itmo_rating, result.solved_problems(), 
                                                                   place if result.region not in standings.ignore_regions else None,
                                                                   max_solved_problems, cnt_official_teams),
                                             result.region not in standings.ignore_regions,
                                             solved_problems_including_upsolving)
                            for place, result in zip(places, standings.all_results)]


class ParticipantResults:
    def __init__(self, n_standings):
        self.results = [None for _ in range(n_standings)]
        self.is_author = [None for _ in range(n_standings)]

    def add_result(self, num, result):
        assert self.results[num] is None, f'{num} {result.raw_name}'
        self.results[num] = result

    def set_is_author(self, num, info):
        self.is_author[num] = info

    def get_average_rating_itmo(self):
        ratings = [result.rating_itmo if result is not None else None for result, author in zip(self.results, self.is_author) if author is None]
        if len([rating for rating in ratings if rating is not None]) == 0:
            return 0
        if rating_averaging_method.startswith('avg'):
            ratings = [rating for rating in ratings if rating is not None]
            return sum(ratings) / len(ratings) if ratings else 0
        else:
            ratings = [rating if rating is not None else 0 for rating in ratings]
            ratings = list(reversed(sorted(ratings)))
            n_standings = len(ratings)
            if rating_averaging_method.startswith('except'):
                not_count = max(0, min(n_standings - 1, int(rating_averaging_method[6:])))
                ratings = ratings[:-not_count]
                return sum(ratings) / len(ratings) if ratings else 0
            elif rating_averaging_method.startswith('ucup'):
                k = float(rating_averaging_method[4:])
                assert 0 < k < 1
                pw = 1
                tot = 0
                for r in ratings:
                    tot += pw * r
                    pw *= k
                mx_coef = ((k ** n_standings) - 1) / (k - 1)
                return tot / mx_coef
        raise KeyError(rating_averaging_method)

    def get_average_dirt(self):
        dirts = [result.dirt for result in self.results if result is not None]
        return sum(dirts) / len(dirts) if dirts else 0

    def get_total_solved(self):
        solved = [result.n_solved_problems for result in self.results if result is not None]
        return sum(solved)

    def get_total_upsolved(self):
        solved = [result.n_upsolved_problems for result in self.results if result is not None]
        return sum(solved)

    def get_average_solved_during_freezing(self):
        solved = [result.n_solved_problems_during_freezing for result in self.results if result is not None]
        return sum(solved) / len(solved) if solved else 0

    def get_rating_itmo_at(self, i):
        if self.is_author[i] is not None:
            return self.is_author[i]
        return f'{self.results[i].rating_itmo:.2f}' if self.results[i] is not None else '-'

    def get_comparator_key(self):
        return self.get_average_rating_itmo(), self.get_total_solved(), self.get_total_upsolved(), self.get_average_solved_during_freezing(), -self.get_average_dirt()

    def __lt__(self, other):
        return self.get_comparator_key() > other.get_comparator_key()

    def __eq__(self, other):
        return self.get_comparator_key() == other.get_comparator_key()

    def is_official_team(self):
        status = [result.is_official_team for result in self.results if result is not None]
        return max(status) if status else False


def load_standings(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)


def get_places(all_results, consider_all_official=False):
    pos = 0
    places = []
    offical_place = 0
    while pos < len(all_results):
        start_pos = pos
        start_offical_place = offical_place
        while pos < len(all_results) and f'{all_results[start_pos][0].get_average_rating_itmo():.2f}' == f'{all_results[pos][0].get_average_rating_itmo():.2f}':
            offical_place += consider_all_official or all_results[pos][0].is_official_team()
            pos += 1
        for i in range(start_pos, pos):
            if consider_all_official or all_results[i][0].is_official_team():
                if pos == start_pos + 1:
                    places.append(f'{start_offical_place + 1}')
                else:
                    places.append(f'{start_offical_place + 1}-{offical_place}')
            else:
                places.append('-')
    return places


def calculate_regions_stats(all_standings, all_results, statistic_team_number):
    places = get_places(all_results, consider_all_official=True)
    results_by_region = defaultdict(list)
    for place, (results, raw_name) in zip(places, all_results):
        some_result = [result for result in results.results if result is not None][0]
        region = some_result.region
        if place.find('-') != -1:
            place = int(place[:place.find('-')])
        else:
            place = int(place)
        for upd_region in ['All', region]:
            results_by_region[upd_region].append((
                 results.get_average_rating_itmo(),
                 place,
                 results.get_average_solved_during_freezing()
            ))
    stats_by_region = dict()
    for region, results in results_by_region.items():
        results.sort(reverse=True)
        n_teams = len(results)
        results = results[:min(len(results), statistic_team_number)]
        stats = [0, 0, 0]
        for result in results:
            assert len(stats) == len(result)
            for i in range(len(stats)):
                stats[i] += result[i]
        if results:
            for i in range(len(stats)):
                stats[i] /= len(results)
        stats_by_region[region] = (n_teams,) + tuple(stats)
    all_stats = [(stats, region) for region, stats in stats_by_region.items() if region != 'All']
    all_stats.sort(reverse=True)
    all_stats = all_stats + [(stats_by_region['All'], 'All')]
    print(all_stats)
    return all_stats


def write_regions(f, region_column_name, statistic_team_number, stats_region, show_flags):
    print('''<table class="region_statistic" width="50%"> <tr>
<th>Show</th> 
<th>{}</th>
<th>Teams</th>
<th>Average rating of top {} teams</th>
<th>Average place taken by top {} teams</th>
<th>Average problems solved at freezing by top {} teams </th> </tr>'''.format(region_column_name, statistic_team_number, statistic_team_number, statistic_team_number), file=f)
    for stats, region in stats_region:
        print('<tr class="row_region">', file=f)
        if region == 'All':
            print('<td class="st_region" id="region_all" align="center"> <input type="checkbox" checked onchange="checkAll()"> </input> </td>', file=f)
        else:
            print('<td class="st_region" align="center"> <input type="checkbox" checked onchange="filter()"> </input> </td>', file=f)
        updated_region = region
        region_align = 'center'
        if show_flags:
            raise NotImplementedError()
            # updated_region = update_region_with_flag(updated_region, 9.5)
            region_align = 'left'
        print(f'<td class="st_region" align="{region_align}">{updated_region}</td>', file=f)
        print('<td class="st_region" align="center">{}</td>'.format(stats[0]), file=f)
        print('<td class="st_region" align="center">{:.2f}</td>'.format(stats[1]), file=f)
        print('<td class="st_region" align="center">{:.2f}</td>'.format(stats[2]), file=f)
        print('<td class="st_region" align="center">{:.2f}</td>'.format(stats[3]), file=f)
        print('</tr>', file=f)
    print('</table>', file=f)


def write_statistics_headers(f):
    def get_average_title():
        if rating_averaging_method.startswith('avg'):
            return '''Assuming that team participated in n contests and its ratings sorted in non-increasing order are r[0], r[1], ..., r[n - 1],
average rating is calculated as (sum r[i]) / n.'''
        elif rating_averaging_method.startswith('except'):
            not_count = int(rating_averaging_method[6:])
            return '''Assuming that there were n contests (not counting contests where the team was author or seen the problems before) and team ratings sorted in non-increasing order are r[0], r[1], ..., r[n - 1],
average rating is calculated as average number among max(1, n - 2) best ratings: (r[0] + r[1] + ... + r[max(0, n - 3)]) / max(1, n - 2).'''
        elif rating_averaging_method.startswith('ucup'):
            k = float(rating_averaging_method[4:])
            return f'''Assuming that there were n contests (not counting contests where the team was author or seen the problems before) and team ratings sorted in non-increasing order are r[0], r[1], ..., r[n - 1],
average rating is calculated as (sum r[i] * {k}^i) * (1 - {k}) / (1 - {k}^n).'''

    assert max_itmo_rating % 2 == 0
    rating_itmo_title = f'''Average rating ITMO calculated by the following formula for each contest:
{max_itmo_rating // 2} * A / B * (2n - 2) / (n + p - 2), where
A is the number of problems solved by the team,
B is the maximum number of problems solved by some team,
n is the number of teams that made at least one submission,
p is the place of the team.

{get_average_title()}'''
    solved_title = '''Total number of problems solved during contests'''
    upsolved_title = '''Total number of problems upsolved after contests'''
    freezing_title = '''Average number of problems solved during the last hour of the contest'''
    dirt_title = '''Average dirt parameter calculated by the following formula for each contest:
RJ / (RJ + AC), where
AC is the number of problems solved by the team,
RJ is the total number of rejected submissions before first AC for each problem'''
    print(f'<th title="{solved_title}" class="st_pen">Solved&nbspⓘ</th>', file=f)
    print(f'<th title="{freezing_title}" class="st_pen">Freezing&nbspⓘ</th>', file=f)
    print(f'<th title="{dirt_title}" class="st_pen">Dirt&nbspⓘ</th>', file=f)
    print(f'<th title="{rating_itmo_title}" class="st_total">Rating&nbspⓘ</th>', file=f)
    print(f'<th title="{upsolved_title}" class="st_pen">Upsolved&nbspⓘ</th>', file=f)


def get_needed_lengtehed_place(places):
    longest_place_len = max(len(place) for place in places)
    spaces = max(0, longest_place_len - 4)
    return '&nbsp;' * spaces + 'Place' + '&nbsp;' * spaces


def write(all_standings, all_results, filename, path_to_scripts, back_arrow_leads_to,
          camp_title, camp_dates, show_oj_rating, region_column_name, show_flags,
          statistic_team_number, max_itmo_rating):
    with open(filename, 'w', encoding='utf-8') as f:
        print('<div id="standingsSettings"><!--', file=f)
        print('contestDuration {}'.format(0), file=f)
        print('maxItmoRating {}'.format(max_itmo_rating), file=f)
        print('ratingAveragingMethod {}'.format(rating_averaging_method), file=f)
        print('--></div>', file=f)
        for styles_file in ['unpriv.css', 'unpriv3.css', 'animate.css', 'styles.css', 'cf_styles.css', 'atcoder_styles.css', 'summary_standings.css']:
            print(f'<link rel="stylesheet" href="{path_to_scripts}styles/{styles_file}" type="text/css" />', file=f)
        print('<style id="styles"> table.standings td { height: 40px; } </style>', file=f)
        print('<body onload="loadResults()">', file=f)
        for js_file in ['jquery.js', 'filter_regions.js', 'animate.js', 'parse_submissions.js']:
            print(f'<script type="text/javascript" src="{path_to_scripts}scripts/{js_file}"> </script>', file=f)
        print('<div id="main-cont">', file=f)
        print('<div id="container">', file=f)

        standings_title = '<p align="center" style="font-family: times-new-roman"> \
    <a style="position: absolute; left: 0; margin: 13px; padding-left: 7px" href="{}"> <img width="30px" src="{}images/back_arrow.png"></a> \
    <font size="7"> {} </font> </p> <p align="center" style="font-family: times-new-roman"> <font size="7"> {} </font> </p>'.format(back_arrow_leads_to, path_to_scripts, camp_title, camp_dates)
        print(standings_title, file=f)

        print('<div id="l13">', file=f)
        print('<div class="l14" id="contestTable" />', file=f)
        
        write_regions(f, region_column_name, statistic_team_number,
                      calculate_regions_stats(all_standings, all_results, statistic_team_number), show_flags)
        #contest managing
        show_ranking_col = ''
        if len(show_oj_rating):
            show_ranking_col = '<th>Show Ranking</th>'
        print(f'<table class="region_statistic" width="50%"> <tr> <th> Statistics to show </th> {show_ranking_col}</tr>', file=f)
        print('<tr>', file=f)
        print('<td class="st_region" align="center"> <select id="statistics_to_show_select" onchange=updateStatisticsToShow()>', file=f)
        print('\n'.join([f'<option{" selected" if option_name == "Rating" else ""}>{option_name}</option>' for option_name in ['Problems solved', 'Solved during freezing', 'Dirt', 'Rating', 'Problems upsolved']]), file=f)
        print('</td>', file=f)
        if len(show_oj_rating):
            print('<td class="st_region" align="center"> <select id="show_ranking_select" onchange=updateTeamRating()>', file=f)
            print('\n'.join([f'<option>{option_name}</option>' for option_name in show_oj_rating + ['None']]), file=f)
            print('</td>', file=f)
        print('</tr>', file=f)
        print('</table>', file=f)

        print('<center style="font-size: 25px" id="standings_time"> Combined standings </center>', file=f)

        print('<table style="border-collapse: separate; border-spacing: 1px;" width="100%" class="standings">', file=f)
        print('<tr>', file=f)
        places = get_places(all_results)
        print('<th class="st_place">{}</th>'.format(get_needed_lengtehed_place(places)), file=f)
        print('<th class="st_team" style="min-width: 300px">{}</th>'.format('User'), file=f)
        print('<th class="st_extra">{}</th>'.format(region_column_name), file=f)
        for contest_id in range(len(all_standings)):
            print(f'<th title="{all_standings[contest_id].title}" class="st_prob" style="min-width: 40px"><a href="../{get_folder_by_day_number(all_standings[contest_id].day_number)}/standings.html{day_link_suffix}" style="text-decoration: none; color: inherit">{day_header_name} {all_standings[contest_id].day_number}</a></th>', file=f)
        write_statistics_headers(f)
        for place, (results, raw_name) in zip(places, all_results):
            raw_names = [result.raw_name for result in results.results if result is not None]
            assert raw_names
            if min([result.raw_name == raw_names[0] for result in results.results if result is not None]) != True:
                print(f'Different raw names found: {sorted(list(set(raw_names)))}')
            some_result = [result for result in results.results if result is not None][-1]
            print('<tr class="participant_result">', file=f)
            print(f'<td class="st_place"><input style="width: 100%; outline: none; border:none" readonly type="text" value={place}></input></td>', file=f)
            json_with_oj_info_div = ''
            if len(show_oj_rating):
                json_with_oj_info_div = f'<div class="teamInfoJson"><!--{some_result.json_oj_info}--></div>'
            teamContestsLog = '<!--' + '\n'.join([f'{num} {result.get_info()}' for num, result in enumerate(results.results) if result is not None]) + '-->'
            print('<td class="st_team" title="{}"><div class="displayedTeamName">{}</div><div class="teamContestsLog">{}</div>{}</td>'.format('', some_result.displayed_name, teamContestsLog, json_with_oj_info_div), file=f)
            updated_region = some_result.region
            if show_flags:
                raise NotImplementedError()
                updated_region = update_region_with_flag(updated_region, 8)
            print(f'<td class="st_extra">{updated_region}</td>', file=f)
            for i in range(len(all_standings)):
                print('<td class="st_prob"><input style="width: 100%; outline: none; border:none" readonly type="text" value={}></input></td>'.format(results.get_rating_itmo_at(i)), file=f)
            print('<td class="st_total statistics_holder"><input style="width: 100%; outline: none; border:none" class="problems_solved_statistics" readonly type="text" value={}></input></td>'.format(results.get_total_solved()), file=f)
            print('<td class="st_pen statistics_holder"><input style="width: 100%; outline: none; border:none" class="solved_during_freezing_statistics" readonly type="text" value={:.2f}></input></td>'.format(results.get_average_solved_during_freezing()), file=f)
            print('<td class="st_pen statistics_holder"><input style="width: 100%; outline: none; border:none" class="dirt_statistics" readonly type="text" value={:.2f}></input></td>'.format(results.get_average_dirt()), file=f)
            print('<td class="st_pen statistics_holder"><input style="width: 100%; outline: none; border:none" class="rating_statistics main_statistics" readonly type="text" value={:.2f}></input></td>'.format(results.get_average_rating_itmo()), file=f)
            print('<td class="st_pen statistics_holder"><input style="width: 100%; outline: none; border:none" class="problems_upsolved_statistics" readonly type="text" value={}></input></td>'.format(results.get_total_upsolved()), file=f)
            
            print('</tr>', file=f)
        print('</tr>', file=f)
        print('</table>', file=f)
        print('</div>', file=f)
        print('<div id="footer" style="text-align: center; margin-bottom: 5px"></div>', file=f)
        print('<script type="text/javascript" src="{}scripts/footer.js" onload="loadFooter()"></script>'.format(path_to_scripts), file=f)
        print('</div>', file=f)
        print('</div>', file=f)
        print('</div>', file=f)


def extract_team_name(name):
    pos = name.rfind(' (')
    if pos == -1:
        print(f'Could not extract team name: {name}')
        return name
    return name[:pos]


def set_contest_authors():
    if path_to_contest_authors == '':
        return
    with open(path_to_contest_authors, 'r') as f:
        data = json.load(f)
        for author_info in data['authors']:
            results_by_participant[author_info['name']].set_is_author(author_info['contest_id'], author_info['status'])


if __name__ == '__main__':
    all_standings = [load_standings(filename) for filename in filenames]
    results_by_participant = defaultdict(lambda: ParticipantResults(len(all_standings)))
    for num, standings in enumerate(all_standings):
        for result in standings.all_results:
            results_by_participant[extract_team_name(result.displayed_name)].add_result(num, result)
    set_contest_authors()
    all_results = [(results, raw_name) for raw_name, results in results_by_participant.items()]
    all_results.sort()
    write(all_standings, all_results, 'created_tables/standings.html', path_to_scripts, back_arrow_leads_to,
          camp_title, camp_dates, show_oj_rating, region_column_name, show_flags,
          statistic_team_number, max_itmo_rating)
