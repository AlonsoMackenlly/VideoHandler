
import dronekit
from pymavlink import mavutil
import time
from dronekit import LocationGlobal, LocationGlobalRelative, VehicleMode
vehicle = dronekit.connect("udpout:127.0.0.1:30001", wait_ready=False)
def set_roi(location):
    # create the MAV_CMD_DO_SET_ROI command
    msg = vehicle.message_factory.command_long_encode(
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_CMD_DO_SET_ROI, #command
        0, #confirmation
        0, 0, 0, 0, #params 1-4
        location.lat,
        location.lon,
        location.alt
        )
    # send command to vehicle
    vehicle.send_mavlink(msg)


# dronekit.connect(self.drone.connection_string, wait_ready=False)
# point = LocationGlobalRelative(53.509847, 49.256688, 0)
# set_roi(point)
vehicle.gimbal.rotate(10, 0, 0)
# vehicle.gimbal.rotate(30, 0, 0)
# vehicle.gimbal.rotate(0, 0, 0)
# while not vehicle.is_armable:
#     print(" Waiting for vehicle to initialise...")
#     time.sleep(1)
# vehicle.target_location(LocationGlobalRelative(53.495833, 49.285140, 0))
# vehicle.armed = True
# time.sleep(10)
# vehicle.armed = False