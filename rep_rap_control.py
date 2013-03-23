import time

from printcore import printcore
#from Printrun.printcore import printcore

# TODO: Found the error that makes the printer inaccessible!
# RECV:  : Extruder switched off. MINTEMP triggered !
# Need to send 'M302' to prevent temperature errors!
# TODO: sed maximum feedrate on Z axis to 100 or something using M203 Z100
# TODO: M302 is working but if printer stays connected, will time out
# and the MINTEMP error will occur again (I think).
# Need to either disconnect after a period of inactivity,
# try sending M302 on an interval, or hack the firmware / thermister

# Settings (should go in config file eventually)
port = '/dev/ttyUSB0'
baud = 250000

class Printer:
    def __init__(self):
        self.printcore = printcore()
        self.connected = False
        self.printing = False
        self.xyz = False

    def connect(self):
        self.printcore.connect(port, baud)
        if not self.xyz:
            self.home()
        self.connected = True
        time.sleep(0.5)

    def disconnect(self):
        self.printcore.disconnect()
        self.connected = False

    def is_connected(self):
        return self.connected

    def move(self,xyz,z_first=True, relative=False):
        self.wait_for_printing()
        self.restart()
        time.sleep(0.1)
        x = float(xyz[0])
        y = float(xyz[1])
        z = float(xyz[2])
        if relative:
            if not self.xyz:
                self.home()
            x = x + self.xyz[0]
            y = y + self.xyz[1]
            z = z + self.xyz[2]
        # Set to absolute positioning
        moves = ['M302', 'G90']
        xy_move = 'G1 X%.1f Y%.1f F1000' % (x,y)
        z_move = 'G1 Z%.1f F100' % (z)
        if z_first:
            moves.append(z_move)
            moves.append(xy_move)
        else:
            moves.append(xy_move)
            moves.append(z_move)
        self.printcore.startprint(moves)
        self.xyz = (x,y,z)
        self.wait_for_printing()
        self.silence_printer()

    def home(self):
        self.wait_for_printing()
        self.restart()
        time.sleep(0.1)
        self.printcore.startprint(['M302', 'G28'])
        self.xyz = (0,0,0)
        self.wait_for_printing()
        self.printcore.send_now('G92')
        self.silence_printer()

    def run_gcode(self, gcode_path):
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
        self.wait_for_printing()
        self.printcore.startprint(['M84'])
        self.wait_for_printing()

    def wait_for_printing(self):
        time.sleep(0.01)
        printing_before = self.printcore.printing
        while self.printcore.printing:
            pass
        self.printing = not printing_before
        time.sleep(0.01)

    def restart(self):
        self.printcore.send_now('M999')
