import threading
import urllib
from threading import Thread
from tornado.ioloop import IOLoop
import asyncio
try:
    import dronekit
    from dronekit import LocationGlobalRelative, VehicleMode
except Exception as e:
    print(e)

from control_pane.models import History
from control_pane.models import Drone as DroneModel
from control_pane.models import DroneCommand
from control_pane.models import ExchangeObject
from control_pane.models import Route

import json

from django.conf import settings
import tornado.httpclient
import time
import math
import inspect
import logging
def function_logger(file_level, console_level=None):
    function_name = inspect.stack()[1][3]
    logger = logging.getLogger(function_name)
    return logger

file_logger = function_logger(logging.INFO)

class service():
    @staticmethod
    def writeData(type, data, copter_id):
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
                                 last_heartbeat=str(data.last_heartbeat)[:str(data.last_heartbeat).find('.') + 3],
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
                file_logger.info(str(record.history_timestamp))



class _temporary_data(object):
    def __init__(self):
        self.stop_sign = False


class DroneThread(Thread):
    def __init__(self, thread_name, drone, *args, **kwargs):
        Thread.__init__(self, *args, **kwargs)
        self.name = thread_name
        self.drone = drone
        self.cancel = False
        self.not_running = False
        self.not_upper = False
    def go_to_commands(self, commands):
        if len(commands) != 0:
            vehicle = self.drone.vehicle
            cmds = vehicle.commands
            cmds.clear()
            for command in commands:
                #if command.status != "2" and command.status != "4":
                try:
                    command.status = "2"
                    command.save(update_fields=['status'])  # Статус команды обновился на 2 - "Выполняется"
                    # TODO: need SYNC object
                    ex = ExchangeObject.objects.filter(type="command", uid=command.uid).last()
                    if ex == None:
                        exchange_object = ExchangeObject(type="command", uid=command.uid)
                        exchange_object.save()
                except Exception as e:
                    file_logger.info(e)
                if vehicle.mode == VehicleMode("RTL"):
                    if self.get_distance_metres(vehicle.location.global_relative_frame, vehicle.home_location) < 2:
                        while vehicle.armed == True:
                            time.sleep(1)
                self.handle(command)
                if self.async_commands_thread.cancel == False:
                    if self.not_running == False and self.not_upper == False:
                        command.status = "3"  # Статус команды обновился на 3 - "Выполнено"
                        command.save(update_fields=['status'])
                        ex = ExchangeObject.objects.filter(type="command", uid=command.uid).last()
                        if ex == None:
                            exchange_object = ExchangeObject(type="command", uid=command.uid)
                            exchange_object.save()

    def get_distance_metres(self, aLocation1, aLocation2):
        """
        Returns the ground distance in metres between two LocationGlobal objects.

        This method is an approximation, and will not be accurate over large distances and close to the
        earth's poles. It comes from the ArduPilot test code:
        https://github.com/diydrones/ardupilot/blob/master/Tools/autotest/common.py
        """
        dlat = aLocation2.lat - aLocation1.lat
        dlong = aLocation2.lon - aLocation1.lon
        return math.sqrt((dlat * dlat) + (dlong * dlong)) * 1.113195e5

    def arm_and_takeoff(self, aTargetAltitude):

        vehicle = self.drone.vehicle
        # Copter should arm in GUIDED mode
        vehicle.mode = VehicleMode("GUIDED")

        file_logger.info("Arming motors")
        vehicle.armed = True
        # Confirm vehicle armed before attempting to take off
        startArming = time.time()
        while not vehicle.armed:
            if time.time() - startArming >= 30:
                new_command = DroneCommand(type='cancel', drone_id=self.drone.id, status=1, is_sync=True, is_async=True)
                new_command.save()
                break
            else:
                file_logger.info("Waiting for arming...")
                time.sleep(0.5)
        file_logger.info("Taking off!")
        vehicle.simple_takeoff(aTargetAltitude)  # Take off to target altitude
        # Wait until the vehicle reaches a safe height before processing the goto (otherwise the command
        #  after Vehicle.simple_takeoff will execute immediately).
        startTakeOff = time.time()
        while True:
            if time.time() - startTakeOff >= 30:
                while not vehicle.armed:
                    if time.time() - startArming >= 5:
                        vehicle.armed = True
                        if time.time() - startArming >= 20:
                            break
                    else:
                        file_logger.info("Waiting for arming...")
                        time.sleep(0.5)
                vehicle.simple_takeoff(aTargetAltitude)
                startTakeOff = time.time()
            elif time.time() - startTakeOff >= 90:
                self.not_upper = True
                file_logger.info(' ******************************* Not running! *******************************')
                break
            file_logger.info("Altitude: " + str(vehicle.location.global_relative_frame.alt))
            # Break and return from function just below target altitude.
            if self.async_commands_thread.cancel == True:
                return
            if vehicle.location.global_relative_frame.alt >= aTargetAltitude * 0.8:
                file_logger.info("Reached target altitude")
                break
            time.sleep(1)

    def goTo(self, command):
        vehicle = self.drone.vehicle
        coordinates = json.loads(command.point)
        vehicle.airspeed = self.drone.work_air_speed
        vehicle.groundspeed = self.drone.work_ground_speed
        altitude = self.drone.work_altitude
        self.arm_and_takeoff(altitude)
        if self.async_commands_thread.cancel == False:
            if self.not_upper == False:
                point = LocationGlobalRelative(coordinates[0], coordinates[1], altitude)
                vehicle.simple_goto(point)
                distancetopoint = self.get_distance_metres(vehicle.location.global_frame, point)
                startdistance = distancetopoint
                startdistancetimestamp = time.time()
                while distancetopoint >= 1.5:
                    if time.time() - startdistancetimestamp >= 30:
                        if vehicle.armed == False:
                            self.not_running = True
                            file_logger.info(' ******************************* Not running! *******************************')
                            break
                    if self.async_commands_thread.cancel == False:
                        file_logger.info("distance to target point = " + str(distancetopoint))
                        time.sleep(1)
                        distancetopoint = self.get_distance_metres(vehicle.location.global_frame, point)
                    else:
                        break
    def handle(self, command):
        if command.type == 'waypoint':
            self.goTo(command)
    async def statistic_thread(self):
        await asyncio.sleep(0.5)
        service.writeData("history", self.drone.vehicle, self.drone.id)
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
                    'event': str(dontUploadsRecord.event),
                    'is_uploaded': str(dontUploadsRecord.is_uploaded),
                    'connection': True,
                    'copter_id': str(dontUploadsRecord.drone.id),
                }  # self.drone.connection.drone.connected
                # django.db.close_old_connections()
                try:

                    self.drone.connection.write_message(json.dumps({
                        'type': 'upload_statistic',
                        'data': data,
                    }))
                except Exception as e:
                    file_logger.info(e)
        except Exception as e:
            file_logger.info(e)
    def connect(self):
        global stop_sign
        self.drone.connected = False
        while self.drone.connected == False:
            try:
                # connection_string = "udpout:10.8.0.101:14550"
                self.vehicle = dronekit.connect(self.drone.connection_string, wait_ready=True)
                self.drone.connected = True
                self.drone.vehicle = self.vehicle
                my_location_alt = self.vehicle.location.global_frame
                self.vehicle.home_location = my_location_alt
                self.statistic_thread = DroneThread('statistic_thread', self.drone)
                self.statistic_thread.start()
                self.commands_thread = DroneThread('commands_thread', self.drone)
                self.commands_thread.start()
                self.exchange_thread = DroneThread('exchange_thread', self.drone)
                self.exchange_thread.start()
                threads_is_alive = self.statistic_thread.is_alive() and self.commands_thread.is_alive() and self.exchange_thread.is_alive()
                while threads_is_alive:
                    threads_is_alive = self.statistic_thread.is_alive() and self.commands_thread.is_alive() and self.exchange_thread.is_alive()
                    if self.vehicle.last_heartbeat > 15:
                        file_logger.info("drone connection closing... reconnection...")
                        self.vehicle.close()
                        self.drone.connected = False
                        return
                    else:
                        self.drone.connected = True
                        # futures = [self.statistic_thread(), self.commands_thread(), self.exchange_thread()]
                        # for future in asyncio.as_completed(futures):
                        #     result = await future
                        time.sleep(1)
                file_logger.info("statistic or comamnds thread is not alive...")
                self.vehicle.close()
                return
            except Exception as e:
                self.drone.connected = False
                file_logger.info(str(e))
                # self.vehicle.close()
                return

        # vehicle.wait_ready('autopilot_version')

    def run(self):
        file_logger.info("Drone '" + self.name + "' started")
        if self.name == "main_thread":
            asyncio.run(self.connect())
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
                                'coordinates': obj[0].coordinates,
                                'copter_id': obj[0].drone.id,
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
                                    'copter_id': obj[0].drone.id,
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
                                self.drone.connection.write_message({
                                    'type': 'exchange_response',
                                    'data_sended': {},
                                    'data_recieved': data_recieved
                                })
                                # time.sleep(1)
                            except Exception as e:
                                continue
                # time.sleep(2)
        elif self.name == "statistic_thread":
            asyncio.set_event_loop(asyncio.new_event_loop())
            while self.is_alive():
                time.sleep(0.5)
                service.writeData("history", self.drone.vehicle, self.drone.id)
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
                            'copter_id': str(dontUploadsRecord.drone.id),
                        } #self.drone.connection.drone.connected
                        #django.db.close_old_connections()
                        try:

                            self.drone.connection.write_message(json.dumps({
                                'type': 'upload_statistic',
                                'data': data,
                            }))
                        except Exception as e:
                            file_logger.info(e)
                            continue
                except Exception as e:
                    break

        elif self.name == "commands_thread":
            try:
                self.async_commands_thread = DroneThread('async_commands_thread', self.drone)
                self.async_commands_thread.start()
                while self.async_commands_thread.is_alive():
                    if self.drone.connected == True:
                        issetCommands = False
                        current_routes = Route.objects.filter(is_sync=True, status__in=['1'])
                        if len(current_routes) > 0:
                            current_route = current_routes[0]
                            counter = DroneCommand.objects.filter(route_uid=current_route.uid,  type='waypoint', status__in=['1', '2'])
                            if len(counter) == len(json.loads(current_route.coordinates)):
                                commands = DroneCommand.objects.filter(status="2", is_async=False,  type='waypoint', route_uid=current_route.uid).order_by('outer_id')  # Сначала ищем выполняющиеся в текущий момент (если было потеряно соединение)
                                if len(commands) > 0:
                                    self.go_to_commands(commands)
                                    issetCommands = True
                                commands = DroneCommand.objects.filter(status="1", is_async=False, type='waypoint', route_uid=current_route.uid).order_by('outer_id')  # Идем к следующей точке
                                if len(commands) > 0:
                                    self.go_to_commands(commands)
                                    issetCommands = True
                                if issetCommands == True:
                                    file_logger.info("Returning to Launch")
                                    self.drone.vehicle.mode = VehicleMode("RTL")
                                    if self.async_commands_thread.cancel == True:
                                        self.async_commands_thread.cancel = False
                                    else:
                                        current_route.status="2"
                                        current_route.save(update_fields=['status'])
                                        exchange_object = ExchangeObject(type="route", uid=current_route.uid)
                                        exchange_object.save()
                                    time.sleep(10)
                    else:
                        break
            except Exception as e:
                file_logger.info("***************** < error > ******************")
                file_logger.info(e)
                file_logger.info("***************** </ error > ******************")
        elif self.name == "async_commands_thread":
            try:
                while True:
                    commands = DroneCommand.objects.filter(is_async=True, status__in=["0", "1", "2"]).order_by(
                        'outer_id')
                    if len(commands) != 0:
                        for command in commands:
                            if command.type == 'cancel':
                                route_cancelled = Route.objects.filter(uid=command.route_uid).last()
                                cmds_cancelled = DroneCommand.objects.filter(status="4", route_uid=route_cancelled.uid, type='waypoint')
                                all_cmds = DroneCommand.objects.filter(route_uid=route_cancelled.uid, type='waypoint')
                                while len(cmds_cancelled) != len(all_cmds):
                                    file_logger.info('cmds_cancelled = '+str(len(cmds_cancelled)))
                                    file_logger.info('all_cmds = '+str(len(all_cmds)))

                                    cmds_cancelled = DroneCommand.objects.filter(status="4",route_uid=route_cancelled.uid,type='waypoint')
                                    all_cmds = DroneCommand.objects.filter(route_uid=route_cancelled.uid,type='waypoint')
                                    self.cancel = True
                                    command.status = "3"
                                    command.save(update_fields=['status'])
                                    exchange_object = ExchangeObject(type="command", uid=command.uid)
                                    exchange_object.save()
                                    commands = DroneCommand.objects.filter(status__in=["0", "1", "2", "3"], type='waypoint', route_uid=command.route_uid).order_by('outer_id')
                                    route_uid = ""
                                    for command in commands:
                                        command.status = "4"
                                        command.save(update_fields=['status'])
                                        route_uid = command.route_uid
                                        exchange_object = ExchangeObject(type="command", uid=command.uid)
                                        exchange_object.save()
                                    current_route = Route.objects.filter(uid=command.route_uid)
                                    if len(current_route) > 0:
                                        current_route[0].status = "4"
                                        current_route[0].save(update_fields=['status'])
                                        exchange_object = ExchangeObject(type="route", uid=route_uid)
                                        exchange_object.save()
                                    time.sleep(1)
                            # else:
                            #     current_route = Route.objects.filter(uid=command.route_uid)
                            #     if len(current_route) > 0:
                            #         if current_route[0].status == "4":
                            #             for cmd in commands:
                            #                 self.cancel = True
                            #                 cmd.status = "4"
                            #                 cmd.save(update_fields=['status'])
                            #                 exchange_object = ExchangeObject(type="command", uid=cmd.uid)
                            #                 exchange_object.save()
                            #             break
                    # else:
                    #     self.cancel = True
                    #     commands = DroneCommand.objects.filter(is_async=True, status__in=["0", "1", "2"]).order_by(
                    #         'outer_id')
                    #     if len(commands) != 0:
                    #         for command in commands:
                    #             command.status = "4"
                    #             command.save(update_fields=['status'])
                    #             exchange_object = ExchangeObject(type="command", uid=command.uid)
                    #             exchange_object.save()

                    time.sleep(1)
            except Exception as e:
                file_logger.info("***************** < error > ******************")
                file_logger.info(e)
                file_logger.info("***************** </ error > ******************")


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
        self.temporary_data = _temporary_data()
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
        file_logger.info("main_thread connection is not alive.. reconnection....")
        self.connect()

    # def handle_request(self, response):
    #     file_logger.info(response)
    # while True:
    #     file_logger.info(self.droneThreads["connection_thread"])
