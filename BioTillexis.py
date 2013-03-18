# Built-in libraries
#from os import environ
import time

# OpenCV
import cv2.cv as cv
import cv2

# Rep Rap Control
#from rep_rap import sender
from Printrun.printcore import printcore

# Useful libraries
from netifaces import ifaddresses
import requests

# Flask
from flask import Flask
from flask import jsonify
from flask import request
from flask import send_file

# gevent
import gevent
import gevent.monkey
from gevent.pool import Group
from gevent.event import Event
from gevent.wsgi import WSGIServer

gevent.monkey.patch_all()

app = Flask(__name__)

# Settings that should probably go in a config
app_js = 'app.js'
app_html = 'app.html'

#device_uuid = uuid.getnode() # This is better!
device_uuid = 'e5223631-2e7e-5ff4-bbb4-223d4e45da63'
device_status = 'ready'  # Alternative is 'logging'
device_state = 'none'  # What is this?
device_name = 'BioTillexis'
device_ip = ifaddresses('wlan0')[2][0]['addr']
device_port = 8432

manager_ip = 'http://bioturk.ee.washington.edu'
manager_port = '9090'

# Events for global communication of greenlets
device_acquired = Event()
logging = Event()
reprap_moving = Event()

# gevent group - master group for adding new processes
g = Group()

# openCV - camera setup
#vid = cv2.VideoCapture(-1)
cam = cv.CaptureFromCAM(-1)
cv.SetCaptureProperty(cam, cv.CV_CAP_PROP_FRAME_WIDTH, 640)
cv.SetCaptureProperty(cam, cv.CV_CAP_PROP_FRAME_HEIGHT, 360)
#cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_WIDTH, 1280)
#cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_HEIGHT, 720)
#cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_WIDTH, 640)
#cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_HEIGHT, 360)


@app.route('/', methods=['GET', 'POST'])
def index():
    action = request.args.get('cmd')
    print action
    if action == 'ping':
        return 'pong'
    elif action == 'acquire':
        device_acquired.set()
        return ''
    elif action == 'info':
        return jsonify(uuid=device_uuid,
                       status=device_status,
                       state=device_state,
                       name=device_name)
    elif action == 'getCode':
        return send_file(app_js)
    elif action == 'getHTML':
        return send_file(app_html)
    elif action == 'startLog':
        if not logging.is_set():
            logging.set()
            g.add(gevent.spawn(start_logging))
        return ''
    elif action == 'stopLog':
        logging.clear()
        return ''
    elif action == 'data_picture':
        g.add(gevent.spawn(data_picture))
    elif action == 'victoryLap':
        if not reprap_moving.is_set():
            reprap_moving.set()
            g.add(gevent.spawn(do_victory_lap))
        return ''
    elif action == 'home':
        if not reprap_moving.is_set():
            reprap_moving.set()
            g.add(gevent.spawn(do_home))
        return ''
    elif action == 'x_up':
        if not reprap_moving.is_set():
            reprap_moving.set()
            g.add(gevent.spawn(do_x_up))
        return ''
    elif action == 'x_down':
        if not reprap_moving.is_set():
            reprap_moving.set()
            g.add(gevent.spawn(do_x_down))
        return ''
    elif action == 'y_up':
        if not reprap_moving.is_set():
            reprap_moving.set()
            g.add(gevent.spawn(do_y_up))
        return ''
    elif action == 'y_down':
        if not reprap_moving.is_set():
            reprap_moving.set()
            g.add(gevent.spawn(do_y_down))
        return ''
    elif action == 'z_up':
        if not reprap_moving.is_set():
            reprap_moving.set()
            g.add(gevent.spawn(do_z_up))
        return ''
    elif action == 'z_down':
        if not reprap_moving.is_set():
            reprap_moving.set()
            g.add(gevent.spawn(do_z_down))
        return ''

    else:
        print 'Unrecognized cmd'


def start_logging():
    while logging.is_set():
        gevent.sleep(0)
#        # This causes a memory leak - flag and im_array are not garbage collected
#        # or 'vid.read()' is storing pictures.
#        if not vid.isOpened():
#            vid.open(-1)
#        flag, im_array = vid.read()
#        img = cv.fromarray(im_array)
#        cam = cv.CaptureFromCAM(-1)
        cv.WaitKey(100)
        img = cv.QueryFrame(cam)
        cv.WaitKey(10)
        cv.SaveImage('static/cam.jpeg', img)
        cmd_str = '/manager.php?action=storeBig&uuid='
        url = manager_ip + ':' + manager_port + cmd_str + device_uuid
        handle = open('static/cam.jpeg', 'rb')
        image = handle.read()
        print 'Logging picture'
        r = requests.post(url, data=image)
        print r.status_code
        handle.close()
        cv.Zero(img)
#        vid.release()
#        scanner.dump_all_objects('dump.json')
        gevent.sleep(4)


def data_picture():
    was_logging = logging.is_set()
    if was_logging:
        logging.clear()

    if not vid.isOpened():
        vid.open(-1)
    flag, im_array = vid.read()
    img = cv.fromarray(im_array)
    cv.SaveImage('static/data.jpeg', img)
    cv.Zero(img)
    vid.release()

    if was_logging:
        g.add(gevent.spawn(start_logging))
        logging.set()

    print 'completed taking data picture'


def run_gcode(code_path, home=False):
    gevent.sleep(0)
    rep_rap = printcore()
    rep_rap.connect('/dev/ttyUSB0', 250000)
    time.sleep(2)
    with open(code_path) as f:
        lines = f.readlines()
    # Remove comments and extra spaces
    lines = [x.split(';')[0].strip() for x in lines]
    print 'executing g code: %s' % lines
    if home:
        rep_rap.send_now('G28')
        time.sleep(3)
    rep_rap.startprint(lines)
    time.sleep(1)
    # This isn't being applied (motors off).
    # Is rep_rap.startprint(lines) non-blocking?
    rep_rap.send_now('M84')
    rep_rap.disconnect()
    reprap_moving.clear()


def do_victory_lap():
    gevent.sleep(0)
    run_gcode('gcode/victory_lap.gcode')


def do_home():
    gevent.sleep(0)
    run_gcode('gcode/home.gcode')


def do_x_up():
    gevent.sleep(0)
    run_gcode('gcode/x_up.gcode')


def do_x_down():
    gevent.sleep(0)
    run_gcode('gcode/x_down.gcode')


def do_y_up():
    gevent.sleep(0)
    run_gcode('gcode/y_up.gcode')


def do_y_down():
    gevent.sleep(0)
    run_gcode('gcode/y_down.gcode')


def do_z_up():
    gevent.sleep(0)
    run_gcode('gcode/z_up.gcode')


def do_z_down():
    gevent.sleep(0)
    run_gcode('gcode/z_down.gcode')


def announce():
    # Manually attach to bioturk manager
    while not device_acquired.is_set():
        gevent.sleep(3)
        payload = {'action': 'addDevice',
                   'port': device_port,
                   'addr': device_ip}
        requests.get(manager_ip + ':' + manager_port, params=payload)


def start_server():
    print 'Starting server'
    http = WSGIServer(('', device_port), app)
    http.serve_forever()


if __name__ == '__main__':
    g.add(gevent.spawn(announce))
    g.add(gevent.spawn(start_server))
    g.join()
