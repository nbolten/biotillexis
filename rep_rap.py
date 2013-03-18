import time

from Printrun.printcore import printcore

#TODO: use gevent here to prevent competing uses of Printer?

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
        self.connected = True
        time.sleep(0.5)

    def disconnect(self):
        self.printcore.disconnect()
        self.connected = False

    def is_connected(self):
        return self.connected

    def move(self,xyz,z_first=True, relative=False):
        x = float(xyz[0])
        y = float(xyz[1])
        z = float(xyz[2])
        if relative:
            x = x + self.xyz[0]
            y = y + self.xyz[1]
            z = z + self.xyz[2]
        # Set to absolute positioning
        moves = ['G90']
        xy_move = 'G1 X%.1f Y%.1f F1000' % (x,y)
        z_move = 'G1 Z%.1f F100' % (z)
        if z_first:
            moves.append(z_move)
            moves.append(xy_move)
        else:
            moves.append(xy_move)
            moves.append(z_move)
        moves.append('M84')
        self.printcore.startprint(moves)
        self.xyz = (x,y,z)

    def home(self):
        self.printcore.startprint(['G28'])
        self.xyz = (0,0,0)

    def run_gcode(self, gcode_path):
        with open(gcode_path) as f:
            lines = f.readlines()
        processed = [x.split()[0].strip() for x in lines]
        print 'executing gcode: %s' % processed
        self.printcore.startprint(processed)
        # TODO: make it update self.xyz
