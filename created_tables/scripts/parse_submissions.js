String.prototype.replaceAll = function(search, replace){
  return this.split(search).join(replace);
}

function parseSubmisions() {
    var log = document.getElementById('submissionsLog').innerHTML;
    log = log.substr(5, log.length - 8);
    var submissions = log.split('\n');
    var result = new Array(submissions.length);
    for (var i = 0; i < submissions.length; ++i) {
        result[i] = submissions[i].split(' ');
        result[i][0] = result[i][0].replaceAll('&sp&', ' ');
        result[i][1] = parseInt(result[i][1]);
    }
    return result;
}