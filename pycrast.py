# coding=utf-8

from flask import Flask, redirect, render_template
import webui
import threading
import win32process
import win32api
import win32gui
import time
import wmi
import pythoncom
import re
from urlparse import urlparse
import pickle
import copy
import string

update_frequency = 1 #seconds
pickle_frequency = 15 #seconds
pickle_filename = "apps.dat"
firefox_session_location = r"C:\Users\cnwnj1.CNW\AppData\Roaming\Mozilla\Firefox\Profiles\kr30down.default\sessionstore.js"
firefox_session_regex = r'"url":"([^"]*)","title":"([^"]*)"'

class Bar(object):
    def __init__(self, percent, color):
        super(Bar, self).__init__()
        self.percent = percent
        self.color = color


class State(object):
    last_input_time = win32api.GetLastInputInfo()
    applications = {}
    inactive_updates = 0

class Application(object):
    def __init__(self, process, is_productive=None, seconds_active=0):
        super(Application, self).__init__()
        self.process = process
        self.is_productive = is_productive
        self.seconds_active = seconds_active

    def __eq__(self, other) : 
        return self.__dict__ == other.__dict__

app = Flask(__name__)
ui = webui.WebUI(app, debug=True)

def sanitize(s):
    return strip_non_ascii(s).replace(' ', '')

def strip_non_ascii(s):
    return filter(lambda x: x in string.printable, s)

def get_active_window_hwnd():
    return win32gui.GetForegroundWindow()

def get_window_title(hwnd):
    return win32gui.GetWindowText(hwnd)

def get_window_pid(hwnd):
    return win32process.GetWindowThreadProcessId(hwnd)[1]

def get_process_name(pid):
    for p in wmi.WMI().query('SELECT Name FROM Win32_Process WHERE ProcessId = {}'.format(pid)):
        return p.Name
    return None

def get_current_app():
    return get_process_name(get_window_pid(get_active_window_hwnd()))

def get_current_url():
    with open(firefox_session_location, 'r') as session_file:
        session_data = session_file.read()

    sites = re.findall(firefox_session_regex, session_data)

    window_name = sanitize(get_window_title(get_active_window_hwnd()))

    for url, title in sites:
        title = sanitize(title)
        
        if window_name.startswith(title):
            return urlparse(url).netloc
    return "firefox.exe"

def update_state():
    start_timer(update_frequency, update_state)
    print "Running update"
    pythoncom.CoInitialize()

    current_input_time = win32api.GetLastInputInfo() 

    if current_input_time - State.last_input_time == 0:
        State.inactive_updates += 1
    else:
        State.inactive_updates = 0

    if State.inactive_updates >= 10:
        print "Inactive"
        return None
    
    State.last_input_time = win32api.GetLastInputInfo()
    current_app = get_current_app()

    if current_app == "firefox.exe":
        current_app = get_current_url()

    if not current_app:
        print current_app
        print get_current_app()
        return None

    if current_app in State.applications:
        State.applications[current_app].seconds_active += update_frequency
    else:
        State.applications[current_app] = Application(current_app, seconds_active=update_frequency)

    print current_app

def pickle_apps(filename=pickle_filename, obj=None):
    start_timer(pickle_frequency, pickle_apps)

    if not obj:
        obj = State.applications

    with open(filename, 'w') as f:
        print "Saving apps!"
        pickling_apps = copy.deepcopy(obj)

        for k, v in pickling_apps.items():
            v.seconds_active = 0

        pickle.dump(pickling_apps, f)

def load_pickle(filename=pickle_filename):
    try:
        with open(filename) as f:
            print "{} found and loaded!".format(filename)
            return pickle.load(f)
    except IOError:
        return {}

def start_timer(frequency, function):
    t = threading.Timer(frequency, function)
    t.daemon = True
    t.start()

@app.route('/')
def main():
    processes = [app.process for app in State.applications.values() if app.is_productive == None]

    values = [(True, "#34C6CD"), (False, "#FF7600")]

    bars = []
    for value, color in values:
        raw_sum = sum([app.seconds_active for app in State.applications.values() if app.is_productive == value])
        bars.append(Bar(raw_sum, color))

    bar_sum = sum(bar.percent for bar in bars)

    for bar in bars:
        bar.percent = float(bar.percent) / (bar_sum or 1) * 100

    return render_template("pycrast.html", bars=bars, processes=processes)


@app.route('/<process>/<is_productive>/')
def set_productivity(process, is_productive):
    State.applications[process].is_productive = bool(is_productive == "True")
    return redirect('/')


if __name__ == '__main__':
    State.applications = load_pickle()
    start_timer(pickle_frequency, pickle_apps)
    update_state()
    get_current_url()
    ui.run()
    pickle_apps()
