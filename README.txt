PiMotion
========

Pure python motion detection and high quality video recording for the Raspberry Pi Camera Module.

The method used is to capture the video at max resolution (2592 x 1944) then scale it down to final resolution using the GPU to achieve a cleaner image quality thanks to oversampling.

Yes, the Pi can handle it just fine, though it may choke a bit sometimes when doing the motion detection while recording the video. The "Stop recording" method may take a bit too long to kick in, but nothing too bad.

The motion detection is based on the picam.py script, and is achieved by capturing tiny images through the video port without stopping the video recording (image is captured at full resolution and scaled using the gpu), and then checking for changes in these images and triggering "start" and "stop" video recording methods.

Requires installation of PIL and picamera modules:
sudo apt-get install python-imaging-tk
sudo apt-get install python-picamera

I'm not a real programmer, so feel free to improve, simplify my code and let me know so I can use it as well! :-)
Cheers!
Leo.
