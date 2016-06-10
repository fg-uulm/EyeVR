# import the necessary packages
from __future__ import print_function
from imutils.video.pivideostream import PiVideoStream
from imutils.video import FPS
from picamera.array import PiRGBArray
from picamera import PiCamera
import argparse
import imutils
import time
import cv2
import os
import numpy as np

### VARS
width = 320
height = 240
framebuffer = []
playhead = 0
yOffTop = -90
yOffBot = 50
xOffLeft = -80
xOffRight = +150
canny1 = 114
canny2 = 180

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
ap.add_argument("-i", "--inputfile", help="Input file name of eye recording to process")
args = vars(ap.parse_args())


 
### INPUT SOURCE CODE

if(len(args["inputfile"]) > 4):
	######### File mode
	ret = True
	cap = cv2.VideoCapture(args["inputfile"])

	while(cap.isOpened() and ret):
	    ret, frame = cap.read()
	    if(frame is None):
	    	break

	    frame = frame = imutils.resize(frame, width=400)
	    framebuffer.append(frame)

	    print("Reading frame ")
	    print(len(framebuffer))

	cap.release()
	fps = FPS().start()

else:
	######### Live capture mode
	# start LED strobing
	os.system('echo "21=%f" > /dev/pi-blaster' % (args["bright"]))

	# thread for camera
	print("[INFO] sampling THREADED frames from `picamera` module...")
	vs = PiVideoStream().start()
	#vs = PiVideoStream(resolution=(1296,730), framerate=49).start()
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
	print("Captured frames (playback will start now):")
	print(len(framebuffer))


##### MAIN ANALYTICS CODE ######
#
#
#
#
#
#

while True:
	# do teh heavy lifting here
	#
	# first: detect cornea reflex
	#
	if(playhead > len(framebuffer)-2):
		playhead = 0
	else:
		playhead += 1

	frame = framebuffer[playhead].copy()	
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	#gray = cv2.equalizeHist(gray);
	clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8,8))
	gray = clahe.apply(gray)		
	grayblur = cv2.blur(gray, (9,9))

	# find corneal glint location
	(minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(grayblur)

	# extract eye area based on glint location
	eyearea = gray[maxLoc[1]+yOffTop:maxLoc[1]+yOffBot,maxLoc[0]+xOffLeft:maxLoc[0]+xOffRight]
	eyearea_copy = eyearea.copy()

	# canny edge detection on eyearea
	eyearea = cv2.Canny(eyearea, canny1, canny2)
	eye_after_canny = eyearea.copy()
	kernel = np.ones((3,3),np.uint8)
	eyearea = cv2.dilate(eyearea, kernel, iterations=2)
	eyearea_flood = eyearea.copy()
	eyearea_preflood = eyearea.copy()
	
	# Mask used to flood filling.
	# Notice the size needs to be 2 pixels than the image.
	h, w = eyearea.shape[:2]
	mask = np.zeros((h+2, w+2), np.uint8)
	 
	# Floodfill from point (0, 0)
	cv2.floodFill(eyearea_flood, mask, (0,0), 255);
	 
	# Invert floodfilled image
	ea_floodfill_inv = cv2.bitwise_not(eyearea_flood)
	 
	# Combine the two images to get the foreground.
	eyearea = eyearea | ea_floodfill_inv
	
	cnts2 = []
	
	(_, cnts, _) = cv2.findContours(eyearea, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
	cnts = sorted(cnts, key = cv2.contourArea, reverse = True)
	
	'''
	# loop over our contours for filtering
	for c in cnts:
		
		if(cv2.contourArea(c) < 11):
			continue

		peri = cv2.arcLength(c, True)
		approx = cv2.approxPolyDP(c, 0.01 * peri, True)
 		
		if(not(cv2.isContourConvex(c))):
			continue

		#if len(approx) < 20:
		#	continue		
		
		cnts2.extend(c)
	'''

	# easy approach
	try:
		ellipse = cv2.fitEllipse(cnts[0])
	except:
		print("No ellipse fitting possible")

	# check to see if the frame should be displayed to our screen
	if args["display"] > 0:
		h, w = eyearea_copy.shape[:2]
		#print("H: "+str(h)+" W: "+str(w))
		dst = np.zeros((h,w,3), np.uint8) 

		#cv2.drawContours(image, contours, contourIdx, color[, thickness[, lineType[, hierarchy[, maxLevel[, offset]]]]])
		#cv2.drawContours(frame, [cnts[0]], -1, (0, 255, 0), 3, offset=(maxLoc[0]-80,maxLoc[1]-80))
		
		#draw pupil ellipse
		cv2.ellipse(dst, ellipse,(255,0,0),1)
		
		#draw pupil center marker
		cv2.circle(dst, (int(ellipse[0][0]+maxLoc[0]+xOffLeft), int(ellipse[0][1]+maxLoc[1]+yOffTop)), 3, (255, 255, 0), 2)
		
		#draw glint
		cv2.circle(dst, maxLoc, 5, (255, 0, 255), 2)
		#cv2.circle(eyearea, maxLocInv, 5, (255, 255, 0), 2)
		#cv2.circle(eyearea, getPupilCenter(eyearea), 5, (255, 0, 255), 2)
		
		eyearea_copy = cv2.cvtColor(eyearea_copy, cv2.COLOR_GRAY2BGR)
		eyearea_copy = cv2.addWeighted(eyearea_copy,0.5,dst,0.5,0)

		cv2.imshow("Frame",frame)
		cv2.imshow("EyeFlood", eyearea_flood)
		cv2.imshow("EyeCopy", eyearea_copy)
		cv2.imshow("EyeCanny", eye_after_canny)
		#cv2.imshow("EyePreflood", eyearea_preflood)
		cv2.imshow("DST", dst)
		#cv2.imshow("Thresh", thresh)
		#cv2.imshow("ThreshInv", grayinv)
		key = cv2.waitKey(1) & 0xFF
 
	# update the FPS counter
	fps.update()
	#print("Frame!")
 

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



