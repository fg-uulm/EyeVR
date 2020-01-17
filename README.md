# EyeVR

This repo contains the source code for the EyeVR mobile VR eye tracker, which runs on a Raspberry Pi with a Pi Camera and can be implemented 
for less than $100. For a more detailed description, see the associated [UBICOMP publication](https://www.uni-ulm.de/fileadmin/website_uni_ulm/iui.inst.100/institut/Papers/Prof_Rukzio/2016/EyeVRUbicompDemo2016.pdf).

# Purpose

The EyeVR tracker system was created as an inexpensive, mobile solution for in-HMD VR eyetracking, e.g. for facilitating mobile HMD eye interaction.
Its usage is not limited to HMD scenarios though. 

# Setup and getting the tracker to run

Beside a RPi and the hardware described in the paper (see above), clone the repo to the Pi and install the respective dependencies 
(OpenCV, pi-blaster, tornado, numpy). The tracker software then provides a web configuration and control interface.

# Unity Scene

Also included is a dummy unity scene which connects to the tracker, and visualizes eye position and pupil size directly in a VR application, which
for example can be easily deployed with Google Cardboards or Samsung Gear VR devices on a smartphone.

# Caveats

Processing and computer vision is done solely on the Raspberry Pi. As there are quite some restrictions to computing power on such devices, it is
important to tune the parameters to an acceptable level or balance between processing time, precision and delay.
