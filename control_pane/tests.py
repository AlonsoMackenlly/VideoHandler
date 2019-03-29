from threading import Thread
import asyncio
import datetime
from DataService import DataService
try:
    import dronekit
    from dronekit import LocationGlobal, LocationGlobalRelative, VehicleMode
except Exception as e:
    print(e)

from control_pane.models import History
from control_pane.models import Drone as DroneModel
from control_pane.models import DroneCommand
from control_pane.models import ExchangeObject
from control_pane.models import Route

import json
import time
import math
import inspect
import logging


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
                                         drone_id=copter_id)
                        record.save()
                        record = History.objects.last()
                        record.uid = "history_" + str(record.id)
                        record.save(update_fields=['uid'])
                        # exchange_object = ExchangeObject(type="history", uid="history_" + str(record.id))
                        # exchange_object.save()
                        print(str(record.history_timestamp))
        except Exception as e:
            print('******************* error in write statistic ********************')
            print(e)
            print('*****************************************************************')
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
                        file_logger.info('Команда [' + str(command.id) + '] уже имеет статус [' + status + ']')
            if needExchange == True:
                exchange_object = ExchangeObject(type="command", uid=route.uid)
                exchange_object.save()
        except Exception as e:
            file_logger.info('Маршрут [' + str(route.id) + '] уже имеет статус [' + status + ']')


class PilotFunctions(object):
    @staticmethod
    def get_distance_metres(aLocation1, aLocation2):
        """
        Returns the ground distance in metres between two LocationGlobal objects.
        This method is an approximation, and will not be accurate over large distances and close to the
        earth's poles. It comes from the ArduPilot test code:
        https://github.com/diydrones/ardupilot/blob/master/Tools/autotest/common.py
        """
        dlat = aLocation2.lat - aLocation1.lat
        dlong = aLocation2.lon - aLocation1.lon
        return math.sqrt((dlat * dlat) + (dlong * dlong)) * 1.113195e5

class PilotControllWaypoint(object):
    def __init__(self, coordinates, altitude, ground_speed, air_speed):
        self.coordinates = json.loads(coordinates)
        self.altitude = altitude
        self.ground_speed = ground_speed
        self.air_speed = air_speed
        self.pause = False
        self.cancel = False
        self.not_upper = False
        self.not_running = False
        self.success = False
        self.warning = False
        self.performWrapper()
    def checker(self, not_upper = None, not_running = None):
        if not_upper == None and not_running == None:
            allowContinue = True
            if self.pause == False and self.cancel == False and self.not_upper == False and self.not_running == False:
                allowContinue = False
            return allowContinue
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
        if self.checker():
            point = LocationGlobalRelative(self.coordinates[0], self.coordinates[1], self.altitude)
            vehicle.simple_goto(point)
            distancetopoint = self.get_distance_metres(vehicle.location.global_frame, point)
            startdistance = distancetopoint
            startdistancetimestamp = time.time()
            not_upper = False
            while distancetopoint >= 1.5:
                if self.checker():
                    if time.time() - startdistancetimestamp >= 30:
                        if vehicle.armed == False:
                            self.not_running = True
                            print(
                                ' ******************************* Not running! *******************************')
                            break
                        elif vehicle.armed == True and self.not_upper == False:
                            if distanceDouble(startdistance, distancetopoint) < 2:
                                self.not_running = True
                                print(
                                    ' ******************************* Not running! *******************************')
                                break
                        elif self.not_upper == True:
                            if distanceDouble(startdistance, distancetopoint) < 1:
                                not_upper = True
                                break
                    print("distance to target point = " + str(distancetopoint))
                    time.sleep(1)
                    distancetopoint = self.get_distance_metres(vehicle.location.global_frame, point)
                else:
                    break
            if not_upper == False and self.not_upper == True:
                self.not_upper = False
        if self.checker() == False:
            self.performHalting()
            if self.pause == False:
                self.performWrapper()
        else:
            self.success = True




class PilotControll(object):
    copter_id = ""
    ws = ""
    vehicle = ""
    def arm_and_takeoff(aTargetAltitude, checker):
        copter_id = PilotControll.copter_id
        vehicle = PilotControll.vehicle
        # Copter should arm in GUIDED mode
        vehicle.mode = VehicleMode("GUIDED")
        print("Waiting for ability to arm...")
        while not vehicle.is_armable:
            if checker():
                print("Waiting for ability to arm...")
                time.sleep(0.2)
            else:
                break

        if checker():
            print("Arming motors")
            vehicle.armed = True
        # Confirm vehicle armed before attempting to take off
        startArming = time.time()
        if checker():
            while not vehicle.armed:
                vehicle.armed = True
                if checker():
                    if time.time() - startArming >= 30:
                        new_command = DroneCommand(type='cancel', drone_id=copter_id, status=1, is_sync=True, is_async=True)
                        new_command.save()
                        break
                    else:
                        print("Waiting for arming...")
                        time.sleep(0.5)
                else:
                    break
            print("Taking off!")
            vehicle.simple_takeoff(aTargetAltitude)  # Take off to target altitude
        # Wait until the vehicle reaches a safe height before processing the goto (otherwise the command
        #  after Vehicle.simple_takeoff will execute immediately).
        startTakeOff = time.time()
        start_alt = vehicle.location.global_relative_frame.alt
        while True:
            if checker():
                if time.time() - startTakeOff >= 10 and time.time() - startTakeOff < 20:
                    while not vehicle.armed:
                        if time.time() - startArming >= 5:
                            vehicle.armed = True
                        else:
                            print("Waiting for arming...")
                            time.sleep(0.5)
                    vehicle.simple_takeoff(aTargetAltitude)
                elif time.time() - startTakeOff >= 20:
                    if distanceDouble(start_alt, vehicle.location.global_relative_frame.alt) < 1:
                        checker(not_upper=True)
                        print(' ******************************* Not upper! *******************************')
                        break
                print("Altitude: " + str(vehicle.location.global_relative_frame.alt))
                # Break and return from function just below target altitude.

                if vehicle.location.global_relative_frame.alt >= aTargetAltitude * 0.8:
                    print("Reached target altitude")
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
            self.pilot_mission = PilotControllWaypoint(self.data.coordinates)
            if self.pilot_mission.success:
                service.changeCommandStatus(command=self.command, status="3", needExchange=True)
            elif self.pilot_mission.warning or self.pilot_mission.pause or self.pilot_mission.cancel:
                service.changeCommandStatus(command=self.command, status="4", needExchange=True)
                if self.pilot_mission.warning == True:
                    self.warning = True
                elif self.pilot_mission.pause == True:
                    self.paused = True
            self.processing = False

    def pause(self, state):
        self.pilot_mission.pause = state
        if state == True:
            service.changeCommandStatus(command=self.command, status="5", needExchange=True)
        elif state == False:
            service.changeCommandStatus(command=self.command, status="2", needExchange=True)
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
        return result
    def connect(self):
        global stop_sign
        self.drone.connected = False
        while self.drone.connected == False:
            try:
                # connection_string = "udpout:10.8.0.101:14550"
                self.vehicle = dronekit.connect(self.drone.connection_string, wait_ready=True)# dronekit.connect(self.drone.connection_string, wait_ready=False)
                PilotControll.vehicle = self.vehicle
                self.drone.connected = True
                self.drone.vehicle = self.vehicle
                drone__ = DroneModel.objects.filter(id=self.drone.id).last()
                my_location_alt = self.vehicle.location.global_frame
                if drone__ != None:
                    if drone__.rtl != None:
                        coordinates = json.loads(drone__.rtl)
                        point_rtl = LocationGlobal(coordinates[0], coordinates[1], 40)
                        my_location_alt = point_rtl
                try:
                    self.vehicle.home_location = my_location_alt
                except Exception as e:
                    print('****** Do not set home location (vehicle not ready) *******')
                self.statistic_thread = DroneThread('statistic_thread', self.drone)
                self.statistic_thread.start()
                self.commands_thread = DroneThread('commands_thread', self.drone)
                self.commands_thread.start()
                self.exchange_thread = DroneThread('exchange_thread', self.drone)
                self.exchange_thread.start()
                self.statistic_writing_thread = DroneThread('statistic_writing_thread', self.drone)
                self.statistic_writing_thread.start()

                threads_is_alive = self.statistic_thread.is_alive() and self.commands_thread.is_alive() and self.exchange_thread.is_alive() and self.statistic_writing_thread.is_alive()
                while threads_is_alive:
                    threads_is_alive = self.statistic_thread.is_alive() and self.commands_thread.is_alive() and self.exchange_thread.is_alive() and self.statistic_writing_thread.is_alive()
                    if self.vehicle.last_heartbeat > 15:
                        print("drone connection closing... reconnection...")
                        self.vehicle.close()
                        self.drone.connected = False
                        return
                    else:
                        self.drone.connected = True
                        time.sleep(1)
                print("statistic or comamnds thread is not alive...")
                self.vehicle.close()
                return
            except Exception as e:
                self.drone.connected = False
                print(str(e))
                # self.vehicle.close()
                return

    def run(self):
        print("Drone '" + self.name + "' started")
        if self.name == "main_thread":
            self.connect()
        elif self.name == "exchange_thread":
            asyncio.set_event_loop(asyncio.new_event_loop())
            while self.is_alive():

                data_recieved = {}
                # ***************************************** RECIEVED *********************************************
                packages = ExchangeObject.objects.all()
                for package in packages:
                    if len(packages) > 0:
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
            while self.is_alive():
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
                            'gps_fixed': str(dontUploadsRecord.gps_fixed),
                            'event': str(dontUploadsRecord.event_id),
                            'is_uploaded': str(dontUploadsRecord.is_uploaded),
                            'connection': True,
                            'copter_uid': str(dontUploadsRecord.drone.outer_id),
                        }  # self.drone.connection.drone.connected

                        try:
                            if self.drone.connection != None and not type(self.drone.connection) is str:
                                self.drone.connection.write_message(json.dumps({
                                    'type': 'upload_statistic',
                                    'data': data,
                                }))
                        except Exception as e:
                            print(e)
                            continue
                    # django.db.close_old_connections()
                except Exception as e:
                    break
        elif self.name == "statistic_thread":
            asyncio.set_event_loop(asyncio.new_event_loop())
            while self.is_alive():
                time.sleep(0.5)
                now = datetime.datetime.now()
                try:
                    if self.drone.connection != None and not type(self.drone.connection) is str:
                        voltage = 0
                        level = 0
                        try:
                            voltage = self.drone.vehicle.battery.voltage
                            level = self.drone.vehicle.battery.level
                        except Exception as e:
                            voltage = 0
                            level = 0
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
                                'is_armable': str(self.drone.vehicle.is_armable),
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
                    print(e)

        elif self.name == "commands_thread":
            try:
                self.async_commands_thread = DroneThread('async_commands_thread', self.drone)
                self.async_commands_thread.start()
                while self.async_commands_thread.is_alive():
                    if self.drone.connected == True:
                        current_routes = Route.objects.filter(is_sync=True, status__in=['1'])
                        if len(current_routes) > 0:
                            self.current_route = current_routes[0]
                            current_route_commands = json.loads(self.current_route.commands)
                            uids = []
                            for cmd_current_route_id in current_route_commands:
                                uids.append(current_route_commands[cmd_current_route_id]['uid'])
                            current_route_commands = DroneCommand.objects.filter(route_uid=self.current_route.uid, uid__in=uids, status__in=['1','2'])
                            counter = DroneCommand.objects.filter(route_uid=self.current_route.uid, type='waypoint', is_sync=True, status__in=['1', '2']).exclude(outer_id=None)
                            if len(counter) == len(current_route_commands):
                                issetRouteCommand = True
                                warning = False
                                paused = False
                                success = True
                                while issetRouteCommand:
                                    command = DroneCommand.objects.filter(status="2", is_async=False, is_sync=True, type='waypoint', route_uid=self.current_route.uid).order_by('outer_id').exclude(outer_id=None).first()  # Сначала ищем выполняющиеся в текущий момент (если было потеряно соединение)
                                    if command != None:
                                        issetRouteCommand = True
                                    else:
                                        command = DroneCommand.objects.filter(status="1", is_async=False, is_sync=True, type='waypoint', route_uid=self.current_route.uid).order_by('outer_id').exclude(outer_id=None).first()
                                        if command != None:
                                            issetRouteCommand = True
                                        else:
                                            issetRouteCommand = False
                                    if issetRouteCommand:
                                        self.current_command = PilotCommand(type='waypoint', command=command)
                                        do_thread = Thread(target=self.current_command.do)
                                        do_thread.start()
                                        while self.current_command.processing == True:
                                            time.sleep(0.5)
                                        if self.checkResultCommand() == False:
                                            service.changeRouteStatus(route = self.current_route, status = "4", needExchange = True)
                                            success = False
                                            break
                                if success == True:
                                    service.changeRouteStatus(route=self.current_route, status="3", needExchange=True, without_commands=True)
                    else:
                        break
                    time.sleep(1)
            except Exception as e:
                print("***************** < error > ******************")
                print(e)
                print("***************** </ error > ******************")
        elif self.name == "async_commands_thread":
            try:
                while True:
                    commands = DroneCommand.objects.filter(is_async=True, status__in=["0", "1", "2"], is_sync=True).order_by('outer_id')
                    if len(commands) != 0:
                        for command in commands:
                            if command.type == 'cancel':
                                self.current_command.cancel()
                                service.changeRouteStatus(self.current_route, "4", True)
                                service.changeCommandStatus(command, '3', True)
                            elif command.type == 'pause':
                                self.current_command.pause(True)
                                service.changeCommandStatus(command, '3', True)
                                print('.............. route paused ............')
                            elif command.type == 'unpause':
                                self.current_command.pause(False)
                                service.changeCommandStatus(command, '3', True)
                                print('.............. route starting ............')
                            time.sleep(1)
                    time.sleep(1)
            except Exception as e:
                print("***************** < error > ******************")
                print(e)
                print("***************** </ error > ******************")


class _Drone(object):
    def __init__(self):
        self.connected = False
        self.connection = ""

        drone_model_obj = DroneModel.objects.filter().values()
        self.connection_string = drone_model_obj[0]['connection_ip']
        self.id = drone_model_obj[0]['id']
        self.work_air_speed = drone_model_obj[0]['work_air_speed']
        self.work_ground_speed = drone_model_obj[0]['work_ground_speed']
        self.work_altitude = drone_model_obj[0]['work_altitude']
        self.history_upload_lock = False

        drone_thread = Thread(target=self.connect)
        drone_thread.start()

    @staticmethod
    def init():
        drone = DroneModel.objects.last().values()
        connection_ip = drone.connection_ip
        return _Drone(connection_ip)

    def connect(self):
        main_thread = DroneThread("main_thread", self)
        main_thread.start()

        while main_thread.is_alive():
            continue
        main_thread.join()
        print("main_thread connection is not alive.. reconnection....")
        self.connect()

    # def handle_request(self, response):
    #     print(response)
    # while True:
    #     print(self.droneThreads["connection_thread"])
