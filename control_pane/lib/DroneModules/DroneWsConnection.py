import threading
import urllib
import json
import django.db
from threading import ThreadError
from threading import Thread
from control_pane.models import History
from control_pane.models import Drone, DroneCommand
from control_pane.models import Route
from control_pane.models import ExchangeObject

import time
from django.conf import settings
import websocket
from websocket import WebSocket
from websocket import create_connection


# websocket.enableTrace(False)

class WebsocketThread(Thread):
    def __init__(self, thread_name, drone, *args, **kwargs):
        Thread.__init__(self, *args, **kwargs)
        self.thread_name = thread_name
        if self.thread_name == "statistic":
            self.should_terminate = False
        self.drone = drone
        self.statistic_thread = ""
        self.command_thread = ""
        self.routes_thread = ""
        self.msgReciever_thread1 = ""
        self.msgReciever_thread2 = ""
        self.msgReciever_thread3 = ""
        self.msgReciever_thread4 = ""
        self.msgReciever_thread5 = ""
        self.msgReciever_thread6 = ""
        self.msgReciever_thread7 = ""
        self.msgReciever_thread8 = ""
        self.msgReciever_thread9 = ""
        self.msgReciever_thread10 = ""

        self.kill = False

    def timerStart(self):
        timeout_thread = Thread(target=self.start_timeout_recv, args=(time.time(),))
        timeout_thread.start()
        self.drone.isRecieved = False

    def timerEnd(self):
        self.drone.isRecieved = True
        self.drone.last_request_time = time.time()

    def run(self):
        if self.thread_name == "main":
            self.sync_thread = WebsocketThread("sync_copter", self.drone)
            self.sync_thread.start()
            self.statistic_thread = WebsocketThread("statistic", self.drone)
            self.statistic_thread.start()
            self.command_thread = WebsocketThread("commands", self.drone)
            self.command_thread.start()
            self.routes_thread = WebsocketThread("routes", self.drone)
            self.routes_thread.start()
            self.exchange_thread = WebsocketThread("exchange", self.drone)
            self.exchange_thread.start()
            self.msgReciever_thread1 = WebsocketThread("msgReciever", self.drone)
            self.msgReciever_thread1.start()
            # self.msgReciever_thread2 = WebsocketThread("msgReciever", self.drone)
            # self.msgReciever_thread2.start()
            # self.msgReciever_thread3 = WebsocketThread("msgReciever", self.drone)
            # self.msgReciever_thread3.start()
            # self.msgReciever_thread4 = WebsocketThread("msgReciever", self.drone)
            # self.msgReciever_thread4.start()
            # self.msgReciever_thread5 = WebsocketThread("msgReciever", self.drone)
            # self.msgReciever_thread5.start()
            # self.msgReciever_thread6 = WebsocketThread("msgReciever", self.drone)
            # self.msgReciever_thread6.start()
            # self.msgReciever_thread7 = WebsocketThread("msgReciever", self.drone)
            # self.msgReciever_thread7.start()
            # self.msgReciever_thread8 = WebsocketThread("msgReciever", self.drone)
            # self.msgReciever_thread8.start()
            # self.msgReciever_thread9 = WebsocketThread("msgReciever", self.drone)
            # self.msgReciever_thread9.start()
            # self.msgReciever_thread10 = WebsocketThread("msgReciever", self.drone)
            # self.msgReciever_thread10.start()
            while self.statistic_thread.is_alive() and self.command_thread.is_alive() and self.routes_thread.is_alive() and self.kill == False:
                if not type(self.statistic_thread) is str:
                    if not type(self.statistic_thread.should_terminate) is str:
                        # print("should_terminate = " + str(self.statistic_thread.should_terminate))
                        if self.statistic_thread.should_terminate == True:
                            print("ABORTING!!!!!!!!!!!!!!!!!!")
                            self.statistic_thread.kill = True
                            self.command_thread.kill = True
                            self.routes_thread.kill = True
                            self.kill = True
            self.statistic_thread.kill = True
            self.command_thread.kill = True
            self.routes_thread.kill = True
            self.kill = True
            self.drone.ws.close()
            self.drone.stop_signal = False
            self.drone.connected = False
            self.statistic_thread.join()
            self.command_thread.join()
            self.raiseExc()
            return
        elif self.thread_name == "msgReciever":
            while self.drone.stop_signal == False and self.kill == False:
                self.timerStart()
                ret, result = self.drone.ws.recv_data(True)
                self.timerEnd()
                if ret == 1:
                    try:
                        message = json.loads(result)
                        print(message)
                        if message['type'] == 'upload_statistic':
                            # continue
                            for stat_id in message['data']:
                                if 'id' in message['data'][stat_id]:
                                    record_find = History.objects.filter(outer_id=message['data'][stat_id]['id'])
                                    if len(record_find) == 0:
                                        record = History(
                                            is_uploaded=True,
                                            outer_id=message['data'][stat_id]['id'],
                                            history_timestamp=message['data'][stat_id]['history_timestamp'][
                                                'django_format'],
                                            coordinates_alt=message['data'][stat_id]['coordinates_alt'],
                                            coordinates_lat=message['data'][stat_id]['coordinates_lat'],
                                            coordinates_lon=message['data'][stat_id]['coordinates_lon'],
                                            air_speed=message['data'][stat_id]['air_speed'],
                                            ground_speed=message['data'][stat_id]['ground_speed'],
                                            is_armable=message['data'][stat_id]['is_armable'],
                                            is_armed=message['data'][stat_id]['is_armed'],
                                            status=message['data'][stat_id]['status'],
                                            last_heartbeat=message['data'][stat_id]['last_heartbeat'],
                                            mode=message['data'][stat_id]['mode'],
                                            battery_voltage=message['data'][stat_id]['battery_voltage'],
                                            battery_level=message['data'][stat_id]['battery_level'],
                                            gps_fixed=message['data'][stat_id]['gps_fixed'],
                                            connection=message['data'][stat_id]['connection'],
                                            drone=Drone.objects.get(outer_id=int(message['data'][stat_id]['copter_id']))
                                        )
                                        record.save()
                                        self.drone.last_download = time.time()
                            django.db.close_old_connections()
                        elif message['type'] == 'route_sync':
                            record = Route.objects.get(uid=message['data']['uid'])
                            record.is_sync = True
                            record.save(update_fields=['is_sync'])
                            self.drone.last_download = time.time()
                            django.db.close_old_connections()
                        elif message['type'] == 'stop':
                            rec = DroneCommand.objects.get(uid=message['data']['uid'])
                            rec.is_sync = True
                            rec.save(update_fields=['is_sync'])
                            r = ExchangeObject.objects.filter(uid=message['data']['uid'])
                            if len(r) > 0:
                                r.delete()
                            # if 'status' in message['data']:
                            #     rec.status = message['data']['status']
                            #     rec.save(update_fields=['is_sync', 'status'])
                            # else:
                            #     rec.save(update_fields=['is_sync'])
                            #self.drone.last_download = time.time()
                            # exchange_object = ExchangeObject(type="command", uid=rec.uid)
                            # exchange_object.save()
                            #django.db.close_old_connections()
                        elif message['type'] == "exchange_response":
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
                                        if len(obj) > 0:
                                            drone_obj = DroneCommand.objects.get(uid=message['data_sended']['uid'])
                                            drone_obj.is_sync = True
                                            drone_obj.save(update_fields=['is_sync'])
                                            obj[0].delete()
                                # recieve updates
                            if 'result' in message['data_recieved']:
                                result = message['data_recieved']['result']
                                if result == 'ok':
                                    data_response = {}
                                    if message['data_recieved']['object_type'] == 'Route':
                                        route = Route.objects.filter(uid=message['data_recieved']['uid'])
                                        if len(route) > 0:
                                            route[0].coordinates = message['data_recieved']['coordinates']
                                            route[0].drone = Drone.objects.get(
                                                outer_id=int(message['data_recieved']['copter_id']))
                                            route[0].is_done = message['data_recieved']['is_done']
                                            route[0].status = message['data_recieved']['status']
                                            route[0].is_sync = message['data_recieved']['is_sync']
                                            route[0].save(
                                                update_fields=['coordinates', 'drone', 'is_done', 'status', 'is_sync'])
                                            data_response['result'] = 'ok'
                                            data_response['type'] = 'route'
                                        else:
                                            data_response['result'] = 'fail'
                                            data_response['type'] = 'route'
                                    elif message['data_recieved']['object_type'] == 'DroneCommand':
                                        cmd_ = DroneCommand.objects.filter(uid=message['data_recieved']['uid'])
                                        if len(cmd_) > 0:
                                            need_exchange = False
                                            if cmd_[0].type != message['data_recieved']['type']:
                                                need_exchange = True
                                                cmd_[0].type = message['data_recieved']['type']
                                            if cmd_[0].point != message['data_recieved']['point']:
                                                cmd_[0].point = message['data_recieved']['point']
                                                need_exchange = True
                                            if cmd_[0].drone != Drone.objects.get(outer_id=int(message['data_recieved']['copter_id'])):
                                                cmd_[0].drone = Drone.objects.get(outer_id=int(message['data_recieved']['copter_id']))
                                                need_exchange = True
                                            if cmd_[0].status != message['data_recieved']['status']:
                                                cmd_[0].status = message['data_recieved']['status']
                                                need_exchange = True
                                            if cmd_[0].is_sync != message['data_recieved']['is_sync']:
                                                cmd_[0].is_sync = message['data_recieved']['is_sync']
                                                need_exchange = True
                                            if cmd_[0].is_async != message['data_recieved']['is_async']:
                                                cmd_[0].is_async = message['data_recieved']['is_async']
                                                need_exchange = True
                                            if need_exchange == True:
                                                cmd_[0].save(
                                                    update_fields=['type', 'point', 'drone', 'status', 'is_sync',
                                                                   'is_async'])
                                                ex = ExchangeObject.objects.filter(type="command", uid=cmd_[0].uid).last()
                                                if ex == None:
                                                    exchange_object = ExchangeObject(type="command", uid=cmd_[0].uid)
                                                    exchange_object.save()
                                            data_response['result'] = 'ok'
                                            data_response['type'] = 'cmd'
                                        else:
                                            data_response['result'] = 'fail'
                                            data_response['type'] = 'cmd'
                                    elif message['data_recieved']['object_type'] == 'History':
                                        h_ = History.objects.filter(outer_id=message['data_recieved']['id'])
                                        if len(h_) == 0:
                                            record = History(
                                                coordinates_lon=message['data_recieved']['coordinates_lon'],
                                                coordinates_lat=message['data_recieved']['coordinates_lat'],
                                                coordinates_alt=message['data_recieved']['coordinates_alt'],
                                                air_speed=message['data_recieved']['air_speed'],
                                                ground_speed=message['data_recieved']['ground_speed'],
                                                is_armable=message['data_recieved']['is_armable'],
                                                is_armed=message['data_recieved']['is_armed'],
                                                status=message['data_recieved']['status'],
                                                last_heartbeat=message['data_recieved']['last_heartbeat'],
                                                mode=message['data_recieved']['mode'],
                                                battery_voltage=message['data_recieved']['battery_voltage'],
                                                # data.battery.voltage,
                                                battery_level=message['data_recieved']['battery_level'],
                                                # data.battery.level,
                                                gps_fixed=message['data_recieved']['gps_fixed'],
                                                uid=message['data_recieved']['uid'],
                                                is_uploaded=True,
                                                drone_id=message['data_recieved']['copter_id'])
                                            record.save()
                                            data_response['result'] = 'ok'
                                            data_response['type'] = 'history'
                                        else:
                                            data_response['result'] = 'fail'
                                            data_response['type'] = 'history'
                                    data_response['uid'] = message['data_recieved']['uid']
                                    data_response['object_type'] = message['data_recieved']['object_type']
                                    if data_response['result'] == 'ok':
                                        self.drone.ws.send(json.dumps({
                                            'type': 'exchange_response',
                                            'data': data_response,
                                        }))
                        elif message['type'] == "exchange_request":
                            # ************************************ SENDED ******************************************
                            data_sended = {}
                            if message['data']['object_type'] == 'Route':
                                route = Route.objects.filter(uid=message['type']['data']['uid'])
                                if len(route) > 0:
                                    route[0].coordinates = message['type']['data']['coordinates']
                                    route[0].drone = Drone.objects.get(
                                        outer_id=int(message['type']['data']['copter_id']))
                                    route[0].is_done = message['type']['data']['is_done']
                                    route[0].status = message['type']['data']['status']
                                    route[0].is_sync = True
                                    route[0].save(
                                        update_fields=['coordinates', 'drone', 'is_done', 'status', 'is_sync'])
                                    data_sended['result'] = 'ok'
                                    data_sended['object_type'] = 'Route'
                                    data_sended['uid'] = message['type']['data']['uid']
                                else:
                                    data_sended['result'] = 'fail'
                            elif message['data']['object_type'] == 'DroneCommand':
                                cmd_ = DroneCommand.objects.filter(uid=message['data']['uid'])
                                if len(cmd_) > 0:
                                    cmd_[0].type = message['data']['type']
                                    cmd_[0].point = message['data']['point']
                                    cmd_[0].drone = Drone.objects.get(outer_id=int(message['data']['copter_id']))
                                    cmd_[0].status = message['data']['status']
                                    cmd_[0].is_sync = True
                                    cmd_[0].is_async = message['data']['is_async']
                                    cmd_[0].save(
                                        update_fields=['type', 'point', 'drone', 'status', 'is_sync', 'is_async'])
                                    data_sended['result'] = 'ok'
                                    data_sended['object_type'] = 'DroneCommand'
                                    data_sended['uid'] = message['data']['uid']
                                else:
                                    data_sended['result'] = 'fail'
                            # self.drone.ws.send(json.dumps({
                            #     {
                            #         'type': 'exchange_response',
                            #         'data': data_sended,
                            #     }
                            # }))

                    except Exception as e:
                        print(e)
                        self.drone.ws.close()
                        self.drone.stop_signal = True
                        self.drone.connected = False
                        return

        elif self.thread_name == "statistic":
            while self.drone.stop_signal == False and self.kill == False:
                time.sleep(1)
                try:
                    first_obj = History.objects.order_by('id').filter(is_uploaded=True, drone_id=self.drone.id).first()
                    last_obj = History.objects.order_by('id').filter(is_uploaded=True, drone_id=self.drone.id).last()
                    if first_obj != None:
                        first_id = first_obj.outer_id
                        last_id = last_obj.outer_id
                    else:
                        first_id = 0
                        last_id = 0
                    self.drone.ws.send(json.dumps({
                        'type': 'download_statistic',
                        'downloaded_uuids': str(first_id) + '-' + str(last_id)
                    }))
                    time.sleep(0.1)
                except Exception as e:
                    print(e)
                    self.drone.ws.close()
                    self.drone.stop_signal = True
                    self.drone.connected = False
                    return
            return
        elif self.thread_name == "sync_copter":
            while self.kill == False:
                time.sleep(10)
        elif self.thread_name == "routes":
            while self.drone.stop_signal == False and self.kill == False:
                try:
                    not_sync_route = Route.objects.filter(drone_id=self.drone.id, is_sync=False)
                    if len(not_sync_route) == 0:
                        continue
                    else:
                        not_sync_route = not_sync_route[0]
                    self.drone.ws.send(json.dumps({
                        'type': 'route_sync',
                        'data': {
                            'uid': not_sync_route.uid,
                            'coordinates': not_sync_route.coordinates,
                            'copter_id': not_sync_route.drone.id,
                            'is_done': not_sync_route.is_done,
                            'status': not_sync_route.status,
                            'is_sync': not_sync_route.is_sync
                        }
                    }))
                    time.sleep(0.1)
                except Exception as e:
                    print(e)
                    self.drone.ws.close()
                    self.drone.stop_signal = True
                    self.drone.connected = False
                    return
            return
        elif self.thread_name == "commands":
            while self.drone.stop_signal == False and self.kill == False:
                try:

                    not_sync_cmds = DroneCommand.objects.filter(drone_id=self.drone.id, is_sync=False)
                    if len(not_sync_cmds) == 0:
                        continue
                    else:
                        for not_sync_cmd in not_sync_cmds:
                            self.drone.ws.send(json.dumps({
                                'type': 'cmd_sync',
                                'data': {
                                    'uid': not_sync_cmd.uid,
                                    'type': not_sync_cmd.type,
                                    'copter_id': not_sync_cmd.drone.id,
                                    'point': not_sync_cmd.point,
                                    'status': not_sync_cmd.status,
                                    'is_sync': not_sync_cmd.is_sync,
                                    'is_async': not_sync_cmd.is_async,
                                    'route_uid': not_sync_cmd.route_uid,
                                    'outer_id': not_sync_cmd.outer_id,
                                }
                            }))
                except Exception as e:
                    print(e)
                    self.drone.ws.close()
                    self.drone.stop_signal = True
                    self.drone.connected = False
                    return
            return
        elif self.thread_name == "exchange":
            while self.drone.stop_signal == False and self.kill == False:
                time.sleep(0.2)
                packages = ExchangeObject.objects.all()

                if len(packages) > 0:
                    for package in packages:
                        data = {}
                        obj = Route.objects.filter(uid=package.uid, is_sync=False)
                        if len(obj) > 0:
                            data = {
                                'uid': obj[0].uid,
                                'coordinates': obj[0].coordinates,
                                'copter_id': obj[0].drone.id,
                                'is_done': obj[0].is_done,
                                'status': obj[0].status,
                                'is_sync': obj[0].is_sync,
                                'object_type': 'Route'
                            }
                        else:
                            obj = DroneCommand.objects.filter(uid=package.uid)
                            if len(obj) > 0:
                                data = {
                                    'uid': obj[0].uid,
                                    'type': obj[0].type,
                                    'point': obj[0].point,
                                    'copter_id': obj[0].drone.outer_id,
                                    'uid': obj[0].uid,
                                    'status': obj[0].status,
                                    'is_sync': obj[0].is_sync,
                                    'is_async': obj[0].is_async,
                                    'object_type': 'DroneCommand'
                                }

                        self.drone.ws.send(json.dumps({
                            'type': 'exchange_request',
                            'data': data,
                        }))

                else:
                    self.drone.ws.send(json.dumps({
                        'type': 'exchange_request',
                        'data': {
                            'object_type': 'None'
                        },
                    }))
                    time.sleep(1)

    def start_timeout_recv(self, last_time):
        # print(self.drone.isRecieved)
        while self.drone.isRecieved == False:
            # print(time.time() - last_time)
            if time.time() - last_time >= 5:
                # self.drone.ws.abort()
                self.should_terminate = True
                return
        return

    def raiseExc(self):
        self.kill = True
        # raise ThreadError("close [" + self.thread_name + "]...")


class _Drone(object):
    def __init__(self, connection_string, id):
        self.id = id
        self.connected = False
        self.stop_signal = False
        self.ws = ""
        self.isRecieved = False
        connection_thread = Thread(target=self.connection, args=(connection_string,))
        connection_thread.start()

    def connection(self, connection_string):
        try:
            self.ws = WebSocket()
            self.ws.connect(connection_string)
            # self.ws = create_connection(connection_string)
            self.connected = True

            main_thread = WebsocketThread("main", self)  # Thread(target=self.loopMain)
            main_thread.start()
            print('drone: ' + connection_string + " started.")
            while main_thread.is_alive():
                time.sleep(1)
        except Exception as e:
            print(e)
            time.sleep(1)
        django.db.close_old_connections()
        print("drone websocket connection is not alive... reconnection...")
        self.connection(connection_string)

    @staticmethod
    def init():
        drones = Drone.objects.filter()
        result = {}
        for _drone in drones:
            drone_ws_connection_ip = _drone.connection_ip
            drone_id = _drone.id
            print("drone - " + drone_ws_connection_ip + " initialize...")
            result[drone_id] = _Drone(drone_ws_connection_ip, drone_id)
        return result
