# import the necessary packages
from __future__ import print_function
from EyePiVideoStream import EyePiVideoStream
from imutils.video import FPS
from picamera.array import PiRGBArray
from picamera import PiCamera
from OneEuroFilter import OneEuroFilter
import argparse
import imutils
import time
import cv2
import os
import sys
import numpy as np

import jsonpickle

from threading import Thread

import tornado.web
import tornado.websocket
import tornado.httpserver
import tornado.ioloop 

from EyeApplication import EyeApplication

### VARS
width = 320
height = 240
framebuffer = []
playhead = 0
yOffTop = -100
yOffBot = 50
xOffLeft = -80
xOffRight = +180
canny1 = 50
canny2 = 150
playhead = 0
fps = FPS().start()
isUpsideDown = False
inpaintRadius = 2
maxLoc = (0,0)
calfile = "calib_1465396371267.npz"

DEBUG = False
EQUALIZE = False
UNDISTORT = False
ENHANCE1 = False
ENHANCE2 = True
FILTERING = True
#METHOD = "flood"
METHOD = "threshold"

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

#### FUNCS

def auto_canny(image, sigma=0.33):
	# compute the median of the single channel pixel intensities
	v = np.median(image)
 
	# apply automatic Canny edge detection using the computed median
	lower = int(max(0, (1.0 - sigma) * v))
	upper = int(min(255, (1.0 + sigma) * v))
	edged = cv2.Canny(image, lower, upper)
 
	# return the edged image
	return edged

def adjust_gamma(image, gamma=1.0):
	# build a lookup table mapping the pixel values [0, 255] to
	# their adjusted gamma values
	invGamma = 1.0 / gamma
	table = np.array([((i / 255.0) ** invGamma) * 255
		for i in np.arange(0, 256)]).astype("uint8")
 
	# apply gamma correction using the lookup table
	return cv2.LUT(image, table)



#### INPUT SOURCE CODE

if(args["inputfile"] != None and len(args["inputfile"]) > 4):
	######### File mode
	ret = True
	cap = cv2.VideoCapture(args["inputfile"])


	print("Reading frames from file...")
	while(cap.isOpened() and ret):
	    ret, frame = cap.read()
	    if(frame is None):
	    	break

	    frame = imutils.resize(frame, width=400)
	    if(isUpsideDown):
	    	frame = cv2.flip(frame, 0)
	    framebuffer.append(frame)

	print("Frames read: "+str(len(framebuffer)))
	cap.release()
	fps = FPS().start()

elif(args["live"] != 1):
	######### Live capture mode
	# start LED strobing
	os.system('echo "21=%f" > /dev/pi-blaster' % (args["bright"]))

	# thread for camera
	print("[INFO] sampling THREADED frames from `picamera` module...")
	#vs = EyePiVideoStream().start()
	vs = EyePiVideoStream(resolution=(640,480), framerate=45).start()
	time.sleep(2.0)
	fps = FPS().start()

	while fps._numFrames < args["num_frames"]:
		# grab the frame from the threaded video stream and resize it
		# to have a maximum width of 400 pixels
		frame = vs.read()
		frame = imutils.resize(frame, width=400)	
		framebuffer.append(frame)
		fps.update()
		time.sleep(0.01)

	vs.stop()
	os.system('echo "21=0" > /dev/pi-blaster')
	#show number of captured frames
	print("Num of captured frames (playback will start now):")
	print(len(framebuffer))
else:
	######### Live processing mode
	# start LED strobing
	os.system('echo "21=%f" > /dev/pi-blaster' % (args["bright"]))

	# thread for camera
	print("Starting to sample frames from `picamera` module...")
	vs = EyePiVideoStream().start()
	#vs = PiVideoStream(resolution=(640,480), framerate=60).start()
	time.sleep(2.0)
	fps = FPS().start()	


##### MAIN ANALYTICS CODE ######
#
def analyzr():
	playhead = 0
	if(UNDISTORT):
		cf = np.load(calfile)
		print(cf.files)

	if(FILTERING):
		config = {
	        'freq': 120,       # Hz
	        'mincutoff': 0.05,  # FIXME
	        'beta': 6.0,       # FIXME
	        'dcutoff': 1.0     # this one should be ok
        }
		glintFilterX = OneEuroFilter(**config)
		glintFilterY = OneEuroFilter(**config)
		pupilFilterX = OneEuroFilter(**config)
		pupilFilterY = OneEuroFilter(**config)
		pupilFilterH = OneEuroFilter(**config)
		pupilFilterW = OneEuroFilter(**config)

	while True:
		# do teh heavy lifting here
		#
		# first: detect cornea reflex
		#
		if(args["live"] == 1):
			frame = vs.read()
			#frame = imutils.resize(frame, width=400)
		else:
			if(playhead > len(framebuffer)-2):
				playhead = 0
			else:
				playhead += 1

			frame = framebuffer[playhead].copy()	

		#convert to grayscale
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
		
		#undistort
		if(UNDISTORT):
			h,  w = gray.shape[:2]
			newcameramtx, roi=cv2.getOptimalNewCameraMatrix(cf['mtx'], cf['dist'],(w,h),1,(w,h))    
			gray = cv2.undistort(gray, cf['mtx'], cf['dist'], None, newcameramtx)

		#optional equalization
		if(EQUALIZE):		
			#gray = cv2.equalizeHist(gray);
			clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8,8))
			gray = clahe.apply(gray)		
		
		grayblur = cv2.blur(gray, (9,9))
		
		try:
			# find corneal glint location
			(minVal, maxVal, minLoc, maxLocTmp) = cv2.minMaxLoc(grayblur)
			#only use if bright spot is really bright, otherwise let filter interpolate
			if(maxVal > 180):
				maxLoc = maxLocTmp

			#filter
			#if(FILTERING):
				#maxLoc[0] = glintFilterX(maxLoc[0], int(round(time.time() * 1000)))
				#maxLoc[1] = glintFilterY(maxLoc[1], int(round(time.time() * 1000)))

			# extract eye area based on glint location
			eyearea = gray[maxLoc[1]+yOffTop:maxLoc[1]+yOffBot,maxLoc[0]+xOffLeft:maxLoc[0]+xOffRight]

			#optional contrast / brightness enhancement			
			if(ENHANCE1):
				phi = 1
				theta = 1
				eyearea = (maxVal/phi)*(eyearea/(maxVal/theta))**0.5
				eyearea = np.array(eyearea,dtype=np.uint8)

			if(ENHANCE2):
				ret, eyearea = cv2.threshold(eyearea, 17, 255, cv2.THRESH_TOZERO)
				ret, eyearea = cv2.threshold(eyearea, 160, 255, cv2.THRESH_TRUNC)
				eyearea = adjust_gamma(eyearea, 2.35)
			
			if args["display"] > 0:
				eyearea_copy = eyearea.copy()

			if(DEBUG):
				print("Sucessfully extracted eye area")
		except Exception as e:
			if(DEBUG):				
				print("Eye area extraction failed:")				
				print(str(e))

		try:
			# step 1 - inpaint glint in eyearea image to remove highlights
			ret,glintmask = cv2.threshold(eyearea, maxVal-50,maxVal,cv2.THRESH_BINARY)
			kernel = np.ones((3,3),np.uint8)
			glintmask = cv2.dilate(glintmask, kernel, iterations=1)
			eyearea = cv2.inpaint(eyearea, glintmask, inpaintRadius, cv2.INPAINT_NS)
			
			if args["display"] > 0:
				eyeinpaint = eyearea.copy()

			if(METHOD == "flood"):
				# step 2 - canny edge detection on eyearea			
				eyearea = auto_canny(eyearea, 0.44)
				eye_after_canny = eyearea.copy()
				kernel = np.ones((3,3),np.uint8)
				#eyearea = cv2.dilate(eyearea, kernel, iterations=2)
				eyearea_flood = eyearea.copy()
				
				if args["display"] > 0:
					eyearea_preflood = eyearea.copy()
				
				# step 3 - prepare mask used for flood fill
				h, w = eyearea.shape[:2]
				mask = np.zeros((h+2, w+2), np.uint8)
				 
				# step 4 - floodfill from point (0, 0)
				cv2.floodFill(eyearea_flood, mask, (w-1,h-1), 255);
				 
				# step 5 - invert floodfilled image
				ea_floodfill_inv = cv2.bitwise_not(eyearea_flood)
				 
				# step 6 - combine the two images to get the foreground.
				eyearea = eyearea | ea_floodfill_inv

			elif(METHOD == "threshold"):
				try:
					ret, eyearea = cv2.threshold(eyearea,50,255,cv2.THRESH_BINARY)
					
					if args["display"] > 0:
						eyeinpaint = eyearea.copy()
				except Exception as e:
					if(DEBUG):				
						print("Thresholding failed:")				
						print(str(e))
				
			
			# step 7 - find contours
			cnts2 = []			
			(_, cnts, hierarchy) = cv2.findContours(eyearea, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
			cnts = sorted(cnts, key = cv2.contourArea, reverse = True)			

			# loop over our contours for filtering
			for c in cnts:
				
				if(len(c) < 15):
					continue 

				x,y,w,h = cv2.boundingRect(c)				

				if(w == 0 or h == 0):
					continue

				if (float(w)/h > 2 or float(w)/h < 0.5):
					continue

				area = cv2.contourArea(c)
				#print("Area "+str(area))
				if (area < 600 or area > 4000):
					continue

				cmask = np.zeros(eyearea.shape,np.uint8)
				cv2.drawContours(cmask,[c],0,255,-1)
				mean_val = cv2.mean(eyearea, mask = cmask)
				
				#print("Mean "+str(mean_val))
				if(mean_val[0] > 90):
					continue
				
				cnts2.append(c)
	

			# sort again
			cnts2 = sorted(cnts2, key = cv2.contourArea, reverse = True)

			# easy approach
			try:
				ellipse = cv2.fitEllipse(cnts2[0])
			except:
				if(DEBUG):
					print("No ellipse fitting possible")


			# push data to socket srv
			outdata = {}
			#outglint = 
			if(ellipse != None):
				#filter

				if(FILTERING):
					ellipseX = pupilFilterX(ellipse[0][0], int(round(time.time() * 1000)))
					ellipseY = pupilFilterY(ellipse[0][1], int(round(time.time() * 1000)))
					ellipseH = pupilFilterH(ellipse[1][0], int(round(time.time() * 1000)))
					ellipseW = pupilFilterW(ellipse[1][1], int(round(time.time() * 1000)))
				else:
					ellipseX = ellipse[0][0]
					ellipseY = ellipse[0][1]
					ellipseH = ellipse[1][0]
					ellipseW = ellipse[1][1]

				outdata["center"] = (ellipseX, ellipseY)
				outdata["size"] = (ellipseH, ellipseW)
				outdata["glint"] = maxLoc
				outdata["xoffs"] = (xOffLeft, xOffRight)
				outdata["yoffs"] = (yOffTop, yOffBot)

			ws_app.wsSend(jsonpickle.encode(outdata))
		except Exception as e:
			outdata = {}
			ws_app.wsSend(jsonpickle.encode(outdata))
			if(DEBUG):
				print("Analyze frame fail")		
				print(str(e))

		#ws_app.wsSend(jsonpickle.encode(cnts2))

		# check to see if the frame should be displayed to our screen
		if args["display"] > 0:
			try:					
				#draw glint in full frame
				cv2.circle(frame, maxLoc, 5, (255, 220, 255), 1)
			except:
				#nothing
				if(DEBUG):
					print("disp glint frame err")		
			try:	
				h, w = eyearea_copy.shape[:2]
				dst = np.zeros((h,w,3), np.uint8) 
				#draw pupil ellipse
				cv2.ellipse(dst, ellipse,(0,255,0),1)
				#draw pupil center marker
				cv2.circle(dst, (int(ellipse[0][0]), int(ellipse[0][1])), 3, (255, 255, 0), 1)

				#draw glint in eyeframe
				cv2.circle(dst, (yOffTop*-1, xOffLeft*-1), 5, (255, 0, 255), 1)

				eyearea = cv2.cvtColor(eyearea, cv2.COLOR_GRAY2BGR)
				eyearea = cv2.addWeighted(eyearea,0.7,dst,0.3,0)

				cv2.imshow("DST", dst)
			except:
				#nothing
				if(DEBUG):
					print("disp dst superimpose err")		
			try:
				cv2.imshow("EyePreflood", eyearea)
				cv2.imshow("GrayInpaint", gray)
				cv2.imshow("EyeCopy", eyearea_copy)			
			except:
				if(DEBUG):
					print("proc disp err")

			try:
				cv2.imshow("EyeFlood", eyearea_flood)				
				cv2.imshow("EyeCanny", eye_after_canny)											
			except:
				#nothing
				if(DEBUG):
					print("track disp err")

			try:
				cv2.imshow("EyeInpaint", eyeinpaint)			
				cv2.imshow("InPaintMask", glintmask)							
			except:
				#nothing
				if(DEBUG):
					print("src disp err")

			try:
				if(len(cnts) > 0):
					cv2.drawContours(frame, cnts, -1, (0, 0, 255), 3)#, offset=(maxLoc[0]-80,maxLoc[1]-80))
				if(len(cnts2) > 0):
					cv2.drawContours(frame, [cnts2[0]], -1, (0, 255, 0), 3)#, offset=(maxLoc[0]-80,maxLoc[1]-80))
			except:
				if(DEBUG):
					print("draw contours err")

			cv2.imshow("Frame",frame)
			
			#cv2.imshow("Thresh", thresh)
			#cv2.imshow("ThreshInv", grayinv)
			key = cv2.waitKey(1) & 0xFF
	 
		# update the FPS counter
		fps.update()
		#print("Frame!")
 
def reportFPS():
	global fps
	fps.stop()
	print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
	print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
	fps = FPS().start()


### RUN CODE

#### SOCKETS 
ws_app = EyeApplication()
server = tornado.httpserver.HTTPServer(ws_app)
server.listen(8080)

#### PROCESSING THREAD
t = Thread(target=analyzr)
t.start()

#### GO!
tornado.ioloop.PeriodicCallback(reportFPS, 5000).start()
tornado.ioloop.IOLoop.instance().start()


###ENDE 
# stop the timer and display FPS information
fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
print(ellipse) 

input()

# do a bit of cleanup
cv2.destroyAllWindows()
vs.stop()
os.system('echo "21=0" > /dev/pi-blaster')



