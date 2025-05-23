var time_delay = 5000;
var contest_penalty = 20;
var contest_duration = 300, max_itmo_rating = 200, rating_averaging_method = 'avg';
var num = 0;
var all_teams_elem, all_place_elem, all_total_elem, all_penalty_elem, all_dirt_elem, all_rating_elem;
var has_rating_col = true;
var mn_y, start_y, height, margin_y;
var loaded = false;
var interval;
var cur_submission, cur_time;
var all_submissions;
var all_results;
var is_animation = false;
var finish_contest = false;
var was_submission, was_wa_modified, last_wa_parity, problems;
var statistic_elem;
var slider_pressed = false;

function Submission(id, problem_id, time, result, is_opener, elem) {
    this.id = id;
    this.problem_id = problem_id;
    this.time = time;
    this.result = result;
    this.is_opener = is_opener;
    this.elem = elem;
}

function getWrongTries(result) {
    if (result.length == 1) {
        return 0;
    }
    if (result[0] == "+") {
        return parseInt(result.substr(1)) + 1;
    }
    return parseInt(result.substr(1));
}

function lessSubmissionByTime(first, second) {
    return first.time < second.time || (first.time == second.time && getWrongTries(first.result) < getWrongTries(second.result));
}

function compareSubmissionByTime(first, second) {
    if (lessSubmissionByTime(first, second)) {
        return -1;
    } else if (lessSubmissionByTime(second, first)) {
        return 1;
    } else {
        return 0;
    }
}

function Result(id) {
    this.total = 0;
    this.penalty = 0;
    this.submissions = 0;
    this.dirt_submissions = 0;
    this.id = id;
    
    this.getDirt = function() {
        if (this.total == 0) {
            return '0.00';
        }
        return (this.dirt_submissions / (this.total + this.dirt_submissions)).toFixed(2);
    }
}

var use_id = 1;

function compareResultByTotal(first, second) {
    var a = [-first.total, first.penalty, use_id * first.id];
    var b = [-second.total, second.penalty, use_id * second.id];
    for (var i = 0; i < 3; ++i) {
        if (a[i] != b[i]) {
            if (a[i] < b[i]) {
                return -1;
            }
            return 1;
        }
    }
    return 0;
}

function compareById(first, second) {
    if (first.id < second.id) {
        return -1;
    } else if (first.id > second.id) {
        return 1;
    } else {
        return 0;
    }
}

function Statistic(problems) {
    this.problems = problems;
    this.all_submissions = new Array(problems + 1);
    this.ok_submissions = new Array(problems + 1);
    this.percent_submissions = new Array(problems + 1);
    for (var i = 0; i <= problems; ++i) {
        this.all_submissions[i] = 0;
        this.ok_submissions[i] = 0;
        this.percent_submissions[i] = 0;
    }
    
    this.addSubmission = function(submission) {
        this.all_submissions[submission.problem_id] += 1;
        if (submission.result[0] == '+') {
            this.ok_submissions[submission.problem_id] += 1;
        }
    }
    this.prepare = function() {
        this.ok_submissions[this.problems] = 0;
        this.all_submissions[this.problems] = 0;
        for (var i = 0; i < this.problems; ++i) {
            this.ok_submissions[this.problems] += this.ok_submissions[i];
            this.all_submissions[this.problems] += this.all_submissions[i];
        }
        for (var i = 0; i <= this.problems; ++i) {
            if (this.ok_submissions[i] == 0) {
                this.percent_submissions[i] = 0;
            } else {
                this.percent_submissions[i] = parseInt(100 * this.ok_submissions[i] / this.all_submissions[i] + 0.5);
            }
            this.percent_submissions[i] = this.percent_submissions[i].toString() + '%';
        }
    }
}

var statistic;

function isSummaryStandings() {
    return contest_duration == 0;
}

function loadResults() {
    loadStandingsSettings();
    if (!isSummaryStandings()) {
        updateButtonsAvailability(false);
    }
    all_teams_elem = document.getElementsByClassName('participant_result');
    all_place_elem = new Array(all_teams_elem.length);
    all_total_elem = new Array(all_teams_elem.length);
    all_penalty_elem = new Array(all_teams_elem.length);
    all_dirt_elem = new Array(all_teams_elem.length);
    all_rating_elem = new Array(all_teams_elem.length);
    has_rating_col = true;
    height = new Array(all_teams_elem.length);
    start_y = new Array(all_teams_elem.length);
    margin_y = new Array(all_teams_elem.length);
    problems = all_teams_elem[0].getElementsByClassName('st_prob').length;
    for (var i = 0; i < all_teams_elem.length; ++i) {
        all_place_elem[i] = all_teams_elem[i].getElementsByClassName('st_place')[0].getElementsByTagName('input')[0];
        all_total_elem[i] = all_teams_elem[i].getElementsByClassName('st_total')[0].getElementsByTagName('input')[0];
        var st_pens = all_teams_elem[i].getElementsByClassName('st_pen');
        all_penalty_elem[i] = st_pens[0].getElementsByTagName('input')[0];
        all_dirt_elem[i] = st_pens[1].getElementsByTagName('input')[0];
        if (st_pens.length > 2) {
            all_rating_elem[i] = st_pens[2].getElementsByTagName('input')[0];
        } else {
            has_rating_col = false;
        }
    }
    loaded = true;
}

function updateMaxHeight(height) {
    var elem = document.getElementById('styles');
    elem.innerHTML = 'table.standings td { height: ' + height.toString() + 'px; }';
}

function fillY() {
    mn_y = -1;
    var mx_height = 0;
    for (var i = 0; i < all_teams_elem.length; ++i) {
        var rect = all_teams_elem[i].getBoundingClientRect();
        mx_height = Math.max(mx_height, rect.height);
    }
    updateMaxHeight(mx_height);
    var cur_pos = 0, last_y = -1, last_height = -1;
    for (var i = 0; i < all_teams_elem.length; ++i) {
        var rect = all_teams_elem[i].getBoundingClientRect();
        height[i] = rect.height;
        mx_height = Math.max(mx_height, height[i]);
        start_y[i] = rect.top;
        if (start_y[i] != 0) {
            if (mn_y == -1) {
                mn_y = start_y[i];
            }
            if (last_y != -1) {
                margin_y[cur_pos] = start_y[i] - last_y - last_height;
                ++cur_pos;
            }
            last_y = start_y[i];
            last_height = height[i];
        }
    }
}

function updateStandingsTime(time) {
    var elem = document.getElementById('standings_time');
    elem.innerHTML = 'Standings [' + time + ']';
}

function timeInMinutes(time) {
    return parseInt(time[1]) * 60 + parseInt(time.substr(3, 2));
}

function timeInStr(time) {
    var time_str = '(' + ((time / 60) >> 0).toString() + ':';
    if (time % 60 < 10) {
        time_str += '0';
    }
    time_str += (time % 60).toString() + ')';
    return time_str;
}

function getPlace(id) {
    return all_place_elem[id].value;
}

function updatePlace(id, val) {
    if (all_place_elem[id].value != '-') {
        all_place_elem[id].value = val;
    }
}

function updateTotal(id, val) {
    all_total_elem[id].value = val;
}

function updatePenalty(id, val) {
    all_penalty_elem[id].value = val;
}

function updateDirt(id, val) {
    all_dirt_elem[id].value = val;
}

function updateRating(id, val) {
    if (has_rating_col && all_rating_elem[id].value != '') {
        all_rating_elem[id].value = val;
    }
}

function getPlaces(all_results) {
    var time_start = Date.now();
    
    var next_place = 0;
    var places = new Array(all_results.length);
    use_id = 0;
    var real_i = 0, real_next_place = 0;
    for (var i = 0; i < all_results.length; ) {
        if (getPlace(all_results[i].id) == '-') {
            ++i;
            continue;
        }
        while (next_place < all_results.length && (compareResultByTotal(all_results[next_place], all_results[i]) <= 0 || getPlace(all_results[next_place].id) == '-')) {
            if (getPlace(all_results[next_place].id) != '-') {
                ++real_next_place;
            }
            ++next_place;
        }
        var place = (real_i + 1).toString();
        if (real_i + 1 < real_next_place) {
            place += '-' + real_next_place.toString();
        }
        for (var j = i; j < next_place; ++j) {
            places[j] = place;
            if (getPlace(all_results[j].id) != '-') {
                real_i += 1;
            }
        }
        i = next_place;
    }
    return places;
}

function calculateRatingITMO(max_solved_problems, cnt_official_teams, place, total) {
    var itmo_rating = 0;
    if (total > 0) {
        if (cnt_official_teams == 1) {
            return max_itmo_rating;
        }
        var min_place;
        if (place.indexOf('-') == -1) {
            min_place = parseInt(place);
        } else {
            min_place = parseInt(place.substr(0, place.indexOf('-')));
        }
        itmo_rating = 0.5 * max_itmo_rating * total / max_solved_problems * (2 * cnt_official_teams - 2) / (cnt_official_teams + min_place - 2);
    }
    return itmo_rating;
}

function updateStandingsToTime(to_time) {
    var time_start = Date.now();
    
    console.log(cur_time, to_time);
    var to_time_str = timeInStr(to_time);
    updateStandingsTime(to_time_str.substr(1, 4) + ':00');
    if (!slider_pressed) {
        var slider = document.getElementById('slider');
        if (slider) {
            slider.value = to_time;
            updateSliderFill();
        }
    }
    all_results.sort(compareById);
    for (var i = 0; i < was_submission.length; ++i) {
        was_submission[i] = 0;
    }
    for (var i = 0; i < was_wa_modified.length; ++i) {
        for (var j = 0; j < problems; ++j) {
            was_wa_modified[i][j] = 0;
        }
    }
    while (cur_submission < all_submissions.length && all_submissions[cur_submission].time <= to_time_str) {
        var time = all_submissions[cur_submission].time;
        var id = all_submissions[cur_submission].id;
        var submission_result = all_submissions[cur_submission].result;
        var is_opener = all_submissions[cur_submission].is_opener;
        var prob = all_submissions[cur_submission].elem;
        var problem_id = all_submissions[cur_submission].problem_id;
        statistic.addSubmission(all_submissions[cur_submission]);
        if (submission_result[0] == '-') {
            prob.innerHTML = submission_result;
            if (!was_wa_modified[id][problem_id]) {
                prob.style = 'animation: color_change_wa' + last_wa_parity[id][problem_id].toString() + ' 3s; animation-fill-mode: forwards;';
                was_wa_modified[id][problem_id] = 1;
            }
            //prob.style = 'background: #ffd0d0';
        } else if (submission_result[0] == '?') {
            prob.innerHTML = submission_result + '<div class="st_time">' + time + '</div>';
            if (was_wa_modified[id][problem_id] != 2) {
                prob.style = 'animation: color_change_frozen' + last_wa_parity[id][problem_id].toString() + ' 3s; animation-fill-mode: forwards;';
                was_wa_modified[id][problem_id] = 2;
            }
        } else if (is_opener) {
            prob.style = 'animation: color_change_ac_first 3s 1; animation-fill-mode: forwards;';
            //prob.style = 'background: #b0ffb0';
        } else {
            prob.style = 'animation: color_change_ac 3s 1; animation-fill-mode: forwards;';
            //prob.style = 'background: #e0ffe0';
        }
        all_results[id].submissions += 1;
        if (submission_result[0] == '+') {
            was_submission[all_results[id].id] = 1;
            all_results[id].total += 1;
            all_results[id].penalty += timeInMinutes(time);
            if (submission_result.length > 1) {
                all_results[id].penalty += contest_penalty * parseInt(submission_result.substr(1));
                all_results[id].dirt_submissions += parseInt(submission_result.substr(1));
            }
            prob.innerHTML = submission_result + '<div class="st_time">' + time + '</div>';
        }
        cur_submission += 1;
    }
    use_id = 1;
    all_results.sort(compareResultByTotal);
    
    var places = getPlaces(all_results);
    var to_y = mn_y;
    var max_solved_problems = 0, cnt_official_teams = 0;
    for (var i = 0; i < all_results.length; ++i) {
        var id = all_results[i].id;
        if (all_place_elem[id].value != '-') {
            ++cnt_official_teams;
            max_solved_problems = Math.max(max_solved_problems, all_results[i].total);
        }
    }
    for (var i = 0; i < all_results.length; ++i) {
        var id = all_results[i].id;
        all_teams_elem[id].style.transform = 'translateY(' + (to_y - start_y[id]).toString() + 'px)';
        updatePlace(id, places[i]);
        if (was_submission[id] == 1) {
            updateTotal(id, all_results[i].total);
            updatePenalty(id, all_results[i].penalty);
            updateDirt(id, all_results[i].getDirt());
        }
        if (has_rating_col && all_place_elem[id].value != '-') {
            var itmo_rating = calculateRatingITMO(max_solved_problems, cnt_official_teams, places[i], all_results[i].total);
            updateRating(id, itmo_rating.toFixed(2));
        }
        for (var j = 0; j < problems; ++j) {            
            if (was_wa_modified[i][j]) {
                last_wa_parity[i][j] ^= 1;
            }
        }
        to_y += height[id] + margin_y[i];
    }
    cur_time = to_time;
    if (cur_time == contest_duration && document.getElementsByTagName('button')[0].disabled) {
        setTimeout(function() { 
            if (document.getElementById('standings_time').innerHTML == 'Standings [' + timeInStr(contest_duration).substr(1, 4) + ':00' + ']') {
                clearInterval(interval);
                filter(true); 
            }
        }, 3000);
    }
    statistic.prepare();
    updateStatistic(statistic_elem[0], statistic.all_submissions);
    updateStatistic(statistic_elem[1], statistic.ok_submissions);
    updateStatistic(statistic_elem[2], statistic.percent_submissions);
    console.log('Update results', Date.now() - time_start);
}

function fillPlaces() {
    var places = getPlaces(all_results);
    var max_solved_problems = 0, cnt_official_teams = 0;
    for (var i = 0; i < all_results.length; ++i) {
        var id = all_results[i].id;
        if (all_place_elem[id].value != '-') {
            ++cnt_official_teams;
            max_solved_problems = Math.max(max_solved_problems, all_results[i].total);
        }
    }
    for (var i = 0; i < all_results.length; ++i) {
        var id = all_results[i].id;
        var elem = all_teams_elem[id];
        updatePlace(id, places[i]);
        updateTotal(id, all_results[i].total);
        updatePenalty(id, all_results[i].penalty);
        updateDirt(id, all_results[i].getDirt());
        if (has_rating_col && all_place_elem[id].value != '-') {
            var itmo_rating = calculateRatingITMO(max_solved_problems, cnt_official_teams, places[i], all_results[i].total);
            updateRating(id, itmo_rating.toFixed(2));
        }
    }
    is_animation = false;
    disableRegions(false);
    updateMaxHeight(40);
}

function getContestSpeed() {
    var elem = document.getElementById('contest_speed');
    return parseInt(elem.value);
}

function updateSubmissions() {
    if (cur_time == contest_duration) {
        return;
    }
    var to_time = Math.min(contest_duration, cur_time + getContestSpeed());
    if (finish_contest) {
        to_time = contest_duration;
    }
    updateStandingsToTime(to_time);
}

function finish() {
    if (is_animation) {
        document.getElementsByTagName('button')[1].disabled = true;
        document.getElementsByTagName('button')[2].disabled = true;
        if (document.getElementById('pause').innerHTML == "Continue") {
            document.getElementById('pause').innerHTML == "Pause"
        }
        clearInterval(interval);
        interval = setInterval(updateSubmissions, 500);
        finish_contest = true;
    }
}

function pause() {
    if (is_animation) {
        var elem = document.getElementById('pause');
        if (elem.innerHTML == "Pause") {
            clearInterval(interval);
            elem.innerHTML = "Continue";
        } else {
            elem.innerHTML = "Pause";
            updateSubmissions();
            interval = setInterval(updateSubmissions, time_delay);
        }
    }
}

function getPenalty() {
    var time = document.getElementById('penalty_points').value;
    if (time == "") {
        time = 20;
    }
    if (time > 20) {
        time = 20;
    }
    if (time < 1) {
        time = 1;
    }
    document.getElementById('penalty_points').value = time;
    return time;
}

function getStartTime() {
    var time = document.getElementById('contest_start_time').value;
    var res = 0;
    if ('0' <= time[0] && time[0] <= '9' && '0' <= time[2] && time[2] <= '9' && '0' <= time[3] && time[3] <= '9') {
        res = Math.min(contest_duration, (time.charCodeAt(0) - 48) * 60 + (time.charCodeAt(2) - 48) * 10 + (time.charCodeAt(3) - 48));
    }
    var pl = '';
    if (res % 60 < 10) {
        pl = '0';
    }
    document.getElementById('contest_start_time').value = ((res / 60) >> 0).toString() + ':' + pl + (res % 60).toString() + ':00';
    return res;
}

function getHrefParams() {
    var res = {};
    const startParams = document.location.href.indexOf('?');
    if (startParams != -1) {
        var params = document.location.href.substring(startParams + 1).split('&');
        for (var param of params) {
            var data = param.split('=');
            if (data.length == 2) {
                res[data[0]] = data[1];
            }
        }
    }
    return res;
}

function loadStandingsSettings() {
    contest_duration = 300;
    max_itmo_rating = 200;
    rating_averaging_method = 'avg';
    if (document.getElementById('standingsSettings') === null) {
    } else {
        var settings = document.getElementById('standingsSettings').innerHTML;
        settings = settings.substr(5, settings.length - 8);
        params = settings.split('\n');
        for (var i = 0; i < params.length; ++i) {
            var data = params[i].split(' ');
            if (data[0] == 'contestDuration') {
                contest_duration = parseInt(data[1]);
            } else if (data[0] == 'maxItmoRating') {
                max_itmo_rating = parseInt(data[1]);
            } else if (data[0] == 'ratingAveragingMethod') {
                rating_averaging_method = data[1];
            }
        }
    }
    var href_params = getHrefParams();
    if ('ratingAveragingMethod' in href_params) {
        rating_averaging_method = href_params['ratingAveragingMethod'];
    }
}

function go(only_init) {
    if (!loaded || (is_animation && only_init === undefined)) {
        return;
    }
    time_delay = 5000;
    if (document.location.href.indexOf('time_delay=') != -1) {
        var pos = document.location.href.indexOf('time_delay=');
        time_delay = parseInt(document.location.href.substr(pos + 11));
        if (time_delay !== time_delay) {
            time_delay = 5000;
        }
        time_delay = Math.max(time_delay, 500);
    }
    finish_contest = false;
    is_animation = true;
    var need_update = true;
    if (document.getElementsByClassName('row_region')[0].getElementsByTagName('input')[0].disabled) {
        need_update = false;
        if (!only_init) {
            updateButtonsAvailability(true);
        }
    }
    var time_start = Date.now();
    all_results = new Array();
    was_submission = new Array(all_teams_elem.length);
    if (need_update) {
        disableRegions(true);
        if (only_init) {
            updateButtonsAvailability(false);
        }
        fillY();
        all_submissions = [];
        var id = -1;
        loadStandingsSettings();
        if (document.getElementById('submissionsLog') === null) {
            for (var i = 0; i < all_teams_elem.length; ++i) {
                if (all_teams_elem[i].hidden) {
                    continue;
                }
                all_teams_elem[i].style = "transition: transform 1s ease-in-out 0ms, opacity 1s ease-in-out 0ms;";
                id += 1;
                all_results.push(new Result(i));
                var probs = all_teams_elem[i].getElementsByClassName('st_prob');
                var all_ac_times = [];
                var all_was = [];
                for (var j = 0; j < probs.length; ++j) {
                    var last_time = contest_duration - 1;
                    var prob_res = getSubmissionResult(probs[j]);
                    if (getTime(probs[j]) != '(9:99)') {
                        all_submissions.push(new Submission(id, j,
                                                            getTime(probs[j]), 
                                                            prob_res, 
                                                            probs[j].style.background == 'rgb(176, 255, 176)', 
                                                            probs[j]));
                        last_time = Math.max(0, timeInMinutes(getTime(probs[j])) - 1);
                        all_ac_times.push(timeInMinutes(getTime(probs[j])));
                    }
                    if (prob_res.length > 1 && (prob_res[0] == '+' || prob_res[0] == '-')) {
                        var wa = parseInt(prob_res.substr(1));
                        all_was.push([last_time, wa, j, probs[j]]);
                    }
                    probs[j].innerHTML = '&nbsp';
                    probs[j].style = '';
                }
                all_ac_times.sort(function(x, y) { return x - y; } );
                all_was.sort(function(x, y) { return x[0] - y[0]; } );
                var pos_ac = 0;
                for (var j = 0; j < all_was.length; ++j) {
                    var last_time = all_was[j][0];
                    var wa = all_was[j][1];
                    var problem_id = all_was[j][2];
                    var elem = all_was[j][3];
                    while (pos_ac < all_ac_times.length && all_ac_times[pos_ac] <= last_time) {
                        ++pos_ac;
                    }
                    var pos_from = pos_ac - 2;
                    if (last_time == contest_duration - 1) {
                        --pos_from;
                    }
                    var from_time = 0;
                    if (pos_from >= 0) {
                        from_time = all_ac_times[pos_from];
                    }
                    var rnds;
                    if (last_time == contest_duration - 1) {
                        rnds = new Array(wa + 1);
                        rnds[0] = 0;
                        for (var k = 1; k <= wa; ++k) {
                            rnds[k] = (Math.random() - 0.5) * 0.2
                        }
                        rnds.sort(function(a, b) { return a - b; });
                    }
                    for (var k = 1; k <= wa; ++k) {
                        var coef = k / (k + 1);
                        if (last_time == contest_duration - 1) {
                            coef += rnds[k];
                            coef = Math.max(coef, 0);
                            coef = Math.min(coef, 1);
                        }
                        var time = parseInt(from_time + (last_time - from_time) * coef);
                        all_submissions.push(new Submission(id, problem_id,
                                                            timeInStr(time), 
                                                            '-' + k.toString(), 
                                                            false, 
                                                            elem));
                    }
                }
                updateDirt(i, '0.00');
                updateTotal(i, 0);
                updatePenalty(i, 0);
            }
        } else {
            var submissionsData = parseSubmisions();
            if (submissionsData.length <= 1) {
                submissionsData = [];
            }
            var team_ids = {};
            var probs = new Array(all_teams_elem.length);
            var is_opener = new Array(all_teams_elem.length);
            for (var i = 0; i < all_teams_elem.length; ++i) {
                if (all_teams_elem[i].hidden) {
                    continue;
                }
                id += 1;
                var team_name = all_teams_elem[i].getElementsByClassName('st_team')[0].innerHTML;
                team_ids[team_name] = id;
                probs[id] = all_teams_elem[i].getElementsByClassName('st_prob');
                all_teams_elem[i].style = "transition: transform 1s ease-in-out 0ms, opacity 1s ease-in-out 0ms;";
                all_results.push(new Result(i));
                updateDirt(i, '0.00');
                updateTotal(i, 0);
                updatePenalty(i, 0);
                is_opener[id] = new Array(probs[id].length);
                for (var j = 0; j < probs[id].length; ++j) {
                    is_opener[id][j] = probs[id][j].style.background == 'rgb(176, 255, 176)';
                    probs[id][j].innerHTML = '&nbsp';
                    probs[id][j].style = '';
                }
                if (!submissionsData.length) {
                    var log = all_teams_elem[i].getElementsByClassName('teamSubmissionsLog')[0].innerHTML;
                    log = log.replace('<!--', '').replace('-->', '');
                    var submissions = log.split('\n');
                    for (var submission of submissions) {
                        var data = submission.split(' ');
                        var problem_id = parseInt(data[0]);
                        all_submissions.push(new Submission(id,
                                                            problem_id,
                                                            data[1], // timeInStr
                                                            data[2], // result
                                                            is_opener[id][problem_id],
                                                            probs[id][problem_id]));
                    }
                }
            }
            for (var submission of submissionsData) {
                if (submission[0] in team_ids) {
                    var id = team_ids[submission[0]];
                    var problem_id = submission[1];
                    all_submissions.push(new Submission(id,
                                                        problem_id,
                                                        submission[2], // timeInStr
                                                        submission[3], // result
                                                        is_opener[id][problem_id],
                                                        probs[id][problem_id]));
                }
            }
        }
    } else {
        for (var i = 0; i < all_teams_elem.length; ++i) {
            if (all_teams_elem[i].hidden) {
                continue;
            }
            var probs = all_teams_elem[i].getElementsByClassName('st_prob');
            all_teams_elem[i].style = "transition: transform 1s ease-in-out 0ms, opacity 1s ease-in-out 0ms;";
            all_results.push(new Result(i));
            updateDirt(i, '0.00');
            updateTotal(i, 0);
            updatePenalty(i, 0);
            console.log(i);
            for (var j = 0; j < probs.length; ++j) {
                probs[j].innerHTML = '&nbsp';
                probs[j].style = '';
            }
        }
    }
    last_wa_parity = new Array(all_results.length);
    was_wa_modified = new Array(all_results.length);
    console.log(all_results.length, problems);
    for (var i = 0; i < all_results.length; ++i) {
        last_wa_parity[i] = new Array(problems);
        was_wa_modified[i] = new Array(problems);
        for (var j = 0; j < problems; ++j) {
            last_wa_parity[i][j] = 0;
            was_wa_modified[i][j] = 0;
        }
    }
    console.log('Prepared', Date.now() - time_start);
    all_submissions.sort(compareSubmissionByTime);
    /*for (var i = 0; i < all_submissions.length; ++i) {
        console.log(all_submissions[i]);
    }*/
    cur_submission = 0;
    cur_time = 0;
    statistic = new Statistic(problems);
    statistic_elem = document.getElementsByClassName('submissions_statistic');
    contest_penalty = getPenalty();
    updateStandingsToTime(getStartTime());
    if (!only_init && cur_time < contest_duration) {
        interval = setInterval(updateSubmissions, time_delay);
    } else if (document.getElementById('pause').innerHTML == "Pause") {
        is_animation = false;
    }
}

function updateSliderFill() {
    var slider = document.getElementById('slider');
    var fill = 100 * slider.value / slider.max;
    slider.style.background = "linear-gradient(to right, #4CAF50 0%, #4CAF50 " + fill.toString() + "%, #d3d3d3 " + fill.toString() + "%, #d3d3d3 100%)";
}

function sliderMouseDown() {
    slider_pressed = true;
}

function sliderMouseUp() {
    slider_pressed = false;
    if (is_animation) {
        clearInterval(interval);
        var start_time = document.getElementById('slider').value;
        var old_start_time = document.getElementById('contest_start_time').value;
        document.getElementById('contest_start_time').value = timeInStr(start_time).substr(1, 4) + ':00';
        go(document.getElementById('pause').innerHTML == "Continue");
        document.getElementById('contest_start_time').value = old_start_time;
        /*updateStandingsToTime(start_time);
        if (cur_time < contest_duration) {
            interval = setInterval(updateSubmissions, time_delay);
        }*/
    } else {
        var start_time = document.getElementById('slider').value;
        document.getElementById('contest_start_time').value = timeInStr(start_time).substr(1, 4) + ':00';
        go(true);
    }
}

function updateButtonsAvailability(start_disabled) {
    document.getElementsByTagName('button')[0].disabled = start_disabled;
    document.getElementsByTagName('button')[1].disabled = !start_disabled;
    document.getElementsByTagName('button')[2].disabled = !start_disabled;
}

function getColoredClass(oj, rating) {
    if (oj == 'AtCoder') {
        if (rating >= 2800) {
            return 'user-red-atcoder';
        } else if (rating >= 2400) {
            return 'user-orange-atcoder';
        } else if (rating >= 2000) {
            return 'user-yellow-atcoder';
        } else if (rating >= 1600) {
            return 'user-blue-atcoder';
        } else if (rating >= 1200) {
            return 'user-cyan-atcoder';
        } else if (rating >= 800) {
            return 'user-green-atcoder';
        } else if (rating >= 400) {
            return 'user-brown-atcoder';
        } else if (rating > 0) {
            return 'user-gray-atcoder';
        }
        return 'user-unrated-atcoder';
    } else if (oj == 'CF') {
        if (rating >= 2400) {
            return 'user-red';
        } else if (rating >= 2100) {
            return 'user-orange';
        } else if (rating >= 1900) {
            return 'user-violet';
        } else if (rating >= 1600) {
            return 'user-blue';
        } else if (rating >= 1400) {
            return 'user-cyan';
        } else if (rating >= 1200) {
            return 'user-green';
        } else if (rating > 0) {
            return 'user-gray';
        }
        return 'user-black';
    }
}

function getNutellaName(name, rating) {
    if (rating >= 3000) {
        return `<span class="legendary-user-first-letter">${name[0]}</span>${name.substring(1)}`;
    }
    return name;
}

function getColoredName(info, oj) {
    if (!(oj in info.info)) {
        return info.name;
    }
    var handle = info.info[oj].handle;
    var rating = info.info[oj].rating;
    if (oj == 'AtCoder') {
        return `<a href="https://atcoder.jp/users/${handle}" title="${handle}, ${rating}" class="user-atcoder ${getColoredClass(oj, rating)}">${info.name}</a>`;
    } else if (oj == 'CF') {
        return `<a href="https://codeforces.com/profile/${handle}" title="${handle}, ${rating}" class="user-cf ${getColoredClass(oj, rating)}">${getNutellaName(info.name, rating)}</a>`;
    }
}

function getColoredRating(rating, oj) {
    console.log(rating, oj);
    if (oj == 'AtCoder') {
        return `<a class="user-atcoder ${getColoredClass(oj, rating)}">${rating}</a>`;
    } else if (oj == 'CF') {
        return `<a class="user-cf ${getColoredClass(oj, rating)}">${getNutellaName(rating.toString(), rating)}</a>`;
    }
}

function updateTeamRating() {
    var oj = document.getElementById('show_ranking_select').value;
    for (var i = 0; i < all_teams_elem.length; ++i) {
        var info = all_teams_elem[i].getElementsByClassName('teamInfoJson')[0].innerHTML;
        info = info.substring(4, info.length - 3);
        if (info == '') {
            continue;
        }
        info = JSON.parse(info);
        var team_members = [], team_ratings = [];
        for (var team_member of info.members) {
            if (oj in team_member.info) {
                team_members.push(getColoredName(team_member, oj));
                team_ratings.push(team_member.info[oj].rating);
            } else {
                team_members.push(team_member.name);
            }
        }
        var team_name = info.team + ' (' + team_members.join(', ') + ')';
        if (oj in info.rating && info.rating[oj] > 0) {
            team_name += ', total = ' + getColoredRating(info.rating[oj], oj);
        }
        all_teams_elem[i].getElementsByClassName('displayedTeamName')[0].innerHTML = team_name;
    }
}