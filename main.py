import requests
import yt_dlp
import flask
import flaskwebgui
import time
import random
from flask import Flask, render_template, request, jsonify
import os
import threading
import logging
import json
import pathlib
import appdirs
import sqlite3
import logging
import re
import time
import database
import webbrowser

app = Flask(__name__)

states = 0

logging.basicConfig()
logging.disable()

SAVE_PATH = pathlib.Path.home() / "Downloads" / "ZE LOADER"

CONFIG_PATH = appdirs.user_config_dir('ZE LOADER', 'ZE APPS')
DATABASE_PATH = os.path.join(CONFIG_PATH, "database.db")

PERCENT = ''
SPEED = ''
ETA = ''
LAST_URL = ''
ERROR = False
ERROR_LIST = []
VIDEO_LAST_NAME = ''
VIDEO_DOWNLOADED = False
HISTORY_MAX_LENGHT = 9
FIRST_RUN = 0

os.makedirs(CONFIG_PATH, exist_ok=True)


if os.path.exists(DATABASE_PATH) == False:
    FIRST_RUN += 1
    browser_cookie = 'not_using'
    download_folder = None
    if os.name == 'posix':
        name = webbrowser.get().name

        if name == 'google-chrome':
            browser_cookie = 'chrome'

        config_path = os.path.expanduser('~/.config/user-dirs.dirs')

        print(config_path)
        if os.path.exists(config_path):
            with open(config_path, 'r') as file:
                for line in file:
                    if line.startswith('XDG_DOWNLOAD_DIR'):
                        download_folder = line.split('=')[1].strip().strip('"')
                        download_folder = download_folder.replace('$HOME', os.path.expanduser('~'))
                        break
        if not download_folder:
            download_folder = str(SAVE_PATH)
        
        print(download_folder)


    history = json.dumps([])
    download_type = 'video+audio'
    download_quality = 'best_quality'
    download_path = json.dumps(download_folder)
    print(history)
    print(download_type)
    print(download_quality)
    print(download_path)
    print(browser_cookie)

    database.create_database(
        DATABASE_PATH,
        history,
        download_type,
        download_quality,
        download_path,
        browser_cookie
        )

database.initialize_database(DATABASE_PATH)


ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


status_list = []


class YTDLPHelper:
    def __init__(self, status_list, task_id):
        self.status_list = status_list
        self.task_id = task_id
        self.progress = {
            'task_id': task_id,
            'status': 'idle',
            'percent': 0,
            'speed': None,
            'eta': None,
            'already_downloaded': False,
            'name': None,
            'url': None,
            'error': None
        }
        self.status_list.append(self.progress)

    def find_progress_by_id(self, task_id):
        return next((d for d in self.status_list if d['task_id'] == task_id), None)

    def update_progress(self, d):
        for progress_dict in self.status_list:
            if progress_dict['task_id'] == self.task_id:
                progress_dict.update(d)
                break

    def download(self, url, task_id, download_path, download_type, download_quality, browser_cookie):
        format = ''
        quality = ''
        if download_type == 'video+audio':
            format = 'bestvideo+bestaudio'
        elif download_type == 'video':
            format = 'bestvideo'
        elif download_type == 'audio':
            format = 'bestaudio'


        if download_quality == 'best_quality':
            quality = 'best'
        elif download_quality == 'medium_quality':
            quality = 'high'
        elif download_quality == 'low_quality':
            quality = 'low'

        
        if download_path[-1] != '/':
            download_path = download_path + '/'

        print(format)
        print(download_path)
        print(browser_cookie)


        ydl_opts = {
            'progress_hooks': [self.progress_hook],
            'format': format,
            'merge_output_format': 'mp4',
            'quiet': False,
            'no_warnings': False,
            'cookiesfrombrowser': (browser_cookie,) if browser_cookie != 'not_using' else None,
            'outtmpl': download_path + '%(title)s.%(ext)s',
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print(ydl_opts)
                info = ydl.extract_info(url, download=False)
                filename = ydl.prepare_filename(info)
                ydl.existing_file(filepaths=[filename])

                video_name = info['title']
                self.progress['name'] = video_name
                self.progress['url'] = url
                self.progress['status'] = 'downloading'
                
                status_list.append(self.progress)
                ydl.download([url])
                self.progress['status'] = 'completed'

                history = json.loads(database.get_history())

                to_append = {
                        'url': url,
                        'path': filename,
                        'name': video_name,
                        'exists': True,
                    }
                
                if to_append not in history:
                    history.append(
                        {
                            'url': url,
                            'path': filename,
                            'name': video_name,
                            'exists': True,
                        }
                    )

                database.set_history(json.dumps(history))
                

        except Exception as e:
            self.update_progress({
                'status': 'error',
                'error': str(e)
            })

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            PERCENT = d.get('_percent_str', 'N/A')
            SPEED = d.get('_speed_str', 'N/A')
            ETA = d.get('_eta_str', 'N/A')
            
            self.update_progress({
                'percent': ansi_escape.sub('', str(PERCENT)),
                'speed': ansi_escape.sub('', str(SPEED)),
                'eta': ansi_escape.sub('', str(ETA))
            })
 
@app.route('/')
@app.route('/index')
def index():
    global FIRST_RUN

    if FIRST_RUN == 1:
        FIRST_RUN -= 1
        return render_template('welcome.html')
    
    else:
        return render_template('index.html', app_icon='/styles/static/icon.ico')


@app.route('/index-error')
def index_error():
    erorr = request.args.get('error', '')
    print(erorr)
    erorr.replace('\n', '<br>')
    return render_template('index-error.html', app_icon='/styles/static/icon.ico', error_value=erorr)

@app.route('/settings')
def settings():
    download_path = json.loads(database.get_download_path())
    return render_template('settings.html', current_path=download_path)


@app.route('/about')
def about():
    return render_template('about.html', current_path=SAVE_PATH)


@app.route('/history')
def history():
    history2 = json.loads(database.get_history())
    histor = []

    for i in history2:
        histor.append(
            {
                'name': i['name'],
                'url': i['url'],
                'path': i['path'],
                'exists': True,
            }
        )

    return render_template('history.html', histor=history2)


@app.route('/download')
def download():
    video_download_url = request.args.get('url')
    print(video_download_url)

    video_quality = database.get_download_quality()
    video_type = database.get_download_type()
    video_path = json.loads(database.get_download_path())
    browser_cookie = database.get_browser_cookie()

    TASK_ID = random.randint(1000000, 999999999999)

    helper = YTDLPHelper(status_list, TASK_ID)
    threading.Thread(target=helper.download, args=(video_download_url, TASK_ID, video_path, video_type, video_quality, browser_cookie)).start()

    return render_template('download.html', state='loading...', task_id=TASK_ID)


@app.route('/get_state')
def get_state():
    task_id = int(request.args.get('task_id'))
    
    STATUS = ''
    PERCENT = ''
    SPEED = ''
    ETA = ''
    NAME = ''
    URL = ''
    ERROR_TEXT = ''

    print(status_list)
    print(task_id)
    for progress_dict in status_list:
        if progress_dict['task_id'] == task_id:
            STATUS = progress_dict['status']
            PERCENT = progress_dict['percent']
            SPEED = progress_dict['speed']
            ETA = progress_dict['eta']
            NAME = progress_dict['name']
            URL = progress_dict['url']
            ERROR_TEXT = progress_dict['error']

    STATE_TO_SEND = f"{NAME} {STATUS}... \nPERCENT:{PERCENT} | SPEED: {SPEED} | ETA: {ETA}".replace('\n', '<br>')

    if 'is not a valid URL' in str(ERROR_TEXT):
        error_text = 'Video is unavailble. \nInvalid URL'.replace('\n', '<br>')
    elif 'Sign in to confirm' in str(ERROR_TEXT) or 'Video unavailable' in str(ERROR_TEXT):
        error_text = "Video is unavailble. \nTry change browser's cookies in settings".replace('\n', '<br>')
    elif 'Requested format is not available' in str(ERROR_TEXT):
        error_text = "Video is unavailble. \nTry change download quality in settings\nTry remove browser's cookies in settings".replace('\n', '<br>')
    else:
        error_text = str(ERROR_TEXT)

    completed_text = f'{NAME} is downloaded.'.replace('\n', '<br>')

    if STATUS == 'error':
        return jsonify(state=f"{STATE_TO_SEND}", ready=True, error_text=error_text)
    else:
        if NAME is not None:
            if str(PERCENT) == '0':
                return jsonify(state=f"{NAME} \nis downloading...".replace('\n', '<br>'), ready=True if STATUS == 'completed' else False, error_text=completed_text)
            else:
                return jsonify(state=f"{STATE_TO_SEND}", ready=True if STATUS == 'completed' else False, error_text=completed_text)

        else:
            return jsonify(state=f"loading information...", ready=True if STATUS == 'completed' else False, error_text=completed_text)


@app.route('/download_post')
def download_post():
    print('1')


# 
#
#
# SETTING'S FUNCTRIONS
#
#
#


@app.route('/set_video_quality', methods=['POST'])
def set_video_quality():
    data = request.get_json()

    database.set_download_quality(str(data['quality']))

    return jsonify({'quality': database.get_download_quality()})

@app.route('/get_video_quality', methods=['GET'])
def get_video_quality():
    return jsonify({'quality': database.get_download_quality()})

@app.route('/set_video_type', methods=['POST'])
def set_video_type():
    data = request.get_json()

    database.set_download_type(str(data['type']))
    return jsonify({'type': database.get_download_type()})

@app.route('/get_video_type', methods=['GET'])
def get_video_type():
    return jsonify({'type': database.get_download_type()})

@app.route('/set_browser_cookie', methods=['POST'])
def set_cookie_type():
    data = request.get_json()
    print(data)
    database.set_browser_cookie(str(data['type']))
    
    return jsonify({'type': database.get_browser_cookie()})

@app.route('/get_browser_cookie', methods=['GET'])
def get_cookie_type():
    return jsonify({'type': database.get_browser_cookie()})

@app.route('/set_directory_path', methods=['POST'])
def set_directory_path():
    global SAVE_PATH
    data = request.get_json()
    print(data['path'])
    database.set_download_path(json.dumps(str(data['path'])))
    return jsonify({'path': database.get_download_path()})


@app.route('/delete_history', methods=['POST'])
def delete_history_page():
    data = request.get_json()

    history = json.loads(database.get_history())

    for i in history:
        if i['path'] == data['path']:
            history.remove(i)

    database.set_history(json.dumps(history))
    if os.path.exists(data['path']):
        os.remove(data['path'])

    return jsonify({'q': 'q'})


if __name__ == "__main__":
    flaskwebgui.FlaskUI(app=app, server="flask", width=1200, height=700, port=13225).run()
