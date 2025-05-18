def get_rating_itmo(max_itmo_rating, n_solved_problems, place, max_solved_problems, cnt_official_teams):
    assert isinstance(place, str)
    assert cnt_official_teams >= 1
    assert max_solved_problems >= n_solved_problems
    if n_solved_problems == 0:
        return 0.0
    if cnt_official_teams == 1:
        return max_itmo_rating
    if place.find('-') != -1:
        min_place = int(place[:place.find('-')])
    else:
        min_place = int(place)
    return 0.5 * max_itmo_rating * n_solved_problems / max_solved_problems * (2 * cnt_official_teams - 2) / (cnt_official_teams + min_place - 2)
