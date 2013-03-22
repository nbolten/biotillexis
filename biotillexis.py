# Built-in libraries
#from os import environ
import time
import numpy

# OpenCV
import cv2.cv as cv
import cv2

# Rep Rap Control
from rep_rap_control import Printer

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

gevent.monkey.patch_all(thread=False)

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

# gevent group - master group for adding new processes
g = Group()

# openCV - camera setup
vid = cv2.VideoCapture(-1)
#cam = cv.CaptureFromCAM(-1)
#cv.SetCaptureProperty(cam, cv.CV_CAP_PROP_FRAME_WIDTH, 640)
#cv.SetCaptureProperty(cam, cv.CV_CAP_PROP_FRAME_HEIGHT, 360)

# initialize rep rap
printer = Printer()

# Routes - intercepts requests and routes them to functions / responses
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
    while logging.is_set():
        gevent.sleep(0)
        if not vid.isOpened():
            vid.open(-1)
        vid.set(cv.CV_CAP_PROP_FRAME_WIDTH, 1280)
        vid.set(cv.CV_CAP_PROP_FRAME_HEIGHT, 720)
        gevent.sleep(0)
        flag, im_array = vid.read()
        gevent.sleep(0)
        img = cv.fromarray(im_array)
        gevent.sleep(0)
        cv.SaveImage('static/cam.jpeg', img)
        gevent.sleep(0)
        cmd_str = '/manager.php?action=storeBig&uuid='
        gevent.sleep(0)
        url = manager_ip + ':' + manager_port + cmd_str + device_uuid
        gevent.sleep(0)
        handle = open('static/cam.jpeg', 'rb')
        gevent.sleep(0)
        image = handle.read()
        gevent.sleep(0)
        print 'Logging picture'
        gevent.sleep(0)
        r = requests.post(url, data=image)
        gevent.sleep(0)
        print r.status_code
        gevent.sleep(0)
        handle.close()
        gevent.sleep(0)
        cv.Zero(img)
        gevent.sleep(0)
        vid.release()
        gevent.sleep(4)


def single_picture():
    was_logging = logging.is_set()
    if was_logging:
        logging.clear()

    if not vid.isOpened():
        vid.open(-1)
    vid.set(cv.CV_CAP_PROP_FRAME_WIDTH, 1280)
    vid.set(cv.CV_CAP_PROP_FRAME_HEIGHT, 720)

    flag, im_array = vid.read()
    print 'image acquired'
    img_raw = cv.fromarray(im_array)
    cv.SaveImage('static/cam_home.jpeg', img_raw)

    img = cv2.imread('static/cam_home.jpeg')

    print 'thresholding green'
    GREEN_MIN = numpy.array([70, 210, 100],numpy.uint8)
    GREEN_MAX = numpy.array([100, 250, 200],numpy.uint8)
    hsv_img = cv2.cvtColor(img,cv2.COLOR_BGR2HSV)
    frame_threshed = cv2.inRange(hsv_img, GREEN_MIN, GREEN_MAX)
    print 'finding contours'
    contours, hierarchy = cv2.findContours(frame_threshed,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(img,contours,-1,(0,255,0),5)
    print 'writing image'
    cv2.imwrite('static/cam.jpeg', img)

    cmd_str = '/manager.php?action=storeBig&uuid='
    url = manager_ip + ':' + manager_port + cmd_str + device_uuid
    handle = open('static/cam.jpeg', 'rb')
    image = handle.read()
    print 'Logging picture'
    r = requests.post(url, data=image)
    print r.status_code
    handle.close()

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
