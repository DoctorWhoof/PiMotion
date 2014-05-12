# Version 0.21, 2014-05-11
# Script created by Leo Santos ( http://www.leosantos.com )
# Based on the picam.py script (by brainflakes, pageauc, peewee2 and Kesthal) and picamera examples.
# Dependencies: PIL and picamera. Run "sudo apt-get install python-imaging-tk" and "sudo apt-get install python-picamera" to get those.
# If you want .mp4 files instead of .h264, install gpac with "sudo apt-get install -y gpac" and set convertToMp4=True

import picamera
import cStringIO
import os
import sys
import time
import subprocess

from datetime import datetime
from PIL import Image

class Motion:

	def __init__( self ):

		self.captureWidth = 1920		# Set this to a high resolution. The video file will be scaled down using "width" and "height" to reduce noise.
		self.captureHeight = 1440		# Setting these to more than 1920x1440 seems to cause slowdown (records at a lower framerate)
							# To achieve 30 fps, set this to 1920x1080 or less (cropping will occur)
							
		self.bitrate = 0			# default is 17000000
		self.quantization = 20			# 10 is very high quality, 40 is very low. Use bitrate = 0 if quantization is non-zero.
		
		self.timerStart = 0			# only allows recording after this hour
		self.timerStop = 24			# only allows recording before this hour
							
		self.videoReduction = 2			# For best results set this to 2. A video recorded at 1920x1440 will be scaled by half and saved at 960x720, reducing noise.
		self.nightVideoReduction = 2		# scaling for nightMode.
		self.allowNightMode = False		# If True, light sensitivity is increased at the expense of image quality
		self.minimumTail = 10.0			# how long to keep testing for motion after last activity before commiting file

		self.framerate = 15			# Video file framerate.
		self.rotation = 0			# Rotates image (warning: cropping will occur!)
		self.filepath = "/home/"		# Local file path for video files
		self.prefix = ""			# Optional filename prefix
		self.convertToMp4 = False		# Requires GPAC to be installed. Removes original .h264 file
		self.useDateAsFolders = True		# Creates folders with current year, month and day, then saves file in the day folder.
		self.usePreviewWindow = False		# Whether the preview window will be opened when running inside X.
		
		self.testInterval = 0.25		# Interval at which stills are captured to test for motion
		self.testWidth = 96			# motion testing horizontal resolution. Use low values!
		self.testHeight = 72			# motion testing vertical resolution. Use low values!
		self.testStart = [ 0, 24 ]		# coordinates to start testing for motion
		self.testEnd = [ 80, 71 ]		# coordinates to finish testing for motion
		self.threshold = 20			# How much a pixel value has to change to consider it "motion"
		self.sensitivity = 25			# How many pixels have to change to trigger motion detection
							# Good day values with no wind: 20 and 25; with wind: at least 30 and 50; good night values: 15 and 20?
		
		self.camera = picamera.PiCamera()	# The camera object
		self.timeWithoutActivity = 0.0		# How long since last motion detection
		self.lastTimeWithoutActivity = datetime.now()	# How long since last frame without motion detected
		self.lastStartedRecording = 0.0		# The time at which the last motion detection occurred
		self.isRecording = False		# Is the camera currently recording? Prevents stopping a camera that is not recording.
		self.skip = True			# Skips the first frame, to prevent a false positive motion detection (since the first image1 is black)
		self.nightMode = False
		self.filename = ""
		self.mp4name = ""
		self.folderPath = ""
		self.image1 = Image.new( 'RGB', (self.testWidth, self.testHeight) )	# initializes image1
		self.image2 = Image.new( 'RGB', (self.testWidth, self.testHeight) )	# initializes image2
		self.buffer1 = self.image1.load()					# initializes image1 "raw data" buffer
		self.buffer2 = self.image2.load()					# initializes image2 "raw data" buffer
											# The difference here is that image1 is handled like a file stream, while the buffer is the actual RGB byte data, if I understand it correctly!

		self.camera.resolution = ( self.captureWidth, self.captureHeight )
		self.camera.framerate = self.framerate
		self.camera.rotation = self.rotation
		self.camera.meter_mode = "average"	# Values are: average, spot, matrix, backlit
	
	
	def StartRecording( self ):
		if not self.isRecording and not self.skip:
			timenow = datetime.now()
			
			if self.useDateAsFolders:
				self.folderPath = self.filepath +"%04d/%02d/%02d" % ( timenow.year, timenow.month, timenow.day )
				subprocess.call( [ "mkdir", "-p", self.folderPath ] )
				self.filename = self.folderPath + "/" + self.prefix + "%02d-%02d-%02d.h264" % ( timenow.hour, timenow.minute, timenow.second )
			else:
				self.filename = self.filepath + self.prefix + "%04d%02d%02d-%02d%02d%02d.h264" % ( timenow.year, timenow.month, timenow.day, timenow.hour, timenow.minute, timenow.second )
			
			if (( timenow.hour >= 20 ) or ( timenow.hour <= 5 )) and ( self.allowNightMode == True ):
				self.camera.exposure_mode = "night"
				self.camera.image_effect = "denoise"
				self.camera.exposure_compensation = 25
				self.camera.ISO = 800
				self.camera.brightness = 70
				self.camera.contrast = 50
				self.width = int( self.captureWidth / self.nightVideoReduction )
				self.height = int( self.captureHeight / self.nightVideoReduction )
				self.nightMode = True
			else:
				self.camera.exposure_mode = "auto"
				self.camera.image_effect = "none"
				self.camera.exposure_compensation = 0
				self.camera.ISO = 0
				self.camera.brightness = 50
				self.camera.contrast = 0
				self.width = int( self.captureWidth / self.videoReduction )
				self.height = int( self.captureHeight / self.videoReduction )
				self.nightMode = False

			self.mp4name = self.filename[:-4] + "mp4"
			self.camera.start_recording( self.filename, resize=( self.width, self.height), quantization = self.quantization, bitrate = self.bitrate )
			self.isRecording = True
			print "Started recording %s" % self.filename + " with night mode = " + str( self.nightMode )

	def StopRecording( self ):
		if self.isRecording:
			self.camera.stop_recording()
			self.isRecording = False
			motion.skip = True
			if self.convertToMp4:
				subprocess.call( [ "MP4Box","-fps",str(self.framerate),"-add",self.filename,self.mp4name ] )
				subprocess.call( [ "rm", self.filename ] )
				print "\n"
			else:
				print "Finished recording."

	def CaptureTestImage( self ):
		self.camera.image_effect = "none"
		self.image1 = self.image2
		self.buffer1 = self.buffer2
		imageData = cStringIO.StringIO()
		self.camera.capture( imageData, 'bmp', use_video_port=True, resize=( self.testWidth, self.testHeight) )
		imageData.seek(0)
		im = Image.open( imageData )
		buffer = im.load()
		imageData.close()
		return im, buffer

	def TestMotion( self ):
		changedPixels = 0
		self.image2, self.buffer2 = self.CaptureTestImage()
		for x in xrange( self.testStart[0], self.testEnd[0] ):
			for y in xrange( self.testStart[1], self.testEnd[1] ):
				pixdiff = abs( self.buffer1[x,y][1] - self.buffer2[x,y][1] )
				if pixdiff > self.threshold:
					changedPixels += 1
		if changedPixels > self.sensitivity:
			self.timeWithoutActivity = 0
			self.lastTimeWithoutActivity = datetime.now()
			return True
		else:
			self.timeWithoutActivity += ( datetime.now() - self.lastTimeWithoutActivity ).total_seconds()
			self.lastTimeWithoutActivity = datetime.now()
			return False

motion = Motion()
print "Warming up camera..."
time.sleep( 2 )
print "Camera ready to record. Use Ctrl+C to stop."

try:
	while True:
		timenow = datetime.now()
		if ( timenow.hour >= motion.timerStart ) and ( timenow.hour <= motion.timerStop ):
			if motion.usePreviewWindow:
				motion.camera.start_preview()
			if motion.TestMotion():
				motion.StartRecording()
			else:
				if ( motion.timeWithoutActivity > motion.minimumTail ):
					motion.StopRecording()
		time.sleep( motion.testInterval )
		motion.skip = False
except KeyboardInterrupt:
		print "\nClosing camera. Bye!"
		if motion.isRecording:
			motion.camera.stop_recording()
		motion.camera.stop_preview()
		motion.camera.close()
		sys.exit(1)
