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
from image_mapper import map_to_plate

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

# Settings - should go in a config eventually
# Calibration settings:
# Position (in Rep Rap mm) from which to take a calibration picture
picture_home_position = (30, 73, 30)
# Positions (in Rep Rap mm) where the pipet tip is directly above each
# pink dot. The order is upper left, upper right, bottom right, bottom left.
reference_points = [(50, 30, 0),
                    (10, 27, 0),
                    (10, 66, 0),
                    (53, 66, 0)]
# Device / network / manager settings
app_js = 'app.js'
app_html = 'app.html'
device_uuid = str(uuid.uuid5(uuid.uuid1(), 'biotillexis'))
device_status = 'ready'  # Alternative is 'logging'
device_state = 'none'  # Does not change (yet)
device_name = 'biotillexis'
# Strictly uses wlan0 for now
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


# TODO: upon approval of colony selection, send cropped images of each colony
# along with metadata to the manager
# Routes - intercepts requests and routes them to functions / responses
@app.route('/', methods=['GET', 'POST'])
def index():
    '''Intercepts requests directly to root of the device. Processes
       specific GET and POST requests and ignores everything else'''
    # TODO: reduce redundancy by making GET requests from the app
    # use parameters (e.g. remove redundancies between x_up and x_down).
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
        g.add(gevent.spawn(move_green))
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
        xy = map_to_plate(522, 218, reference_points=reference_points)
        g.add(gevent.spawn(move_xyz(xy, 0)))
        return ''
    elif action == 'dot2':
        xy = map_to_plate(780, 356, reference_points=reference_points)
        g.add(gevent.spawn(move_xyz(xy, 0)))
        return ''

    else:
        print 'Unrecognized cmd'


# Functions (responses) that get run by routes
# Logging:
def start_logging():
    '''Takes a picture using opencv and sends it to the manager
       every 4 seconds.'''
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


# Rep Rap movement
def move_green():
    '''Acquires a picture, finds the locations of pink and green dots,
       then moves to the positions of the green dots. Proper identification
       of green dots is not yet working, nor is the move loop (which
       should be straightforward).'''
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
    print 'green dot coordinates: {}'.format(coord)

    cv2.imwrite('static/cam_tracked.jpeg', img_green)
    cmd_str = '/manager.php?action=storeBig&uuid='
    url = manager_ip + ':' + manager_port + cmd_str + device_uuid
    handle = open('static/cam_tracked.jpeg', 'rb')
    image = handle.read()
    print 'Logging picture'
    r = requests.post(url, data=image)
    print 'Returned status code {}'.format(r.status_code)
    handle.close()
    vid.release()

    # TODO: move to green dots here using 'coord' variable and move.xyz
    print 'Finished green dot loop'


def run_gcode(code_path):
    '''Helper function to send g code (Rep Rap movement language) to
       the Rep Rap.'''
    gevent.sleep(0)
    printer.connect()
    gevent.sleep(0.1)
    printer.run_gcode(code_path)
    printer.disconnect()


def do_victory_lap():
    '''Demo function - sets the rep rap on a loop around the bed.'''
    gevent.sleep(0)
    run_gcode('gcode/victory_lap.gcode')


def do_home():
    '''Homes the Rep Rap. Effectively recalibrates the Rep Rap's movements.'''
    gevent.sleep(0)
    printer.connect()
    printer.home()
    printer.disconnect()


def move_xyz(x, y, z, z_first=False):
    '''Helper function to move to any arbitrary x, y, z location.'''
    gevent.sleep(0)
    printer.connect()
    time.sleep(0.1)
    printer.move((x, y, z), z_first=z_first)
    printer.disconnect()


def do_x_up():
    '''Demo function - move the Rep Rap 10 units in the x direction.'''
    gevent.sleep(0)
    printer.connect()
    time.sleep(0.1)
    print printer.xyz
    printer.move((10, 0, 0), relative=True)
    print printer.xyz
    printer.disconnect()


def do_x_down():
    '''Demo function - move the Rep Rap -10 units in the x direction.'''
    gevent.sleep(0)
    printer.connect()
    printer.move((-10, 0, 0), relative=True)
    printer.disconnect()


def do_y_up():
    '''Demo function - move the Rep Rap 10 units in the y direction.'''
    gevent.sleep(0)
    printer.connect()
    printer.move((0, 10, 0), relative=True)
    printer.disconnect()


def do_y_down():
    '''Demo function - move the Rep Rap -10 units in the y direction.'''
    gevent.sleep(0)
    printer.connect()
    printer.move((0, -10, 0), relative=True)
    printer.disconnect()


def do_z_up():
    '''Demo function - move the Rep Rap 10 units in the z direction.'''
    gevent.sleep(0)
    printer.connect()
    printer.move((0, 0, 10), relative=True)
    printer.disconnect()


def do_z_down():
    '''Demo function - move the Rep Rap -10 units in the z direction.'''
    gevent.sleep(0)
    printer.connect()
    printer.move((0, 0, -10), relative=True)
    printer.disconnect()


def picture_position():
    '''Moves the Rep Rap to a standardized location for acquiring a
       calibration / homing image.'''
    gevent.sleep(0)
    printer.connect()
    printer.home()
    printer.move(picture_home_position)
    printer.disconnect()


def find_colonies():
    '''This function will supercede move_green once colony identification
       is working'''
    # Pseudocode:
    # Move to picture position
    # Take picture
    # Run track_red, get back coordinates
    # Check values of track_red
    # Run track_green, get back coordinates
    # Run track_green output through map_to_plate
    # call pick_colonies with map_to_plate output
    pass


def pick_colonies(positions):
    '''This function will have the rep rap pick colonies at inputted xy
       coordinates.'''
    for x in positions:
        pass
    pass


# Server initialization functions
def announce():
    '''Attempts to connect to the manager every 3 seconds until the device
       is acquired.'''
    while not device_acquired.is_set():
        gevent.sleep(3)
        payload = {'action': 'addDevice',
                   'port': device_port,
                   'addr': device_ip}
        requests.get(manager_ip + ':' + manager_port, params=payload)


def start_server():
    '''Starts a minimal Werkzeug server. This is not a robust server
       and should be replaced eventually with something like CherryPy.'''
    print 'Starting server'
    http = WSGIServer(('', device_port), app)
    http.serve_forever()


if __name__ == '__main__':
    '''Launch the biotillexis device - start the server and send
       an acquisition request to manager.'''
    g.add(gevent.spawn(announce))
    g.add(gevent.spawn(start_server))
    g.join()
