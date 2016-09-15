import numpy as np
import cv2
import glob
from EyePiVideoStream import EyePiVideoStream
from imutils.video import FPS
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import os

# termination criteria
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((6*7,3), np.float32)
objp[:,:2] = np.mgrid[0:7,0:6].T.reshape(-1,2)

# Arrays to store object points and image points from all the images.
objpoints = [] # 3d point in real world space
imgpoints = [] # 2d points in image plane.

images = glob.glob('*.png')

framebuffer = []


os.system('echo "21=1" > /dev/pi-blaster')
# thread for camera
print("[INFO] sampling THREADED frames from `picamera` module...")
#vs = EyePiVideoStream().start()
vs = EyePiVideoStream(resolution=(640,480), framerate=45).start()
time.sleep(2)
fps = FPS().start()

#show number of captured frames
print("Num of captured frames (playback will start now):")
print(len(framebuffer))

for fname in images:
#while len(objpoints) < 25:
    #frame = vs.read()
    frame = cv2.imread(fname)
    gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    #cv2.imshow('frame',gray)
    #gray = cv2.equalizeHist(gray)
    fps.update()

    # Find the chess board corners
    ret, corners = cv2.findChessboardCorners(gray, (7,6),None)

    # If found, add object points, image points (after refining them)
    if ret == True:
        objpoints.append(objp)

        corners2 = cv2.cornerSubPix(gray,corners,(11,11),(-1,-1),criteria)
        imgpoints.append(corners2)

        # Draw and display the corners
        millis = str(int(round(time.time() * 1000)))
        #cv2.imwrite(millis+".png",frame)
        frame = cv2.drawChessboardCorners(frame, (7,6), corners2,ret)               
        #cv2.imshow('frame',frame)
        print("collected chessboard sample, now having "+str(len(objpoints)))     
    else:
        print("no chessboard!")
    key = cv2.waitKey(1) & 0xFF     



ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1],None,None)
print("Calib succeeded")
print(mtx)
print(dist)
print(rvecs)
print(tvecs)

mean_error = 0
tot_error = 0
for i in range(len(objpoints)):
    imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], mtx, dist)
    error = cv2.norm(imgpoints[i],imgpoints2, cv2.NORM_L2)/len(imgpoints2)
    tot_error += error

print("Total Reprojection Error: ", mean_error/len(objpoints))

filename = "calib_"+str(int(round(time.time() * 1000)))
np.savez(filename, mtx=mtx, dist=dist, rvecs=rvecs, tvecs=tvecs)

while True:
    frame = vs.read()   
    gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    #cv2.imshow("Frame",gray)
    h,  w = frame.shape[:2]
    newcameramtx, roi=cv2.getOptimalNewCameraMatrix(mtx,dist,(w,h),1,(w,h))    
    dst = cv2.undistort(gray, mtx, dist, None, newcameramtx)
    cv2.imshow("Undistort",dst)
    key = cv2.waitKey(1) & 0xFF
    #print("Showing")

vs.stop()
fps.stop()
os.system('echo "21=0" > /dev/pi-blaster')

input()
cv2.destroyAllWindows()
vs.stop()