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

function recalculateRatingITMO() {
    loadStandingsSettings();
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
            var itmo_rating = calculateRatingITMO(max_solved_problems, cnt_official_teams, all_place_elem[i].value, problems_solved);
            updateRating(i, itmo_rating.toFixed(2));
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
    var all_results = new Array();
    for (var i = 0; i < all_teams_elem.length; ++i) {
        if (all_teams_elem[i].hidden) {
            continue;
        }
        var cur_result = new Result(i);
        cur_result.total = parseInt(all_total_elem[i].value);
        cur_result.penalty = parseInt(all_penalty_elem[i].value);
        all_results.push(cur_result);
    }
    var places = getPlaces(all_results);
    for (var i = 0; i < all_results.length; ++i) {
        updatePlace(all_results[i].id, places[i]);
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