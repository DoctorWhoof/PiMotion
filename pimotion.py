# Version 0.1, 2014-04-26
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
							# For best results (by far) set width and height to exactly half camera.resolution. Anything else may result in cropping and noisy images.
		self.width = 960			# Video file horizontal resolution
		self.height = 720			# Video file vertical resolution
		self.framerate = 15			# Video file framerate.
		self.minimumLength = 10			# Minimum duration of a recording after motion stops. Lower number results in more files, higher number results in fewer, longer files.
		self.rotation = 0			# Rotates image (warning: cropping will occur!)
		self.filepath = "/home/leo/camera/"	# Local file path for video files
		self.prefix = ""			# Optional filename prefix
		self.testInterval = 0.5			# Interval at which stills are captured to test for motion
		self.tWidth = 96			# motion testing horizontal resolution. Use low values!
		self.tHeight = 72			# motion testing vertical resolution. Use low values!
		self.threshold = 15			# How much a pixel value has to change to consider it "motion"
		self.sensitivity = 25			# How many pixels have to change to trigger motion detection
		
		self.convertToMp4 = False		# Requires GPAC to be installed. Removes original .h264 file
		self.useDateAsFolders = True		# Creates folders with current year, month and day, then saves file in the day folder.

		self.camera = picamera.PiCamera()	# The camera object
		self.timeWithoutActivity = 0.0		# How long since last motion detection
		self.lastActiveTime = 0.0		# The time at which the last motion detection occurred
		self.isRecording = False		# Is the camera currently recording? Prevents stopping a camera that is not recording.
		self.skip = True			# Skips the first frame, to prevent a false positive motion detection (since the first image1 is black)
		self.filename = ""
		self.mp4name = ""
		self.folderPath = ""

		self.camera.resolution = ( 1920, 1440 )	# Set this to a high resolution, scale the video file down using "width" and "height" to reduce noise.
							# Setting this to more than 1920x1440 seems to cause slowdown (records at a lower framerate)
							# To achieve 30 fps, set this to 1920x1080 or less (cropping will occur)
												
		self.camera.framerate = self.framerate	# Sets camera framerate
		self.camera.rotation = self.rotation	# Sets camera rotation
	
		self.image1 = Image.new( 'RGB', (self.tWidth, self.tHeight) )	# initializes image1
		self.image2 = Image.new( 'RGB', (self.tWidth, self.tHeight) )	# initializes image2
		self.buffer1 = self.image1.load()				# initializes image1 "raw data" buffer
		self.buffer2 = self.image2.load()				# initializes image2 "raw data" buffer
																		# The difference here is that image1 is handled like a file stream, while the buffer is the actual RGB byte data, if I understand it correctly!
	
	def StartRecording( self ):
		if not self.isRecording and not self.skip:
			timenow = datetime.now()
			
			if self.useDateAsFolders:
				self.folderPath = self.filepath +"%04d/%02d/%02d" % ( timenow.year, timenow.month, timenow.day )
				subprocess.call( [ "mkdir", "-p", self.folderPath ] )
				self.filename = self.folderPath + "/" + self.prefix + "%02d%02d%02d.h264" % ( timenow.hour, timenow.minute, timenow.second )
			else:
				self.filename = self.filepath + self.prefix + "%04d%02d%02d-%02d%02d%02d.h264" % ( timenow.year, timenow.month, timenow.day, timenow.hour, timenow.minute, timenow.second )

			self.mp4name = self.filename[:-4] + "mp4"
			self.camera.start_recording( self.filename, resize=( self.width, self.height) )
			self.isRecording = True
			self.lastActiveTime = time.clock()
			print "Started recording %s" % self.filename

	def StopRecording( self ):
		if self.isRecording and ( self.timeWithoutActivity > self.minimumLength ):
			self.camera.stop_recording()
			self.isRecording = False
			if self.convertToMp4:
				subprocess.call( [ "MP4Box","-fps",str(self.framerate),"-add",self.filename,self.mp4name ] )
				subprocess.call( [ "rm", self.filename ] )
				print "\n"
			else:
				print "Finished recording."

	def CaptureTestImage( self ):
		self.image1 = self.image2
		self.buffer1 = self.buffer2
		imageData = cStringIO.StringIO()
		self.camera.capture( imageData, 'bmp', use_video_port=True, resize=( self.tWidth, self.tHeight) )
		imageData.seek(0)
		im = Image.open( imageData )
		buffer = im.load()
		imageData.close()
		return im, buffer

	def TestMotion( self ):
		changedPixels = 0
		self.image2, self.buffer2 = self.CaptureTestImage()
		for x in xrange( 0, self.tWidth-1 ):
			for y in xrange( 0, self.tHeight-1 ):
				pixdiff = abs( self.buffer1[x,y][1] - self.buffer2[x,y][1] )
				if pixdiff > self.threshold:
					changedPixels += 1
		if changedPixels > self.sensitivity:
			self.timeWithoutActivity = 0
			return True
		else:
			self.timeWithoutActivity += ( time.clock() - self.lastActiveTime )
			return False

motion = Motion()
print "Warming up camera..."
time.sleep( 1 )
print "Camera ready to record. Use Ctrl+C to stop."

try:
	while True:
		motion.camera.start_preview()
		if motion.TestMotion():
			motion.StartRecording()
		else:
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
