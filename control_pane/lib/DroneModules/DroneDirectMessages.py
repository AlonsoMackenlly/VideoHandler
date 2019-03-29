import json
import time
import pickle
import django.db
from control_pane.models import History, Drone, Route, DroneCommand, ExchangeObject
from threading import Thread
from django.conf import settings
from importlib import import_module
from control_pane.lib.DroneModules.DataService import log
session_engine = import_module(settings.SESSION_ENGINE)
import inspect
import logging
def function_logger(file_level, console_level=None):
    function_name = inspect.stack()[1][3]
    logger = logging.getLogger(function_name)
    return logger

file_logger = function_logger(logging.INFO)

class DroneDirectMessages():
    @staticmethod
    def updateRecordsIntoOuterUUIDS(downloaded_uuids):
        firstid = downloaded_uuids[:downloaded_uuids.find("-")]
        firstid = int(firstid)
        lastid = downloaded_uuids[downloaded_uuids.find("-") + 1:]
        lastid = int(lastid)
        if firstid != 0 and lastid != 0:
            if firstid != lastid:
                intervalObjects = History.objects.filter(is_uploaded=False, pk__gte=firstid, pk__lte=lastid)
                if len(intervalObjects) > 0:
                    for intervalObject in intervalObjects:
                        intervalObject.is_uploaded = True
                        intervalObject.save(update_fields=['is_uploaded'])
                    django.db.close_old_connections()
            else:
                intervalObjects = History.objects.filter(id=firstid)
                if len(intervalObjects) > 0:
                    intervalObject = intervalObjects[0]
                    intervalObject.is_uploaded = True
                    intervalObject.save(update_fields=['is_uploaded'])
                    django.db.close_old_connections()

    @staticmethod
    def getLastHistoryObject():
        stats_obj = History.objects.last()
        if stats_obj != None:
            data = {
                'id': str(stats_obj.id),
                'history_timestamp': str(stats_obj.history_timestamp),
                'coordinates_alt': str(stats_obj.coordinates_alt),
                'air_speed': str(stats_obj.air_speed),
                'ground_speed': str(stats_obj.ground_speed),
                'is_armable': str(stats_obj.is_armable),
                'is_armed': str(stats_obj.is_armed),
                'status': str(stats_obj.status),
                'last_heartbeat': str(stats_obj.last_heartbeat),
                'mode': str(stats_obj.mode),
                'battery_voltage': str(stats_obj.battery_voltage),
                'battery_level': str(stats_obj.battery_level),
                'gps_fixed': str(stats_obj.gps_fixed),
                'event': str(stats_obj.event_id),
            }
            return data

    @staticmethod
    def handle(connection, message):
        if len(message) > 10000:
            return
        message = json.loads(message)
        log(message)
        session_key = connection.get_cookie(settings.SESSION_COOKIE_NAME)
        session = session_engine.SessionStore(session_key)
        
        if message['type'] == 'update_statistic':
            django.db.close_old_connections()
            stats_obj = History.objects.last()  # TODO: по id !!!! drone_id=int(message['id'])).last()

            data = {
                'history_timestamp': {
                    'year': stats_obj.history_timestamp.year,
                    'month': stats_obj.history_timestamp.month,
                    'day': stats_obj.history_timestamp.day,
                    'hour': stats_obj.history_timestamp.hour,
                    'minute': stats_obj.history_timestamp.minute,
                    'second': stats_obj.history_timestamp.second,
                },
                'coordinates_alt': str(stats_obj.coordinates_alt),
                'coordinates_lon': str(stats_obj.coordinates_lon),
                'coordinates_lat': str(stats_obj.coordinates_lat),
                'air_speed': str(stats_obj.air_speed),
                'ground_speed': str(stats_obj.ground_speed),
                'is_armable': str(stats_obj.is_armable),
                'is_armed': str(stats_obj.is_armed),
                'status': str(stats_obj.status),
                'last_heartbeat': str(stats_obj.last_heartbeat),
                'mode': str(stats_obj.mode),
                'battery_voltage': str(stats_obj.battery_voltage),
                'battery_level': str(stats_obj.battery_level),
                'gps_fixed': str(stats_obj.gps_fixed),
                'event': str(stats_obj.event_id),
                'connection': str(stats_obj.connection),
                'copter_uid': str(stats_obj.drone.id),
            }
            connection.write_message({
                'type': message['type'],
                'data': data
            })
        elif message['type'] == "route_sync":
            try:
                uid = message['data']['uid']
                route = Route.objects.filter(uid=uid)
                if len(route) == 0:
                    route = Route(
                        commands=message['data']['commands'],
                        drone=Drone.objects.get(outer_id=message['data']['copter_uid']),
                        is_done=message['data']['is_done'],
                        status=message['data']['status'],
                        uid=message['data']['uid'],
                        is_sync=True
                    )
                    route.save()
                    django.db.close_old_connections()
                    data = {
                        'uid': message['data']['uid'],
                        'is_sync': True
                    }
                    connection.write_message({
                        'type': 'route_sync',
                        'data': data,
                    })
                else:
                    route = Route.objects.get(uid=message['data']['uid'])
                    if route != None:
                        data = {
                            'uid': message['data']['uid'],
                            'is_sync': True
                        }
                        connection.write_message({
                            'type': 'route_sync',
                            'data': data,
                        })
            except Exception as e:
                log(e)
        elif message['type'] == "cmd_sync":
            uid = message['data']['uid']
            cmd = DroneCommand.objects.filter(uid=uid)
            if len(cmd) == 0:
                cmd = DroneCommand(
                    point=message['data']['point'],
                    drone=Drone.objects.get(outer_id=str(message['data']['copter_uid'])),
                    type=message['data']['type'],
                    status=message['data']['status'],
                    uid=uid,
                    is_sync=True,
                    is_async=message['data']['is_async'],
                    route_uid=message['data']['route_uid'],
                    outer_id=message['data']['outer_id'],
                    order=message['data']['order'],

                )
                cmd.save()
                exchange_object = ExchangeObject(type="command", uid=uid)
                exchange_object.save()

                data_sended = {}
                data_sended['result'] = 'ok'
                data_sended['object_type'] = 'DroneCommand'
                data_sended['uid'] = uid
                connection.write_message({
                    'type': 'exchange_response',
                    'data_sended': data_sended,
                    'data_recieved': {}
                })
            else:
                data_sended = {}
                data_sended['result'] = 'ok'
                data_sended['object_type'] = 'DroneCommand'
                data_sended['uid'] = uid
                connection.write_message({
                    'type': 'exchange_response',
                    'data_sended': data_sended,
                    'data_recieved': {}
                })
        elif message['type'] == "run_route":
            route_uid = ""
            for cmd_id in message['data']:
                cmds = DroneCommand.objects.filter(uid=message['data'][cmd_id]['uid'], type='waypoint')
                for cmd in cmds:
                    route_uid = cmd.route_uid
                    cmd.status = "1"#message['data'][cmd_id]['status']
                    cmd.save(update_fields=['status'])
            route_ = Route.objects.filter(uid=route_uid)
            if len(route_) > 0:
                route_[0].status = "1"
                route_[0].is_sync = True
                route_[0].save(update_fields=['status', 'is_sync'])
                # ex = ExchangeObject.objects.filter(type="route", uid=route_uid).last()
                # if ex == None:
                exchange_object = ExchangeObject(type="route", uid=route_uid)
                exchange_object.save()
        elif message['type'] == 'exchange_delete':
            if 'data_sended' in message:
                result = message['data_sended']
                if 'result' in message['data_sended']:
                    result = message['data_sended']['result']
                    if result == "ok":
                        if message['data_sended']['object_type'] == 'Route':
                            obj = ExchangeObject.objects.filter(uid=message['data_sended']['uid'])
                            if len(obj) > 0:
                                obj[0].delete()
                        elif message['data_sended']['object_type'] == 'DroneCommand':
                            obj = ExchangeObject.objects.filter(uid=message['data_sended']['uid'])
                            if len(obj) > 0 or len(DroneCommand.objects.filter(uid=message['data_sended']['uid'])) > 0:
                                drone_obj = DroneCommand.objects.get(uid=message['data_sended']['uid'])
                                drone_obj.is_sync = True
                                drone_obj.save(update_fields=['is_sync'])
                                if len(obj) > 0:
                                    obj[0].delete()
            elif 'route_uid' in message:
                cmds = DroneCommand.objects.filter(route_uid=message['route_uid'])
                if len(cmds) > 0:
                    uids = []
                    for cmd in cmds:
                        uids.append(cmd.uid)
                    exchange_objects = ExchangeObject.objects.filter(uid__in=uids)
                    if len(exchange_objects) > 0:
                        exchange_objects.delete()
                    exchange_objects = ExchangeObject.objects.filter(uid=message['route_uid'])
                    if len(exchange_objects) > 0:
                        exchange_objects.delete()
                    route = Route.objects.filter(uid=message['route_uid']).last()
                    if route != None:
                        route.is_sync = False
                        route.save(update_fields=['is_sync'])
                        exchange_object = ExchangeObject(type="route", uid=message['route_uid'])
                        exchange_object.save()
        elif message['type'] == 'exchange_response':
            result = message['data_sended']
            if 'result' in message['data_sended'] :
                result = message['data_sended']['result']
                if result == "ok" :
                    if message['data_sended']['object_type'] == 'Event' :
                        obj = ExchangeObject.objects.filter(uid = message['data_sended']['uid'])
                        if len(obj) > 0 :
                            obj[0].delete()
        elif message['type'] == 'exchange_request':
            django.db.close_old_connections()
            data_sended = {}
            data_recieved = {}
            # ************************************ SENDED ******************************************
            if 'object_type' in message['data']:
                if message['data']['object_type'] == 'Route':
                    route = Route.objects.filter(uid=message['data']['uid'])
                    if len(route) > 0:
                        exchange_objects = ExchangeObject.objects.filter(uid=message['data']['uid'])
                        if len(exchange_objects) == 0:
                            route[0].commands = message['data']['commands']
                            route[0].drone = Drone.objects.get(outer_id=message['data']['copter_uid'])
                            route[0].is_done = message['data']['is_done']
                            route[0].status = message['data']['status']
                            route[0].is_sync = True#message['data']['is_sync']
                            route[0].save(update_fields=['commands', 'drone', 'is_done', 'status', 'is_sync'])
                            # exchange_object = ExchangeObject(type="route", uid=message['data']['uid'])
                            # exchange_object.save()
                            data_sended['result'] = 'ok'
                            data_sended['object_type'] = 'Route'
                            data_sended['uid'] = message['data']['uid']
                        else:
                            data_sended['result'] = 'ok'
                            data_sended['object_type'] = 'Route'
                            data_sended['uid'] = message['data']['uid']
                    else:
                        data_sended['result'] = 'fail'
                elif message['data']['object_type'] == 'DroneCommand':
                    cmd_ = DroneCommand.objects.filter(uid=message['data']['uid'])
                    if len(cmd_) > 0:
                        cmd_[0].type = message['data']['type']
                        cmd_[0].point = message['data']['point']
                        cmd_[0].drone = Drone.objects.get(outer_id=message['data']['copter_uid'])
                        cmd_[0].status = message['data']['status']
                        cmd_[0].is_sync = True
                        cmd_[0].is_async = message['data']['is_async']
                        cmd_[0].outer_id = message['data']['outer_id']
                        cmd_[0].order = message['data']['order']
                        cmd_[0].save(update_fields=['type', 'point', 'drone', 'status', 'is_sync', 'is_async', 'outer_id', 'order'])
                        # exchange_object = ExchangeObject(type="command", uid=message['data']['uid'])
                        # exchange_object.save()
                        data_sended['result'] = 'ok'
                        data_sended['object_type'] = 'DroneCommand'
                        data_sended['uid'] = message['data']['uid']
                    else:
                        data_sended['result'] = 'fail'
                elif message['data']['object_type'] == 'Drone':
                    drone_ = Drone.objects.filter(outer_id=message['data']['uid'])
                    if len(drone_) > 0:
                        try:
                            drone_[0].rtl = message['data']['rtl']
                            drone_[0].save(update_fields=['rtl'])
                        except Exception as e:
                            log(e)
                        data_sended['result'] = 'ok'
                        data_sended['object_type'] = 'Drone'
                        data_sended['uid'] = message['data']['uid']

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
                                    'result': 'ok',
                                    'outer_id': obj[0].outer_id,
                                    'order': obj[0].order,
                                }
                            else:
                                data_recieved = {
                                    'result': 'no'
                                }
                if len(data_sended) > 0 or len(data_recieved) > 0:
                    connection.write_message({
                        'type': 'exchange_response',
                        'data_sended': data_sended,
                        'data_recieved': data_recieved
                    })
                    #time.sleep(2)
                    #ExchangeObject.objects.filter().delete()
        elif message['type'] == 'delete_data':
            History.objects.filter().delete()
            ExchangeObject.objects.filter().delete()
            Route.objects.filter().delete()
            DroneCommand.objects.filter().delete()