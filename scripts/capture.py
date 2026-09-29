#!/usr/bin/env python3
# type: ignore

from picamera2.devices.imx500 import IMX500
from picamera2 import Picamera2
import socket

imx500 = IMX500("/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk")

f_name = f"/home/op/Cluster/{socket.gethostname()}.jpg"
picam2 = Picamera2(imx500.camera_num)
picam2.start()
picam2.capture_file(f_name)
picam2.stop()