# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
from threading import Thread
import cv2
import time
 
class EyePiVideoStream:
	def __init__(self, resolution=(640, 480), framerate=60):
		# initialize the camera and stream
		self.camera = PiCamera()
		self.camera.resolution = (640,480)
		self.camera.framerate = 40
		time.sleep(2)		
		#self.camera.sensor_mode = 6	
		self.camera.exposure_mode = "off"
		g = self.camera.awb_gains
		self.camera.awb_mode = "off"
		self.camera.awb_gains = g
		self.camera.iso = 1600
		self.rawCapture = PiRGBArray(self.camera, size=(400,300))
		self.stream = self.camera.capture_continuous(self.rawCapture,
			format="bgr", use_video_port=True, resize=(400,300))
 
		# initialize the frame and the variable used to indicate
		# if the thread should be stopped
		self.frame = None
		self.stopped = False

	def start(self):
		# start the thread to read frames from the video stream
		print("Starting EyePiVideoStream")
		Thread(target=self.update, args=()).start()
		return self
 
	def update(self):
		# keep looping infinitely until the thread is stopped
		for f in self.stream:
			# grab the frame from the stream and clear the stream in
			# preparation for the next frame
			self.frame = f.array
			self.rawCapture.truncate(0)
 
			# if the thread indicator variable is set, stop the thread
			# and resource camera resources
			if self.stopped:
				self.stream.close()
				self.rawCapture.close()
				self.camera.close()
				return
	def read(self):
		# return the frame most recently read
		return self.frame
 
	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True