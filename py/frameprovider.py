from __future__ import print_function
import imutils
from tracker.EyePiVideoStream import EyePiVideoStream
import settings
import numpy as np
import glob
import cv2
import imutils
import os
import time

class FrameProvider:

    def __init__(self):
        print("Init Frameprovider")
        self.framebuffer = []
        self.frame = np.zeros((100, 100, 3), np.uint8)
        self.frameSkipped = True;
        self.vs = None
        self.playhead = 0
        self.lastFramePlayed = (time.time() * 1000)

    def nextFrame(self):
        currentTime = (time.time() * 1000)
        #print(str(currentTime - self.lastFramePlayed))

        if(settings.SETTINGS["mode"] == "live"):
            tmpFrame = self.vs.read()
            self.framebuffer.append(tmpFrame)
            if(len(self.framebuffer) > settings.SETTINGS["looplength"]):
                self.framebuffer.pop(0)
            return tmpFrame
        elif(settings.SETTINGS["mode"] == "file"):
            if(currentTime - self.lastFramePlayed) > 30.0:
                self.lastFramePlayed = currentTime
                if (self.playhead > len(self.framebuffer) - 2):
                    self.playhead = 0
                else:
                    self.playhead += 1
            return self.framebuffer[self.playhead].copy()
        elif(settings.SETTINGS["mode"] == "loop"):
            if (currentTime - self.lastFramePlayed) > 30.0:
                self.lastFramePlayed = currentTime
                if (self.playhead > len(self.framebuffer) - 2):
                    self.playhead = 0
                else:
                    self.playhead += 1
            return self.framebuffer[self.playhead].copy()
        else:
            return np.zeros((100, 100, 3), np.uint8)


    def fileList(self):
        files = glob.glob('*.h264')
        return files


    def loopToFile(self):
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter('rec.avi', fourcc, 40.0, (400, 300))

        for f in self.framebuffer:
            out.write(f)

        out.release()
        settings.logAppend("Wrote "+str(len(self.framebuffer))+" frames to file")


    def loadFile(self, filename):
        try:
            self.framebuffer = []
            print("Cleared framebuffer")
            cap = cv2.VideoCapture(filename)

            print("Reading frames from file...")
            ret = True
            frmCount = 0
            tmpbuffer = []
            while cap.isOpened() and ret:
                ret, frame = cap.read()
                if (frame is None):
                    break

                if(settings.SETTINGS["resize"]):
                    frame = imutils.resize(frame, width=400)
                #if(settings.SETTINGS["flip"]):
                    #frame = cv2.flip(frame, 0)
                tmpbuffer.append(frame)
                frmCount += 1

            self.framebuffer = tmpbuffer
            print("Frames read: " + str(len(self.framebuffer)) + "/" +str(frmCount))
            cap.release()
            return True
        except Exception as e:
            print("Failed reading file: "+str(e))
            if (len(self.framebuffer) < 1):
                self.framebuffer.append(np.zeros((100, 100, 3), np.uint8))
            return False

    def switchMode(self, mode):
        if(mode in ["live", "file", "loop"]):
            settings.SETTINGS["mode"] == "off" #temp disable processing
            if(mode == "live"):
                # start LED strobing
                os.system('echo "21=%f" > /dev/pi-blaster' % (settings.SETTINGS["brightness"]))
                self.vs = EyePiVideoStream(resolution=(640, 480), framerate=45).start()
                time.sleep(1.0)
                #clear framebuffer
                self.framebuffer = []
            elif (mode == "loop"):
                print("Switching to loop mode")
                self.vs.stop()

                if (len(self.framebuffer) < 1):
                    self.framebuffer.append(np.zeros((100, 100, 3), np.uint8))
                self.playhead = 0

                os.system('echo "21=0" > /dev/pi-blaster')
                print("Switched to loop mode, "+str(len(self.framebuffer))+" frames in buffer")
            elif(mode == "file"):
                self.vs.stop()
                self.loadFile(settings.SETTINGS['currentFile'])
                self.playhead = 0
                os.system('echo "21=0" > /dev/pi-blaster')

            settings.SETTINGS["mode"] = mode;
            self.frameSkipped = True

        else:
            print("No such mode: "+mode)