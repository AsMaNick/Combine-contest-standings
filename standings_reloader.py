import os
import time
import json
import ftplib
import signal
import threading
import subprocess
from datetime import datetime, timedelta


def get_standings_snapshot():
    root_dir = os.path.expanduser(os.path.join(reloader_config['acmallukrainian_path'],
                                               reloader_config['directory_to_monitor']))
    standings = dict()
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename == 'standings.html':
                full_path = os.path.join(dirpath, filename)
                with open(full_path, 'rb') as f:
                    standings[os.path.relpath(dirpath, root_dir)] = {
                        'full_path': full_path,
                        'content': f.read()
                    }
    return standings


def reload_standings():
    global old_standings, last_update
    credentials = reloader_config['credentials']
    print(f'{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}, diffs = ', end='')
    for script in reloader_config['scripts_to_run']:
        with open('data/reload_logs.txt', 'w', encoding='utf-8') as f:
            return_code = subprocess.call(script, shell=True, stdout=f, stderr=f)
        if return_code:
            raise subprocess.CalledProcessError(return_code, script)
    new_standings = get_standings_snapshot()
    diffs = [path for path in new_standings if old_standings.get(path) != new_standings.get(path)]
    old_standings = new_standings
    if not diffs:
        print('[]')
        return
    print(sorted(diffs), f'updating after {str(timedelta(seconds=int(time.time() - last_update)))}')
    last_update = time.time()
    with ftplib.FTP('s1.ho.ua') as ftp:
        ftp.login(**credentials)
        ftp.cwd('htdocs/' + reloader_config['directory_to_monitor'])
        for path in diffs:
            try:
                ftp.mkd(path)
            except ftplib.error_perm as e:
                pass
            with open(old_standings[path]['full_path'], 'rb') as f:
                ftp.storbinary(f'STOR {path}/standings.html', f)


def upload_loop():
    while not stop_flag.is_set():
        try:
            reload_standings()
        except Exception as e:
            print(f'reload failed {e}')
        stop_flag.wait(60)


def handle_sigint(signum, frame):
    print('Ctrl+C pressed! Stopping...')
    stop_flag.set()


signal.signal(signal.SIGINT, handle_sigint)
stop_flag = threading.Event()
reloader_config = json.load(open('data/reloader_config.json', 'r'))
old_standings = get_standings_snapshot()
last_update = time.time()
thread = threading.Thread(target=upload_loop)
thread.start()
thread.join()
