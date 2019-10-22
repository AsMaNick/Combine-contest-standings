import time
import json
import hashlib
import requests


def get_time(t):
    hour = t // 3600
    minutes = (t % 3600) // 60
    seconds = (t % 3600) % 60
    return hour, minutes, seconds
    
    
def autorized_request(request, params):
    key = '0b37ec229e1e712a11bc91613986b7db60164008'
    secret = '5985b688b4046ab1182859c052894e740f510a62'
    current_time = int(time.time())
    rand = '123456'
    params.append('apiKey={}'.format(key))
    params.append('time={}'.format(current_time))
    params.sort()
    request = '{}?{}'.format(request, '&'.join(params))
    hash = hashlib.sha512(bytes('{}/{}#{}'.format(rand, request, secret), encoding='utf8')).hexdigest()
    request = 'https://codeforces.com/api/{}&apiSig={}{}'.format(request, rand, hash)
    print(request)
    return requests.get(request)
    
    
delete_university = False
contest_id = 101164
ouf = open('{}.csv'.format(contest_id), 'w', encoding='utf8')
keys = ['Run_Id', 'User_Name', 'Prob', 'Dur_Hour', 'Dur_Min', 'Dur_Sec', 'Stat_Short']
for key in keys:
    print(key, end=';', file=ouf)
print(file=ouf)
response = autorized_request('contest.status', ['contestId={}'.format(contest_id)])
data = response.json()
if data['status'] != 'OK':
    print(data['status'])
    print(data['comment'])
    exit()
submissions = []
for submission in data['result']:
    author = submission['author']
    if author['ghost']:
        run_id = submission['id']
        user_name = author['teamName']
        if delete_university:
            pos = user_name.find('( ')
            user_name = user_name[:pos]
        prob = submission['problem']['index']
        hour, minutes, seconds = get_time(submission['relativeTimeSeconds'])
        verdict = submission['verdict']
        if verdict == 'REJECTED':
            verdict = 'RJ'
        submissions.append((run_id, user_name, prob, hour, minutes, seconds, verdict))
submissions = submissions[::-1]
for submission in submissions:
    print(*submission, sep=';', end=';\n', file=ouf)
ouf.close()
