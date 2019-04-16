import json
from tqdm import tqdm


def is_space(c):
    return ord(c) in [9, 11, 32]
    
    
def get_name(name):
    pos = 0
    while pos < len(name) and is_space(name[pos]):
        pos += 1
    name = name[pos:]
    pos = len(name) - 1
    while pos >= 0 and is_space(name[pos]):
        pos -= 1
    return name[:pos + 1]
    
    
def get_members(text, ignore_patronymic=True, ignore_mails=True):
    members = []
    pos = 0
    while pos < len(text):
        pos = text.find('<a', pos)
        pos = text.find('>', pos) + 1
        to = text.find('</a>', pos)
        member = text[pos:to]
        pos = to + 4
        if member.find('@') != -1:
            if ignore_mails:
                continue
        elif ignore_patronymic:
            name, patronymic, surname = member.split()[:3]
            member = surname + ' ' + name
        members.append(member)
    return members
        
        
data = json.load(open('data/teams/team_list.json', 'r'))
rows = data['rows']
print(rows[0].keys())
f = open('data/team_members.txt', 'w', encoding='utf-8')
team_names = dict()
for row in tqdm(rows):
    team_name = get_name(row['name'])
    members = get_members(row['members'])
    if len(members) == 0:
        continue
    team_names[team_name] = '{} ({})'.format(team_name, ', '.join(members))
json.dump(team_names, f)
