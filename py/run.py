# import all app parts
import tracker.tracker
import server.trackerserver
import tornado.ioloop
import argparse
import settings
import multiprocessing
import time
from frameprovider import FrameProvider
from threading import Thread


def print_time( threadName, delay):
   count = 0
   while count < 5:
      time.sleep(delay)
      count += 1
      print("%s: %s", threadName, time.ctime(time.time()))



# argparsr
ap = argparse.ArgumentParser()
ap.add_argument("-n", "--num-frames", type=int, default=100,
                help="# of frames to loop over for FPS test")
ap.add_argument("-d", "--display", type=int, default=-1,
                help="Whether or not frames should be displayed")
ap.add_argument("-b", "--bright", type=float, default=0.5,
                help="LED brightness")
ap.add_argument("-f", "--freq", type=int, default=100,
                help="PWM frequency")
ap.add_argument("-l", "--live", type=int, default=0,
                help="Live processing mode")
ap.add_argument("-i", "--inputfile", help="Input file name of eye recording to process")
args = vars(ap.parse_args())

# start frameprovider
f = FrameProvider()
f.switchMode("live")
settings.FRMPROV = f

# start tracker
tr = tracker.tracker.Tracker()
t = Thread(target=tr.analyzr)
t.start()
#p = multiprocessing.Process(target=tracker.tracker.Tracker.analyzr())
#p.start()

# start server
app = server.trackerserver.make_app()
app.listen(8888)
tornado.ioloop.IOLoop.current().start()


