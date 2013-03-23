'''Module to make control of the RepRap more straightforward, work
around RepRap idiosyncrasies.'''
import time

from printcore import printcore

# The RepRap occasionally shuts itself down because of a MINTEMP error:
# RECV:  : Extruder switched off. MINTEMP triggered !
# Supposedly, 'M302' prevents this, but if it even works it's only temporary
# A more permanent solution is to drop the MINTEMP in the firmware
# TODO: set maximum feedrate on Z axis to 100 using M203 Z100 to prevent
# it from locking up

# Settings
port = '/dev/ttyUSB0'
baud = 250000


class Printer:
    '''Controls all necessary RepRap functions for abitrary xyz moves and
       calibrations.'''
    def __init__(self):
        # Core printer object
        self.printcore = printcore()
        # Statuses
        self.connected = False
        self.printing = False
        # Keep track of xyz position, since the RepRap apparently doesn't
        # make this easy to access
        self.xyz = False

    def connect(self):
        '''Connect to the Rep Rap and home by default (to calibrate).'''
        self.printcore.connect(port, baud)
        if not self.xyz:
            self.home()
        self.connected = True
        time.sleep(0.5)

    def disconnect(self):
        '''Disconnect from the RepRap - allow other software to control it.'''
        self.printcore.disconnect()
        self.connected = False

    def is_connected(self):
        '''Checks status of the RepRap connection'''
        return self.connected

    def move(self, xyz, z_first=True, relative=False):
        '''Arbitrary xyz movement method. Also have a 'relative' movement
           mode that uses the module's built-in xyz attribute to track
           movements.'''
        self.wait_for_printing()
        # By restarting the connection before every move, prevents MINTEMP
        # error from causing too much trouble
        self.restart()
        time.sleep(0.1)
        x = float(xyz[0])
        y = float(xyz[1])
        z = float(xyz[2])
        if relative:
            if not self.xyz:
                # Home if unaware of RepRap position
                self.home()
            x = x + self.xyz[0]
            y = y + self.xyz[1]
            z = z + self.xyz[2]
        # Attempt to prevent MINTEMP error and set to absolute positioning
        moves = ['M302', 'G90']
        # G code to move xyz. xy and z moves are separate (for now)
        # to avoid locking up the z axis with too fast of a move
        # TODO: Once max Z move speed can be set, allow simultaneous xyz moves.
        xy_move = 'G1 X%.1f Y%.1f F1000' % (x, y)
        z_move = 'G1 Z%.1f F100' % (z)
        # Move the z axis first or last
        if z_first:
            moves.append(z_move)
            moves.append(xy_move)
        else:
            moves.append(xy_move)
            moves.append(z_move)
        self.printcore.startprint(moves)
        self.xyz = (x, y, z)
        self.wait_for_printing()
        self.silence_printer()

    def home(self):
        '''Overly complicated home function - primarily due to working
           around RepRap MINTEMP error'''
        self.wait_for_printing()
        self.restart()
        time.sleep(0.1)
        self.printcore.startprint(['M302', 'G28'])
        self.xyz = (0, 0, 0)
        self.wait_for_printing()
        self.printcore.send_now('G92')
        self.silence_printer()

    def run_gcode(self, gcode_path):
        '''Sends arbitrary G code to the RepRap'''
        self.wait_for_printing()
        self.restart()
        time.sleep(0.1)
        with open(gcode_path) as f:
            lines = f.readlines()
        processed = [x.split(';')[0].strip() for x in lines]
        # M302 prevents cold extrude errors
        processed = ['M302'] + processed
        print 'executing gcode: %s' % processed
        self.printcore.startprint(processed)
        # TODO: make it update self.xyz
        self.wait_for_printing()
        self.silence_printer()

    def silence_printer(self):
        '''Turns off RepRap motors to prevent whiny noises.'''
        self.wait_for_printing()
        self.printcore.startprint(['M84'])
        self.wait_for_printing()

    def wait_for_printing(self):
        '''Wait that blocks until the RepRap is done moving / printing.'''
        time.sleep(0.01)
        printing_before = self.printcore.printing
        while self.printcore.printing:
            pass
        self.printing = not printing_before
        time.sleep(0.01)

    def restart(self):
        '''Restarts the RepRap. Implemented solely to prevent MINTEMP error.'''
        self.printcore.send_now('M999')
