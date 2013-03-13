# Built-in libraries
from os import environ

# OpenCV
import cv2.cv as cv

# Rep Rap Control
from rep_rap import sender

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
device_status = 'ready' # Alternative is 'logging'
device_state = 'none' # What is this?
device_name = 'BioTillexis'
device_ip = ifaddresses('wlan0')[2][0]['addr']
device_port = 8432

manager_ip = 'http://bioturk.ee.washington.edu'
manager_port = '9090'

# Events for global communication of greenlets
device_acquired = Event()
logging = Event()
victorylapping = Event()

# gevent group - master group for adding new processes 
g = Group()

# openCV - camera setup
capture = cv.CaptureFromCAM(-1)
cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_WIDTH, 320)
cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_HEIGHT, 180)


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
    elif action == 'victoryLap':
        if not victorylapping.is_set():
            victorylapping.set()
            g.add(gevent.spawn(victory_lap))
        return ''
    
    else:
        print 'Unrecognized cmd'


def start_logging():
    while logging.is_set():
        img = cv.QueryFrame(capture)
        cv.SaveImage('static/latest.jpeg',img)
        cmd_str = '/manager.php?action=storeBig&uuid='
        url = manager_ip + ':' + manager_port + cmd_str + device_uuid
        handle = open('static/latest.jpeg', 'rb')
        image = handle.read()
        r = requests.post(url, data=image)
        handle.close()
        cv.Zero(img)
        print r.status_code
        print 'Logging picture'
        gevent.sleep(1)


def victory_lap():
    gevent.sleep(0)
    sender.run_gcode('gcode/victory_lap.gcode')
    victorylapping.clear()


def announce():
    # Manually attach to bioturk manager
    while not device_acquired.is_set():
        gevent.sleep(3)
        payload = {'action': 'addDevice',
                   'port': device_port,
                   'addr': device_ip}
        req = requests.get(manager_ip + ':' + manager_port, params=payload)


def start_server():
    print 'Starting server'
    http = WSGIServer(('', device_port), app)
    http.serve_forever()


if __name__ == '__main__':
    g.add(gevent.spawn(announce))
    g.add(gevent.spawn(start_server))
    g.join()
