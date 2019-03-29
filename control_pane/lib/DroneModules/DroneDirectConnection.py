from threading import Thread
import asyncio
import datetime
from control_pane.lib.DroneModules.DataService import log
#from DataService import DataService
try:
    import dronekit
    from dronekit import LocationGlobal, LocationGlobalRelative, VehicleMode
except Exception as e:
    log(e)
from project.settings import WORK_BATTERY_VOLTAGE
from control_pane.models import History
from control_pane.models import Drone as DroneModel
from control_pane.models import DroneCommand
from control_pane.models import ExchangeObject
from control_pane.models import Route, Event

import json
import time
import math
import inspect
import logging
import uuid

def function_logger(file_level, console_level=None):
    function_name = inspect.stack()[1][3]
    logger = logging.getLogger(function_name)
    return logger
def distanceDouble(x, y):
    if x >= y:
        result = x - y
    else:
        result = y - x
    return result

file_logger = function_logger(logging.INFO)

class warnings(object):
    allow = True
    @staticmethod
    def checker():
        while True:
            try:
                if type(PilotControll.vehicle) is not str:
                    # if PilotControll.vehicle.battery.level < 60:
                    if PilotControll.vehicle.battery != None:
                        if PilotControll.vehicle.battery.voltage < 1:#WORK_BATTERY_VOLTAGE:
                            warnings.allow = False
                            sign.stop_sign = True
                            try:
                                log(str(PilotControll.vehicle.battery.voltage))
                            except Exception as e:
                                time.sleep(0.1)
                            if PilotControll.vehicle.mode != VehicleMode("RTL"):
                                PilotControll.vehicle.mode = VehicleMode("RTL")
                                log("Low battery voltage = " + str(PilotControll.vehicle.battery.voltage))
                                log("Blocking and return to home ...")
                        else:
                            warnings.allow = True
                            sign.stop_sign = False
            except Exception as e:
                log(e)
                sign.stop_sign = True
                warnings.allow = False
                break
            time.sleep(1)
        time.sleep(1)
        warnings.checker()
        log("Checker = True.")

class sign(object):
    stop_sign = False


class service():
    @staticmethod
    def writeStatisticData(type, data, copter_id):
        try:
            if data.last_heartbeat < 10:
                if type == "history":
                    if data.location.global_relative_frame.lon != None:
                        voltage = ""
                        level = ""
                        try:
                            voltage = data.battery.voltage
                            level = data.battery.level
                        except Exception as e:
                            voltage = 0
                            level = 0
                        record = History(coordinates_lon=data.location.global_relative_frame.lon,
                                         coordinates_lat=data.location.global_relative_frame.lat,
                                         coordinates_alt=data.location.global_relative_frame.alt,
                                         air_speed=str(data.airspeed)[:str(data.airspeed).find('.') + 3],
                                         ground_speed=str(data.groundspeed)[:str(data.groundspeed).find('.') + 3],
                                         is_armable=str(data.is_armable),
                                         is_armed=str(data.armed),
                                         status=str(data.system_status)[str(data.system_status).find(':') + 1:],
                                         last_heartbeat=str(data.last_heartbeat)[
                                                        :str(data.last_heartbeat).find('.') + 3],
                                         mode=str(data.mode)[str(data.mode).find(':') + 1:],
                                         battery_voltage=data.battery.voltage,
                                         battery_level=data.battery.level,
                                         gps_fixed=data.gps_0.satellites_visible,
                                         outer_id=id,
                                         event_id = 1,
                                         drone_id=copter_id)
                        record.save()
                        record = History.objects.last()
                        record.uid = "history_" + str(record.id)
                        record.save(update_fields=['uid'])
                        # exchange_object = ExchangeObject(type="history", uid="history_" + str(record.id))
                        # exchange_object.save()
                        log(str(record.history_timestamp))
        except Exception as e:
            log('******************* error in write statistic ********************')
            log(e)
            log('*****************************************************************')
            return
    @staticmethod
    def changeCommandStatus(command, status, needExchange = False):
        try:
            command.status = status
            command.save(update_fields=['status'])
            if needExchange == True:
                exchange_object = ExchangeObject(type="command", uid=command.uid)
                exchange_object.save()
        except Exception as e:
            file_logger.info('********* error *********')
            file_logger.info('Команда [' + str(command.id) + '] уже имеет статус [' + status + ']')

    @staticmethod
    def changeRouteStatus(route, status, needExchange=False, without_commands=False):
        try:
            route.status = status
            route.save(update_fields=['status'])
            if without_commands == False:
                commands = DroneCommand.objects.filter(route_uid=route.uid)
                for command in commands:
                    try:
                        command.status = status
                        command.save(update_fields=['status'])
                        exchange_object = ExchangeObject(type="command", uid=command.uid)
                        exchange_object.save()
                    except Exception as e:
                        print('Команда [' + str(command.id) + '] уже имеет статус [' + status + ']')
            if needExchange == True:
                exchange_object = ExchangeObject(type="command", uid=route.uid)
                exchange_object.save()
        except Exception as e:
            print('Маршрут [' + str(route.id) + '] уже имеет статус [' + status + ']')
    @staticmethod
    def new_event(name, drone_id = None, route_id = None, command_id = None, drone_plane_id = None):
        log("drone_id = " + str(drone_id))
        log("route_id = " + str(route_id))
        log("command_id = " + str(command_id))
        log("drone_plane_id = " + str(drone_plane_id))

        if drone_id != None:
            new_event = Event(
                name = name + " [" + str(drone_id) + "]",
                drone_id = drone_id,
                is_seen = False,
                uid = str(uuid.uuid1()),
            )
            new_event.save()
            exchange_object = ExchangeObject(type = "event", uid = new_event.uid)
            exchange_object.save()
        elif route_id != None:
            new_event = Event(
                name = name + " [" + str(route_id) + "]",
                route_id = route_id,
                is_seen = False,
                uid = str(uuid.uuid1()),
                )
            new_event.save()
            exchange_object = ExchangeObject(type = "event", uid = new_event.uid)
            exchange_object.save()
        elif command_id != None :
            new_event = Event(
                name = name + " [" + str(command_id) + "]",
                command_id = command_id,
                is_seen = False,
                uid = str(uuid.uuid1()),
                )
            new_event.save()
            exchange_object = ExchangeObject(type = "event", uid = new_event.uid)
            exchange_object.save()
        elif drone_plane_id != None :
            new_event = Event(
                name = name + " [" + str(drone_plane_id) + "]",
                drone_plane_id = drone_plane_id,
                is_seen = False,
                uid = str(uuid.uuid1()),
                )
            new_event.save()
            exchange_object = ExchangeObject(type = "event", uid = new_event.uid)
            exchange_object.save()

class PilotFunctions(object):
    @staticmethod
    def get_distance_metres(aLocation1, aLocation2):
        """
        Returns the ground distance in metres between two LocationGlobal objects.
        This method is an approximation, and will not be accurate over large distances and close to the
        earth's poles. It comes from the ArduPilot test code:
        https://github.com/diydrones/ardupilot/blob/master/Tools/autotest/common.py
        """
        if aLocation1.alt == None:
            aLocation1.alt = 0
        if aLocation2.alt == None:
            aLocation2.alt = 0

        aLocation2.lat = float(aLocation2.lat)
        aLocation2.lon = float(aLocation2.lon)
        dlat = aLocation2.lat - aLocation1.lat
        dlong = aLocation2.lon - aLocation1.lon
        return math.sqrt((dlat * dlat) + (dlong * dlong)) * 1.113195e5
    @staticmethod
    def wait_vehicle_ready():
        isReady = False
        while isReady == False :
            try :
                if type(PilotControll.vehicle) is not str :
                    PilotControll.vehicle.wait_ready()
                    isReady = True
                else :
                    time.sleep(1)
            except Exception as e :
                print("vehicle not ready, trying again..")
                print(e)
class PilotControllWaypoint(object):
    def __init__(self, coordinates):
        self.coordinates = json.loads(coordinates)
        self.altitude = PilotControll.work_altitude
        self.ground_speed = PilotControll.work_ground_speed
        self.air_speed = PilotControll.work_air_speed
        self.pause = False
        self.cancel = False
        self.not_upper = False
        self.not_running = False
        self.success = False
        self.warning = False
        #self.performWrapper()
        # thr = Thread(target=self.performWrapper)
        # thr.start()
    def checker(self, not_upper = None, not_running = None):

        if not_upper == None and not_running == None:
            if sign.stop_sign == False:
                allowContinue = False
                if self.pause == False and self.cancel == False and self.not_upper == False and self.not_running == False:
                    allowContinue = True
                return allowContinue
            else:
                return False
        else:
            if not_upper == True:
                self.not_upper = True
            elif not_running == True:
                self.not_running = True
    def performHalting(self):
        if self.not_upper == True or self.not_running == True:
            self.warning = True
        elif self.pause == True:
            pauseTimer = time.time()
            while time.time() - pauseTimer < 60:
                if PilotControll.vehicle.mode != VehicleMode("LOITER"):
                    PilotControll.vehicle.mode = VehicleMode("LOITER")
                if self.pause == False:
                    break


    def performWrapper(self):
        vehicle = PilotControll.vehicle
        vehicle.airspeed = self.air_speed
        vehicle.groundspeed = self.ground_speed

        PilotControll.arm_and_takeoff(self.altitude, self.checker)

        if self.not_running == False and self.cancel == False and self.pause == False:
            point = LocationGlobalRelative(self.coordinates[0], self.coordinates[1], self.altitude)
            vehicle.simple_goto(point)
            distancetopoint = PilotFunctions.get_distance_metres(vehicle.location.global_frame, point)
            startdistance = distancetopoint
            startdistancetimestamp = time.time()
            not_upper = False
            while distancetopoint >= 1.5:
                if self.not_running == False and self.cancel == False and self.pause == False and warnings.allow == True and sign.stop_sign == False:
                    if time.time() - startdistancetimestamp >= 30:
                        if vehicle.armed == False:
                            self.not_running = True
                            log(
                                ' ******************************* Not running! *******************************')
                            break
                        elif vehicle.armed == True and self.not_upper == False:
                            if distanceDouble(startdistance, distancetopoint) < 2:
                                self.not_running = True
                                log(
                                    ' ******************************* Not running! *******************************')
                                break
                        elif self.not_upper == True:
                            if distanceDouble(startdistance, distancetopoint) < 1:
                                not_upper = True
                                break
                    log("distance to target point = " + str(distancetopoint))
                    time.sleep(1)
                    distancetopoint = PilotFunctions.get_distance_metres(vehicle.location.global_frame, point)
                else:
                    break
            if not_upper == False and self.not_upper == True:
                self.not_upper = False
        if self.checker() == False:
            self.performHalting()
            if self.pause == False and self.warning == False and self.cancel == False:
                self.performWrapper()
        else:
            self.success = True


class PilotControll(object):
    copter_id = ""
    ws = ""
    vehicle = ""
    work_altitude = 0
    work_air_speed = 0
    work_ground_speed = 0
    def arm_and_takeoff(aTargetAltitude, checker):
        copter_id = PilotControll.copter_id
        vehicle = PilotControll.vehicle
        log('..wait ready..')
        PilotFunctions.wait_vehicle_ready()
        # Copter should arm in GUIDED mode
        if vehicle.mode == VehicleMode("RTL"):
            if PilotFunctions.get_distance_metres(vehicle.location.global_frame, vehicle.home_location) < 1.5:
                timer = time.time()
                while vehicle.armed:
                    if checker() == True:
                        if vehicle.armed == True:
                            if time.time - timer > 90:
                                break
                            else:
                                time.sleep(1)
                                log("waiting for landing...")
                        else:
                            break


        vehicle.mode = VehicleMode("GUIDED")
        # log("Waiting for ability to arm...")
        # while not vehicle.is_armable:
        #     if checker():
        #         log("Waiting for ability to arm...")
        #         time.sleep(1)
        #     else:
        #         break

        if checker():
            log("Arming motors")
            vehicle.armed = True
        # Confirm vehicle armed before attempting to take off
        startArming = time.time()
        if checker():
            while not vehicle.armed:
                if checker():
                    if time.time() - startArming >= 30:
                        new_command = DroneCommand(type='cancel', drone_id=copter_id, status=1, is_sync=True, is_async=True)
                        new_command.save()
                        break
                    else:
                        vehicle.armed = True
                        log("Waiting for arming...")
                        time.sleep(5)
                else:
                    break
            log("Taking off!")
            vehicle.simple_takeoff(aTargetAltitude)  # Take off to target altitude
        # Wait until the vehicle reaches a safe height before processing the goto (otherwise the command
        #  after Vehicle.simple_takeoff will execute immediately).
        startTakeOff = time.time()
        start_alt = vehicle.location.global_relative_frame.alt
        while True:
            if checker():
                if time.time() - startTakeOff >= 90:
                    if distanceDouble(start_alt, vehicle.location.global_relative_frame.alt) < 1:
                        checker(not_upper=True)
                        log(' ******************************* Not upper! *******************************')
                        break
                log("Altitude: " + str(vehicle.location.global_relative_frame.alt))
                # Break and return from function just below target altitude.

                if vehicle.location.global_relative_frame.alt >= aTargetAltitude * 0.8:
                    log("Reached target altitude")
                    break
                time.sleep(1)
            else:
                break

class PilotCommand(object):
    def __init__(self, type, command):
        self.type = type
        self.command = command
        self.processing = True
        self.pilot_mission = ""
        self.warning = False
        self.paused = False
        # self.order = command_data.order
    def do(self):
        if self.type == 'waypoint':
            service.changeCommandStatus(command=self.command, status="2", needExchange=True)
            service.new_event(name = "Выполняется команда прямого движения по маршруту", command_id = self.command.id)
            self.pilot_mission = PilotControllWaypoint(self.command.point)
            self.pilot_mission.performWrapper()
            if self.pilot_mission.checker():
                service.changeCommandStatus(command=self.command, status="3", needExchange=True)
                service.new_event(name = "Команда выполнена",
                                  command_id = self.command.id)
            else:

                # if self.pilot_mission.cancel == True:
                #     # route = Route.objects.filter(uid=self.command.route_uid).last()
                #     # if route != None:
                #     #     service.changeRouteStatus(route = route, status = "4", needExchange = True)
                if self.pilot_mission.warning == True:
                    self.warning = True
                    service.changeCommandStatus(command = self.command, status = "4", needExchange = True)
                    service.new_event(name = "Команда отменена в связи с ошибкой в процессе полета",
                                      command_id = self.command.id)
                elif self.pilot_mission.pause == True:
                    self.paused = True
            self.processing = False

    def pause(self, state):
        self.pilot_mission.pause = state
        if state == True:
            service.changeCommandStatus(command=self.command, status="3", needExchange=True)
            service.new_event(name = "Пауза",
                              command_id = self.command.id)
        elif state == False:
            service.changeCommandStatus(command=self.command, status="2", needExchange=True)
            service.new_event(name = "Продолжение маршрута",
                              command_id = self.command.id)
    def cancel(self):
        self.pilot_mission.cancel = True

class DroneThread(Thread):
    def __init__(self, thread_name, drone, *args, **kwargs):
        Thread.__init__(self, *args, **kwargs)
        self.sendedMessages = {'messages':{}} # блокировка необработанных сообщений
        self.name = thread_name
        self.drone = drone
        self.cancel = False
        self.pause = False
        self.not_routes = False
        self.not_running = False
        self.not_upper = False
        self.current_command = ""
        self.current_route = ""
    def checkResultCommand(self):
        result = True
        if self.current_command.warning == True or self.current_command.paused == True:
            result = False
            file_logger.info("Возврат на домашнюю точку")
            PilotControll.vehicle.mode = VehicleMode("RTL")
        elif self.current_command.cancel == True:
            result = False
            file_logger.info("Возврат на домашнюю точку")
            PilotControll.vehicle.mode = VehicleMode("RTL")
        return result
    def connect(self):
        sign.stop_sign = True
        self.drone.connected = False
        while self.drone.connected == False:
            try:
                # connection_string = "udpout:10.8.0.101:14550"
                self.vehicle = dronekit.connect(self.drone.connection_string, wait_ready=True)# dronekit.connect(self.drone.connection_string, wait_ready=False)
                sign.stop_sign = False
                PilotControll.vehicle = self.vehicle
                self.drone.connected = True
                self.drone.vehicle = self.vehicle
                drone__ = DroneModel.objects.filter(id=self.drone.id).last()
                my_location_alt = self.vehicle.location.global_frame
                if drone__ != None:
                    if drone__.rtl != None:
                        coordinates = json.loads(drone__.rtl)
                        if coordinates[0] != "" and coordinates[1] != "":
                            point_rtl = LocationGlobal(float(coordinates[0]), float(coordinates[1]), 0)
                            my_location_alt = point_rtl
                try:
                    self.vehicle.home_location = my_location_alt
                except Exception as e:
                    log('****** Do not set home location (was set is current coordinates) *******')
                self.commands_thread = DroneThread('commands_thread', self.drone)
                self.commands_thread.start()
                threads_is_alive = self.commands_thread.is_alive()
                while threads_is_alive:
                    threads_is_alive = self.commands_thread.is_alive()
                    if self.vehicle.last_heartbeat > 30:
                        log("drone connection closing... reconnection...")
                        self.vehicle.close()
                        self.drone.connected = False
                        break
                        #return
                    else:
                        self.drone.connected = True
                        time.sleep(1)
                else:
                    while warnings.allow == False:
                        if self.vehicle.last_heartbeat > 30:
                            log("drone connection closing... reconnection...")
                            self.vehicle.close()
                            self.drone.connected = False
                            break
                        else:
                            self.drone.connected = True
                            time.sleep(1)
                        log('warnings! returning to home..')
                        time.sleep(10)
                log("statistic or comamnds thread is not alive...")
                self.vehicle.close()
                #return
            except Exception as e:
                self.drone.connected = False
                log("************************* Error [self.connect] *************************")
                log(str(e))
                log("*********************************************************")
                # self.vehicle.close()
                #return
        self.connect()

    def run(self):
        log("Drone '" + self.name + "' started")
        if self.name == "main_thread":
            time.sleep(1)
            self.connect()
        elif self.name == "exchange_thread":
            asyncio.set_event_loop(asyncio.new_event_loop())
            while True:
                data_recieved = {}

                # ***************************************** RECIEVED *********************************************
                packages = ExchangeObject.objects.all()
                for package in packages:
                    # ************************************ EVENTS ******************************************
                    if package.type == 'event':
                        try:
                            if self.drone.connection != None and not type(self.drone.connection) is str :
                                event = Event.objects.get(uid = package.uid)
                                drone_uid = None
                                command_uid = None
                                route_uid = None
                                drone_plane_uid = None
                                if event.drone != None :
                                    drone_uid = event.drone.outer_id
                                if event.command != None :
                                    command_uid = event.command.uid
                                if event.route != None :
                                    route_uid = event.route.uid
                                if event.drone_plane != None :
                                    drone_plane_uid = event.drone_plane.uid
                                if not event.uid in self.sendedMessages['messages'] :
                                    self.drone.connection.write_message({
                                        'type' : 'exchange_request',
                                        'data' : {
                                            'name' : event.name,
                                            'timestamp' : str(event.timestamp),
                                            'copter_uid' : str(drone_uid),
                                            'command_uid' : str(command_uid),
                                            'route_uid' : str(route_uid),
                                            'drone_plane_uid' : str(drone_plane_uid),
                                            'is_seen' : str(event.is_seen),
                                            'uid' : event.uid,
                                            'object_type' : 'Event',
                                            }
                                        })
                                    self.sendedMessages['messages']['uid'] = time.time()
                                else :
                                    if time.time() - self.sendedMessages['messages']['uid'] > 5 :
                                        self.drone.connection.write_message({
                                            'type' : 'exchange_request',
                                            'data' : {
                                                'name' : event.name,
                                                'timestamp' : str(event.timestamp),
                                                'copter_uid' : str(drone_uid),
                                                'command_uid' : str(command_uid),
                                                'route_uid' : str(route_uid),
                                                'drone_plane_uid' : str(drone_plane_uid),
                                                'is_seen' : str(event.is_seen),
                                                'uid' : event.uid,
                                                'object_type' : 'Event',
                                                }
                                            })
                                        self.sendedMessages['messages']['uid'] = time.time()

                            # time.sleep(1)
                        except Exception as e :
                            print(e)
                    obj = Route.objects.filter(uid=package.uid)
                    if len(obj) > 0:
                        data_recieved = {
                            'uid': obj[0].uid,
                            'commands': obj[0].commands,
                            'copter_uid': obj[0].drone.outer_id,
                            'is_done': obj[0].is_done,
                            'status': obj[0].status,
                            'is_sync': obj[0].is_sync,
                            'object_type': 'Route',
                            'result': 'ok'
                        }
                    else:
                        obj = DroneCommand.objects.filter(uid=package.uid)
                        if len(obj) > 0:
                            data_recieved = {
                                'uid': obj[0].uid,
                                'type': obj[0].type,
                                'point': obj[0].point,
                                'copter_uid': obj[0].drone.outer_id,
                                'status': obj[0].status,
                                'is_sync': obj[0].is_sync,
                                'is_async': obj[0].is_async,
                                'order': obj[0].order,
                                'object_type': 'DroneCommand',
                                'result': 'ok'
                            }
                    # ***************************************** RECIEVED *********************************************
                    if len(data_recieved) > 0:
                        if not type(self.drone.connection) is str and len(data_recieved) > 0:
                            try:
                                if self.drone.connection != None and not type(self.drone.connection) is str:
                                    if not data_recieved['uid'] in self.sendedMessages['messages']:
                                        self.drone.connection.write_message({
                                            'type': 'exchange_response',
                                            'data_sended': {},
                                            'data_recieved': data_recieved
                                        })
                                        self.sendedMessages['messages'][data_recieved['uid']] = time.time()
                                    else:
                                        if time.time() - self.sendedMessages['messages'][data_recieved['uid']] > 5:
                                            self.drone.connection.write_message({
                                                'type': 'exchange_response',
                                                'data_sended': {},
                                                'data_recieved': data_recieved
                                            })
                                            self.sendedMessages['messages'][data_recieved['uid']] = time.time()

                                # time.sleep(1)
                            except Exception as e:
                                continue

                time.sleep(0.1)
        elif self.name == 'statistic_writing_thread':
            asyncio.set_event_loop(asyncio.new_event_loop())
            while True:
                time.sleep(1)
                service.writeStatisticData("history", self.drone.vehicle, self.drone.id)
                try:
                    dontUploadsRecord = History.objects.all().filter().order_by('id').last()
                    data = {}
                    if dontUploadsRecord != None:
                        data[dontUploadsRecord.id] = {
                            'id': str(dontUploadsRecord.id),
                            'history_timestamp': {
                                'year': dontUploadsRecord.history_timestamp.year,
                                'month': dontUploadsRecord.history_timestamp.month,
                                'day': dontUploadsRecord.history_timestamp.day,
                                'hour': dontUploadsRecord.history_timestamp.hour,
                                'minute': dontUploadsRecord.history_timestamp.minute,
                                'second': dontUploadsRecord.history_timestamp.second,
                                'django_format': str(dontUploadsRecord.history_timestamp)
                            },
                            'coordinates_alt': str(dontUploadsRecord.coordinates_alt),
                            'coordinates_lat': str(dontUploadsRecord.coordinates_lat),
                            'coordinates_lon': str(dontUploadsRecord.coordinates_lon),

                            'air_speed': str(dontUploadsRecord.air_speed),
                            'ground_speed': str(dontUploadsRecord.ground_speed),
                            'is_armable': str(dontUploadsRecord.is_armable),
                            'is_armed': str(dontUploadsRecord.is_armed),
                            'status': str(dontUploadsRecord.status),
                            'last_heartbeat': str(dontUploadsRecord.last_heartbeat),
                            'mode': str(dontUploadsRecord.mode),
                            'battery_voltage': str(dontUploadsRecord.battery_voltage),
                            'battery_level': str(dontUploadsRecord.battery_level),
                            'gps_fixed': str(dontUploadsRecord.gps_fixed), # TODO: сделать проверку на нулевой id event и добавить в отправку этого сообщения
                            'is_uploaded': str(dontUploadsRecord.is_uploaded),
                            'connection': self.drone.connected,
                            'copter_uid': str(dontUploadsRecord.drone.outer_id),
                        }  # self.drone.connection.drone.connected

                        try:
                            if self.drone.connection != None and not type(self.drone.connection) is str:
                                self.drone.connection.write_message(json.dumps({
                                    'type': 'upload_statistic',
                                    'data': data,
                                }))
                        except Exception as e:
                            log("************************* Error [statistic_writing_thread] *************************")
                            log(e)
                    # django.db.close_old_connections()
                except Exception as e:
                    log(e)
        elif self.name == "statistic_thread":
            asyncio.set_event_loop(asyncio.new_event_loop())
            while True:
                time.sleep(1)
                now = datetime.datetime.now()
                try:
                    if self.drone.connection != None and not type(self.drone.connection) is str:
                        voltage = 0
                        level = 0
                        is_armable = False
                        try:
                            voltage = self.drone.vehicle.battery.voltage
                            level = self.drone.vehicle.battery.level
                            is_armable = self.drone.vehicle.is_armable
                        except Exception as e:
                            voltage = 0
                            level = 0
                            is_armable = False

                        self.drone.connection.write_message(json.dumps({
                            'type': 'update_statistic',
                            'data': {
                                'history_timestamp': {
                                    'year': now.year,
                                    'month': now.month,
                                    'day': now.day,
                                    'hour': now.hour + 1,
                                    'minute': now.minute,
                                    'second': now.second,
                                },
                                'coordinates_alt': str(self.drone.vehicle.location.global_relative_frame.alt),
                                'coordinates_lat': str(self.drone.vehicle.location.global_relative_frame.lat),
                                'coordinates_lon': str(self.drone.vehicle.location.global_relative_frame.lon),
                                'air_speed': str(self.drone.vehicle.airspeed)[
                                             :str(self.drone.vehicle.airspeed).find('.') + 3],
                                'ground_speed': str(self.drone.vehicle.groundspeed)[
                                                :str(self.drone.vehicle.groundspeed).find('.') + 3],
                                'is_armable': str(is_armable),
                                'is_armed': str(self.drone.vehicle.armed),
                                'status': str(self.drone.vehicle.system_status)[
                                          str(self.drone.vehicle.system_status).find(':') + 1:],
                                'last_heartbeat': str(self.drone.vehicle.last_heartbeat)[
                                                  :str(self.drone.vehicle.last_heartbeat).find('.') + 3],
                                'mode': str(self.drone.vehicle.mode)[str(self.drone.vehicle.mode).find(':') + 1:],
                                'battery_voltage': str(voltage),
                                'battery_level': str(level),
                                'gps_fixed': str(self.drone.vehicle.gps_0.satellites_visible),
                                'copter_uid': DroneModel.objects.get(id=self.drone.id).outer_id,
                            },
                        }))
                except Exception as e:
                    log("************************* Error [statistic_thread] *************************")
                    log(e)


        elif self.name == "commands_thread":
            try:
                self.async_commands_thread = DroneThread('async_commands_thread', self.drone)
                self.async_commands_thread.start()
                while self.async_commands_thread.is_alive() and sign.stop_sign == False and warnings.allow == True:
                    if self.drone.connected == True:
                        current_routes = Route.objects.filter(is_sync=True, status__in=['1'])
                        if len(current_routes) > 0:
                            self.current_route = current_routes[0]
                            self.async_commands_thread.current_route = self.current_route
                            current_route_commands = json.loads(self.current_route.commands)
                            current_route_commands = DroneCommand.objects.filter(route_uid=self.current_route.uid, status__in=['1','2'], is_sync=True).exclude(outer_id=None)
                            counter = DroneCommand.objects.filter(route_uid=self.current_route.uid, type='waypoint', is_sync=True, status__in=['1', '2']).exclude(outer_id=None)
                            if len(counter) == len(current_route_commands):
                                issetRouteCommand = True
                                warning = False
                                paused = False
                                success = True
                                service.new_event(name = "Движение по маршруту начато", route_id = self.current_route.id)
                                while issetRouteCommand:
                                    command = DroneCommand.objects.filter(status="2", is_async=False, is_sync=True, type='waypoint', route_uid=self.current_route.uid).order_by('order').exclude(outer_id=None).first()  # Сначала ищем выполняющиеся в текущий момент (если было потеряно соединение)
                                    if command != None:
                                        issetRouteCommand = True
                                    else:
                                        command = DroneCommand.objects.filter(status="1", is_async=False, is_sync=True, type='waypoint', route_uid=self.current_route.uid).order_by('order').exclude(outer_id=None).first()
                                        if command != None:
                                            issetRouteCommand = True
                                        else:
                                            issetRouteCommand = False
                                    if issetRouteCommand:
                                        self.current_command = PilotCommand(type='waypoint', command=command)
                                        self.async_commands_thread.current_command = self.current_command
                                        self.current_command.do()
                                        if self.checkResultCommand() == False:
                                            service.changeRouteStatus(route = self.current_route, status = "4", needExchange = True)
                                            success = False
                                            break
                                if success == True:
                                    if self.current_command.pilot_mission.cancel == False:
                                        service.changeRouteStatus(route=self.current_route, status="2", needExchange=True, without_commands=True)
                                        service.new_event(name = "Маршрут выполнен",
                                                          route_id = self.current_route.id)
                                    else:
                                        service.changeRouteStatus(route = self.current_route, status = "4",
                                                                  needExchange = True, without_commands = True)
                                        service.new_event(name = "Маршрут отменен",
                                                          route_id = self.current_route.id)
                                    log("Returning to Launch")
                                    self.drone.vehicle.mode = VehicleMode("RTL")

                    else:
                        break
                    time.sleep(1)
            except Exception as e:
                log("***************** < error [commands_thread]> ******************")
                log(e)
                log("***************** </ error [commands_thread]> ******************")
        elif self.name == "async_commands_thread":
            try:
                while sign.stop_sign == False and warnings.allow == True:
                    commands = DroneCommand.objects.filter(is_async=True, status__in=["0", "1", "2"], is_sync=True).order_by('order')
                    if len(commands) != 0:
                        for command in commands:
                            if command.type == 'cancel':
                                startWaitingTime = time.time()
                                while type(self.current_command) == str:
                                    time.sleep(1)
                                    if time.time() - startWaitingTime > 10:
                                        break
                                if type(self.current_command) != str:
                                    self.current_command.cancel()
                                    service.changeRouteStatus(self.current_route, "4", True)
                                    service.changeCommandStatus(command, '3', True)
                                    service.new_event(name = "Команда отмены выполнена",
                                                      command_id = command.id)
                                    service.new_event(name = "Маршрут отменен",
                                                      route_id = self.current_route.id)
                            elif command.type == 'pause':
                                startWaitingTime = time.time()
                                while type(self.current_command) == str:
                                    time.sleep(1)
                                    if time.time() - startWaitingTime > 10:
                                        break
                                if type(self.current_command) != str:
                                    self.current_command.pause(True)
                                    service.changeCommandStatus(command, '3', True)
                                    service.changeRouteStatus(route = self.current_route, status = "3", needExchange = True, without_commands = True)
                                    service.new_event(name = "Команда паузы выполнена",
                                                      command_id = command.id)
                                    service.new_event(name = "Маршрут приостановлен",
                                                      route_id = self.current_route.id)
                                    log('.............. route paused ............')
                            elif command.type == 'unpause':
                                startWaitingTime = time.time()
                                while type(self.current_command) == str:
                                    time.sleep(1)
                                    if time.time() - startWaitingTime > 10:
                                        break
                                if type(self.current_command) != str:
                                    self.current_command.pause(False)
                                    service.changeCommandStatus(command, '3', True)
                                    service.changeRouteStatus(route = self.current_route, status = "1", needExchange = True, without_commands = True)
                                    service.new_event(name = "Команда выполнена",
                                                      command_id = command.id)
                                    service.new_event(name = "Маршрут возобновлен",
                                                      route_id = self.current_route.id)
                                    log('.............. route starting ............')
                            time.sleep(1)
                    time.sleep(1)
            except Exception as e:
                log("***************** < error [async_commands_thread]> ******************")
                log(e)
                log("***************** </ error [async_commands_thread]> ******************")



class _Drone(object):
    def __init__(self):
        self.connected = False
        self.connection = ""
        self.vehicle = ""
        drone_model_obj = DroneModel.objects.filter().values()
        self.connection_string = drone_model_obj[0]['connection_ip']
        self.id = drone_model_obj[0]['id']
        self.work_air_speed = drone_model_obj[0]['work_air_speed']
        self.work_ground_speed = drone_model_obj[0]['work_ground_speed']
        self.work_altitude = drone_model_obj[0]['work_altitude']

        PilotControll.work_air_speed = self.work_air_speed
        PilotControll.work_ground_speed = self.work_ground_speed
        PilotControll.work_altitude = self.work_altitude
        PilotControll.copter_id = self.id
        self.history_upload_lock = False
        thr_warnings_checker = Thread(target=warnings.checker)
        thr_warnings_checker.start()
        drone_thread = Thread(target=self.connect)
        drone_thread.start()
        while type(self.vehicle) is str:
            log('wait background threads..')
            time.sleep(2)
        if type(self.vehicle) is not str:
            self.statistic_thread = DroneThread('statistic_thread', self)
            self.statistic_thread.start()
            self.statistic_writing_thread = DroneThread('statistic_writing_thread', self)
            self.statistic_writing_thread.start()
            self.exchange_thread = DroneThread('exchange_thread', self)
            self.exchange_thread.start()
            Thread(target = PilotFunctions.wait_vehicle_ready).start()
            log('background threads started')

    @staticmethod
    def init():
        drone = DroneModel.objects.last().values()
        connection_ip = drone.connection_ip
        return _Drone(connection_ip)

    def connect(self):
        main_thread = DroneThread("main_thread", self)
        main_thread.start()
        while main_thread.is_alive() and self.connected == True:
            continue
        main_thread.join()
        log("main_thread connection is not alive.. reconnection....")
        self.connect()

