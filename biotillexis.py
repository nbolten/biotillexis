# Built-in libraries
import numpy
import time
import uuid

# OpenCV
import cv2.cv as cv
import cv2
from track_color import track_color

# Rep Rap Control
from rep_rap_control import Printer

# Networking / server
from netifaces import ifaddresses
import requests
from flask import Flask
from flask import jsonify
from flask import request
from flask import send_file

# gevent - async i/o
import gevent
import gevent.monkey
from gevent.pool import Group
from gevent.event import Event
from gevent.wsgi import WSGIServer

gevent.monkey.patch_all(thread=False)


# Settings - should probably go in a config
app_js = 'app.js'
app_html = 'app.html'
device_uuid = str(uuid.uuid5(uuid.uuid1(), 'biotillexis'))
device_status = 'ready'  # Alternative is 'logging'
device_state = 'none'  # What is this?
device_name = 'BioTillexis'
device_ip = ifaddresses('wlan0')[2][0]['addr']
device_port = 8432
manager_ip = 'http://bioturk.ee.washington.edu'
manager_port = '9090'

# gevent globals
device_acquired = Event()
device_logging = Event()
printing = Event()
g = Group()

# openCV camera setup
vid = cv2.VideoCapture(-1)

# initialize rep rap
printer = Printer()

# Flask object to control routes, server
app = Flask(__name__)

# Routes - intercepts requests and routes them to functions / responses
@app.route('/', methods=['GET', 'POST'])
def index():
    '''Intercepts requests directly to root of the device. Processes
       specific GET and POST requests and ignores everything else'''
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
        if not device_logging.is_set():
            device_logging.set()
            g.add(gevent.spawn(start_logging))
        return ''
    elif action == 'stopLog':
        device_logging.clear()
        return ''
    elif action == 'data_picture':
        g.add(gevent.spawn(single_picture))
    elif action == 'victoryLap':
        g.add(gevent.spawn(do_victory_lap))
        return ''
    elif action == 'home':
        g.add(gevent.spawn(do_home))
        return ''
    elif action == 'x_up':
        g.add(gevent.spawn(do_x_up))
        return ''
    elif action == 'x_down':
        g.add(gevent.spawn(do_x_down))
        return ''
    elif action == 'y_up':
        g.add(gevent.spawn(do_y_up))
        return ''
    elif action == 'y_down':
        g.add(gevent.spawn(do_y_down))
        return ''
    elif action == 'z_up':
        g.add(gevent.spawn(do_z_up))
        return ''
    elif action == 'z_down':
        g.add(gevent.spawn(do_z_down))
        return ''
    elif action == 'picture_position':
        g.add(gevent.spawn(picture_position))
        return ''
    elif action == 'dot1':
        xy = map_to_plate(522, 218)
        g.add(gevent.spawn(move_xyz(xy[0], xy[1], 4)))
        return ''
    elif action == 'dot2':
        xy = map_to_plate(780, 356)
        g.add(gevent.spawn(move_xyz(xy[0], xy[1], 4)))
        return ''

    else:
        print 'Unrecognized cmd'


# Functions (responses) that get run by routes
def start_logging():
    while device_logging.is_set():
        gevent.sleep(0)
        if not vid.isOpened():
            vid.open(-1)
        vid.set(cv.CV_CAP_PROP_FRAME_WIDTH, 1280)
        vid.set(cv.CV_CAP_PROP_FRAME_HEIGHT, 720)
        gevent.sleep(0.05)
        flag, im_array = vid.read()
        img = cv.fromarray(im_array)
        gevent.sleep(0.05)
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
        vid.release()
        gevent.sleep(4)


def single_picture():
    was_logging = device_logging.is_set()
    if was_logging:
        device_logging.clear()

    if not vid.isOpened():
        vid.open(-1)
    vid.set(cv.CV_CAP_PROP_FRAME_WIDTH, 1280)
    vid.set(cv.CV_CAP_PROP_FRAME_HEIGHT, 720)

    flag, im_array = vid.read()
    print 'image acquired'
    img_raw = cv.fromarray(im_array)
    cv.SaveImage('static/cam_home.jpeg', img_raw)

    img = cv2.imread('static/cam_home.jpeg')

    coord_ref, img_ref = track_color(img, 'pink')
    print 'reference coordinates: {}'.format(coord_ref)

    coord, img_green = track_color(img, 'green')

    cv2.imwrite('static/cam_tracked.jpeg', img_green)
    cmd_str = '/manager.php?action=storeBig&uuid='
    url = manager_ip + ':' + manager_port + cmd_str + device_uuid
    handle = open('static/cam_tracked.jpeg', 'rb')
    image = handle.read()
    print 'Logging picture'
    r = requests.post(url, data=image)
    print r.status_code
    handle.close()

    vid.release()
#    cv.Zero(img)

    print 'completed taking data picture'


def run_gcode(code_path):
    gevent.sleep(0)
    printer.connect()
    gevent.sleep(0.1)
    printer.run_gcode(code_path)
    printer.disconnect()


def do_victory_lap():
    gevent.sleep(0)
    run_gcode('gcode/victory_lap.gcode')


def do_home():
    gevent.sleep(0)
    printer.connect()
    printer.home()
    printer.disconnect()


def move_xyz(x, y, z):
    gevent.sleep(0)
    printer.connect()
    time.sleep(0.1)
    printer.move((x, y, z), z_first=False)
    printer.disconnect()


def do_x_up():
    gevent.sleep(0)
    printer.connect()
    time.sleep(0.1)
    print printer.xyz
    printer.move((10, 0, 0), relative=True)
    print printer.xyz
    printer.disconnect()


def do_x_down():
    gevent.sleep(0)
    printer.connect()
    printer.move((-10,0,0), relative=True)
    printer.disconnect()


def do_y_up():
    gevent.sleep(0)
    printer.connect()
    printer.move((0,10,0), relative=True)
    printer.disconnect()


def do_y_down():
    gevent.sleep(0)
    printer.connect()
    printer.move((0,-10,0), relative=True)
    printer.disconnect()


def do_z_up():
    gevent.sleep(0)
    printer.connect()
    printer.move((0,0,10), relative=True)
    printer.disconnect()


def do_z_down():
    gevent.sleep(0)
    printer.connect()
    printer.move((0,0,-10), relative=True)
    printer.disconnect()


def picture_position():
    gevent.sleep(0)
    printer.connect()
    printer.home()
    printer.move((30,98,35))
    printer.disconnect()


def find_colonies():
    # Move to picture position
    # Take picture
    # Run track_red, get back coordinates
    # Check values of track_red
    # Run track_green, get back coordinates
    # Run track_green output through map_to_plate
    # call pick_colonies with map_to_plate output
    pass


def map_to_plate(x, y):
    dot1_pixels = (351, 118)
    dot2_pixels = (894, 118)
    dot3_pixels = (920, 608)
    dot4_pixels = (334, 608)
    dot1_mm = (61, 87)
    dot2_mm = (18, 87)
    dot3_mm = (18, 125)
    dot4_mm = (61, 125)

    x_max_ref_pixels = dot1_pixels[0]
    x_min_ref_pixels = dot2_pixels[0]
    x_max_ref_mm = dot1_mm[0]
    x_min_ref_mm = dot2_mm[0]
    y_max_ref_pixels = dot1_pixels[1]
    y_min_ref_pixels = dot3_pixels[1]
    y_max_ref_mm = dot1_mm[1]
    y_min_ref_mm = dot3_mm[1]

    x_span_pixels = x_max_ref_pixels - x_min_ref_pixels
    x_span_mm = x_max_ref_mm - x_min_ref_mm
    y_span_pixels = y_max_ref_pixels - y_min_ref_pixels
    y_span_mm = y_max_ref_mm - y_min_ref_mm

    def x_trans(x_point):
        return -1* float(x_span_mm) / x_span_pixels * (x_max_ref_pixels - x_point) + x_max_ref_mm

    def y_trans(y_point):
        return -1 * float(y_span_mm) / y_span_pixels * (y_max_ref_pixels - y_point) + y_max_ref_mm

    move_x = x_trans(x)
    move_y = y_trans(y)
    return (move_x, move_y)


def pick_colonies(positions):
    for x in positions:
        pass
    pass


# Functions that are run at initialization
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
