import dronekit
from dronekit import VehicleMode
import time
vehicle = dronekit.connect("udpout:127.0.0.1:30001", wait_ready=True)
vehicle.mode = VehicleMode("ALT_HOLD")
print(vehicle.mode)
vehicle.armed = False
