import os
import time
import json
import ftplib
import signal
import threading
import subprocess
from datetime import datetime, timedelta


def get_files_snapshot():
    root_dir = os.path.expanduser(os.path.join(reloader_config['acmallukrainian_path'],
                                               reloader_config['directory_to_monitor']))
    files = dict()
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename in ['index.html', 'standings.html']:
                full_path = os.path.join(dirpath, filename)
                with open(full_path, 'rb') as f:
                    relpath = os.path.relpath(dirpath, root_dir)
                    assert relpath not in files
                    files[relpath] = {
                        'full_path': full_path,
                        'filename': filename,
                        'content': f.read()
                    }
    return files


def run_scripts(script_name):
    for script in reloader_config['scripts'][script_name]:
        with open(f'data/reload_logs_{script_name}.txt', 'w', encoding='utf-8') as f:
            return_code = subprocess.call(script, shell=True, stdout=f, stderr=f)
        if return_code:
            raise subprocess.CalledProcessError(return_code, script)


def reload_standings(update_id):
    update_type = 'full' if update_id % reloader_config['full_script_period'] == 0 else 'light'
    global old_files, last_update, total_updates
    credentials = reloader_config['credentials']
    print(f'{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}, scripts ', end='', flush=True)
    start_time = time.time()
    run_scripts(f'update_logs_{update_type}')
    run_scripts('before_light_snapshot')
    new_files = {
        'light': get_files_snapshot()
    }
    run_scripts('before_full_snapshot')
    new_files['full'] = get_files_snapshot()
    print(f'{time.time() - start_time:.3f}s, diffs = ', end='', flush=True)
    diffs = [
        path for path in new_files[update_type]
        if old_files[update_type].get(path) != new_files[update_type].get(path)
    ]
    old_files = new_files
    if not diffs:
        print('[]', flush=True)
        return
    print(sorted(diffs), f'after {str(timedelta(seconds=int(time.time() - last_update)))}', end='', flush=True)
    last_update = time.time()
    with ftplib.FTP('s1.ho.ua') as ftp:
        ftp.login(**credentials)
        ftp.cwd('htdocs/' + reloader_config['directory_to_monitor'])
        for path in diffs:
            total_updates += 1
            try:
                ftp.mkd(path)
            except (ftplib.error_perm,):
                pass
            with open(new_files[update_type][path]['full_path'], 'rb') as f:
                filename = new_files[update_type][path]['filename']
                ftp.storbinary(f'STOR {path}/{filename}', f)
    print(f', upload #{total_updates} in {time.time() - last_update:.3f}s', flush=True)


def upload_loop():
    update_id = 0
    while not stop_flag.is_set():
        try:
            update_id += 1
            reload_standings(update_id)
        except Exception as e:
            print(f'reload failed {e}')
        stop_flag.wait(60)


def handle_sigint(signum, frame):
    print('Ctrl+C pressed! Stopping...')
    stop_flag.set()


signal.signal(signal.SIGINT, handle_sigint)
stop_flag = threading.Event()
reloader_config = json.load(open('data/reloader_config.json', 'r'))
old_files = {
    'light': get_files_snapshot(),
    'full': get_files_snapshot()
}
last_update = time.time()
total_updates = 0
thread = threading.Thread(target=upload_loop)
thread.start()
thread.join()
