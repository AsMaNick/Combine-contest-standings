var ok_regions, best_time, all_submissions, ok_submissions;
var place;

function removeFlagFromRegionName(region) {
    if (region.startsWith('<img')) {
        return region.substring(region.lastIndexOf('>&nbsp;') + 7);
    }
    return region;
}

function updateRegions(index, elem) {
    var checkbox = elem.getElementsByTagName('input')[0];
    if (checkbox.checked) {
        var region = removeFlagFromRegionName(elem.getElementsByClassName('st_region')[1].innerHTML);
        ok_regions.add(region);
    }
}

function getTime(elem) {
    if (elem == undefined) {
        return '(9:99)';
    }
    var tms = elem.getElementsByClassName('st_time');
    if (tms.length == 1) {
        return tms[0].innerHTML; 
    }
    return '(9:99)';
}

function getSubmissionResult(elem) {
    if (elem == undefined) {
        return '';
    }
    var res = elem.innerHTML;
    if (res.length > 0 && res[0] == '&') { // &nbsp;
        res = '';
    }
    if (res.indexOf('<') != -1) {
        res = res.substr(0, res.indexOf('<'));
    }
    return res; 
}

function myModify(index, elem) {
    elem.style = "";
    var region = removeFlagFromRegionName(elem.getElementsByClassName('st_extra')[0].innerHTML);
    if (ok_regions.has(region)) {
        elem.hidden = false;
        if (isSummaryStandings()) {
            return;
        }
        var place_elem = elem.getElementsByClassName('st_place')[0].getElementsByTagName('input')[0];
        if (place_elem.value != '-') {
            place += 1;
            place_elem.value = place;
        }
        var probs = elem.getElementsByClassName('st_prob');
        if (best_time == undefined) {
            problems = probs.length;
            best_time = new Array(problems);
            all_submissions = new Array(problems + 1);
            ok_submissions = new Array(problems + 1);
            percent_submissions = new Array(problems + 1);
            for (var i = 0; i < problems + 1; ++i) {
                all_submissions[i] = 0;
                ok_submissions[i] = 0;
            }
        }
        for (var i = 0; i < probs.length; ++i) {
            var prob_result = getSubmissionResult(probs[i]);
            if (prob_result != '') {
                if (prob_result[0] == '+') {
                    all_submissions[i] += 1;
                    ok_submissions[i] += 1;
                }
                if (prob_result.length > 1) {
                    all_submissions[i] += parseInt(prob_result.substr(1));
                }
            }
            var cur_tm = getTime(probs[i]);
            if (prob_result != '' && prob_result[0] == '+' && cur_tm < getTime(best_time[i])) {
                if (best_time[i] != undefined) {
                    best_time[i].style = 'background: #e0ffe0';
                }
                best_time[i] = probs[i];
                best_time[i].style = 'background: #b0ffb0';
            } else if (cur_tm != '(9:99)') {
                probs[i].style = 'background: #e0ffe0';
                if (prob_result != '' && prob_result[0] == '?') {
                    probs[i].style = 'background: #fcffaa';
                }
            }
        }
    } else {
        elem.hidden = true;
    }
}

function updateStatistic(elem, arr) {
    var elems = elem.getElementsByClassName('st_prob');
    for (var i = 0; i < elems.length; ++i) {
        elems[i].innerHTML = arr[i];
    }
}

function sort_summary_table_by_rating() {
    var table = document.getElementsByTagName('table')[2];
    var rows = table.getElementsByTagName('tr');
    var ratings = [];
    for (var i = 1; i < rows.length; ++i) {
        ratings.push([rows[i].getElementsByClassName('st_pen')[2].getElementsByTagName('input')[0].value, rows[i]]);
    }
    ratings.sort(function(a, b) {
        return b[0] - a[0];
    });
    for (var rating of ratings) {
        table.append(rating[1]);
    }
}

function calculateAverageRating(ratings, skipped_days) {
    if (ratings.length == 0) {
        return 0;
    }
    if ((rating_averaging_method === null) || rating_averaging_method == 'avg') {
        var tot = 0;
        for (var rating of ratings) {
            tot += rating;
        }
        return tot / ratings.length;
    } else {
        var n_standings = all_teams_elem[0].getElementsByClassName('st_prob').length;
        var sorted_ratings = ratings.slice();
        while (sorted_ratings.length + skipped_days < n_standings) {
            sorted_ratings.push(0);
        }
        n_standings = sorted_ratings.length;
        if (n_standings == 0) {
            return 0;
        }
        sorted_ratings = sorted_ratings.toSorted(function(a, b) { return a - b; } ).toReversed();
        if (rating_averaging_method.startsWith('except')) {
            var not_count = Math.max(0, Math.min(n_standings - 1, parseInt(rating_averaging_method.substring(6))));
            sorted_ratings = sorted_ratings.slice(0, sorted_ratings.length - not_count);
            var tot = 0;
            for (var rating of sorted_ratings) {
                tot += rating;
            }
            return tot / sorted_ratings.length;
        } else if (rating_averaging_method.startsWith('ucup')) {
            const k = parseFloat(rating_averaging_method.substring(4));
            const mx_coef = (Math.pow(k, n_standings) - 1) / (k - 1);
            var pw = 1, tot = 0;
            for (var r of sorted_ratings) {
                tot += pw * r;
                pw *= k;
            }
            return tot / mx_coef;
        }
    }
    return 0;
}

function fillSummaryDayInfo(info_to_show) {
    var id_to_show = ["Problems solved", "Rating", "Solved during freezing", "Dirt", "Problems upsolved"].indexOf(info_to_show);
    if (info_to_show == "Rating") {
        const n_days = all_teams_elem[0].getElementsByClassName('st_prob').length;
        var ratings_by_id = new Array(all_teams_elem.length);
        for (var i = 0; i < ratings_by_id.length; ++i) {
            ratings_by_id[i] = [];
        }
        for (var day = 0; day < n_days; ++day) {
            var max_solved_problems = 0, all_results = [];
            for (var i = 0; i < all_teams_elem.length; ++i) {
                if (all_teams_elem[i].hidden) {
                    continue;
                }
                if (all_place_elem[i].value != '-') {
                    var log = all_teams_elem[i].getElementsByClassName('teamContestsLog')[0].innerHTML;
                    log = log.replace('<!--', '').replace('-->', '');
                    var days_info = log.split('\n');
                    var problems_solved = -1, penalty = -1;
                    for (var day_info of days_info) {
                        var data = day_info.split(' ');
                        if (data[0] == day) {
                            problems_solved = data[1];
                            penalty = data[2];
                            break;
                        }
                    }
                    if (problems_solved != -1) {
                        max_solved_problems = Math.max(max_solved_problems, problems_solved);
                        var cur_result = new Result(i);
                        cur_result.total = parseInt(problems_solved);
                        cur_result.penalty = parseInt(penalty);
                        all_results.push(cur_result);
                    }
                } else {
                    var days = all_teams_elem[i].getElementsByClassName('st_prob');
                    if (days[day].getElementsByTagName('input')[0].value != '-') {
                        days[day].getElementsByTagName('input')[0].value = '0.00';
                    }
                }
                max_solved_problems = Math.max(max_solved_problems);
            }
            all_results.sort(compareResultByTotal);
            var places = getPlaces(all_results);
            for (var i = 0; i < all_results.length; ++i) {
                var rating_itmo = calculateRatingITMO(max_solved_problems, all_results.length, places[i], all_results[i].total);
                var days = all_teams_elem[all_results[i].id].getElementsByClassName('st_prob');
                days[day].getElementsByTagName('input')[0].value = rating_itmo.toFixed(2);
                ratings_by_id[all_results[i].id].push(rating_itmo);
            }
        }
        for (var i = 0; i < all_teams_elem.length; ++i) {
            if (all_teams_elem[i].hidden) {
                continue;
            }
            var skipped_days = 0;
            const days = all_teams_elem[i].getElementsByClassName('st_prob');
            for (var day = 0; day < days.length; ++day) {
                const stats_value = days[day].getElementsByTagName('input')[0].value;
                skipped_days += (stats_value == 'K' || stats_value == 'A');
            }
            all_rating_elem[i].value = calculateAverageRating(ratings_by_id[i], skipped_days).toFixed(2);
        }
        sort_summary_table_by_rating();
    } else {
        for (var i = 0; i < all_teams_elem.length; ++i) {
            var days = all_teams_elem[i].getElementsByClassName('st_prob');
            var log = all_teams_elem[i].getElementsByClassName('teamContestsLog')[0].innerHTML;
            log = log.replace('<!--', '').replace('-->', '');
            var days_info = log.split('\n');
            for (var day_info of days_info) {
                var data = day_info.split(' ');
                days[parseInt(data[0])].getElementsByTagName('input')[0].value = data[1 + id_to_show];
            }
        }
    }
}

function updateStatisticsToShow() {
    var statistics_to_show = $("#statistics_to_show_select option:selected").val();
    fillSummaryDayInfo(statistics_to_show);
    $(".main_statistics").removeClass("main_statistics");
    $("." + statistics_to_show.toLowerCase().replaceAll(' ', '_') + "_statistics").addClass("main_statistics");
}

function recalculateSummarizedRatingITMO() {
    fillSummaryDayInfo('Rating');
    loadResults();
}

function recalculateRatingITMO() {
    loadStandingsSettings();
    if (isSummaryStandings()) {
        recalculateSummarizedRatingITMO();
        return;
    }
    var max_solved_problems = 0, cnt_official_teams = 0;
    for (var i = 0; i < all_teams_elem.length; ++i) {
        if (all_teams_elem[i].hidden) {
            continue;
        }
        if (all_place_elem[i].value != '-') {
            ++cnt_official_teams;
            var problems_solved = parseInt(all_total_elem[i].value);
            max_solved_problems = Math.max(max_solved_problems, problems_solved);
        }
    }
    for (var i = 0; i < all_teams_elem.length; ++i) {
        if (all_teams_elem[i].hidden) {
            continue;
        }
        if (all_place_elem[i].value != '-') {
            var problems_solved = parseInt(all_total_elem[i].value);
            var rating_itmo = calculateRatingITMO(max_solved_problems, cnt_official_teams, all_place_elem[i].value, problems_solved);
            updateRating(i, rating_itmo.toFixed(2));
        }
    }
}

function filter(call_fill_places) {
    if (!loaded) {
        return;
    }
    best_time = undefined;
    all_submissions = undefined;
    ok_submissions = undefined;
    percent_submissions = undefined;
    ok_regions = new Set();
    $(".row_region").each(updateRegions);
    place = 0;
    $(".participant_result").each(myModify);
    recalculateRatingITMO();
    if (isSummaryStandings()) {
        updateStatisticsToShow();
    }
    var all_results = new Array();
    for (var i = 0; i < all_teams_elem.length; ++i) {
        if (all_teams_elem[i].hidden) {
            continue;
        }
        var cur_result = new Result(i);
        cur_result.total = parseInt(all_total_elem[i].value);
        cur_result.penalty = parseInt(all_penalty_elem[i].value);
        if (isSummaryStandings()) {
            cur_result.total = parseInt(parseFloat(all_rating_elem[i].value) * 100);
            cur_result.penalty = 0;
        }
        all_results.push(cur_result);
    }
    var places = getPlaces(all_results);
    for (var i = 0; i < all_results.length; ++i) {
        updatePlace(all_results[i].id, places[i]);
    }
    if (isSummaryStandings()) {
        return;
    }
    if (all_submissions == undefined) {
        all_submissions = new Array(problems + 1);
        ok_submissions = new Array(problems + 1);
        percent_submissions = new Array(problems + 1);
        for (var i = 0; i <= problems; ++i) {
            all_submissions[i] = 0;
            ok_submissions[i] = 0;
            percent_submissions[i] = 0;
        }
    }
    for (var i = 0; i < problems; ++i) {
        all_submissions[problems] += all_submissions[i];
        ok_submissions[problems] += ok_submissions[i];
    }
    for (var i = 0; i <= problems; ++i) {
        if (all_submissions[i] == 0) {
            percent_submissions[i] = 0;
        } else {
            percent_submissions[i] = parseInt(100 * ok_submissions[i] / all_submissions[i] + 0.5);
        }
        all_submissions[i] = all_submissions[i].toString();
        ok_submissions[i] = ok_submissions[i].toString();
        percent_submissions[i] = percent_submissions[i].toString() + '%';
    }
    var statistic = document.getElementsByClassName('submissions_statistic');
    updateStatistic(statistic[0], all_submissions);
    updateStatistic(statistic[1], ok_submissions);
    updateStatistic(statistic[2], percent_submissions);
    if (call_fill_places) {
        fillPlaces();
    }
}

var to_update;

function updateEnable(index, elem) {
    var checkbox = elem.getElementsByTagName('input')[0];
    checkbox.disabled = to_update;
}

function disableRegions(disabled) {
    to_update = disabled;
    $(".row_region").each(updateEnable);
    updateButtonsAvailability(to_update);
}

function updateRegionstate(index, elem) {
    var checkbox = elem.getElementsByTagName('input')[0];
    checkbox.checked = to_update;
}
    
function checkAll() {
    var checkbox = document.getElementById('region_all').getElementsByTagName('input')[0];
    to_update = checkbox.checked;
    $(".row_region").each(updateRegionstate);
    filter();
}