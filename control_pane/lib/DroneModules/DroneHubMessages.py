import json
from control_pane.models import History, Route, Drone, DroneCommand, ExchangeObject
import uuid
import  time
# class DroneHubRouteMessages:
#     @staticmethod
#     def change_route_state(connection, message):
#


class DroneHubMessages:
    @staticmethod
    def handle(connection, message):
        if not message:
            return
        if len(message) > 10000:
            return
        message = json.loads(message)
        if message['type'] == 'update_statistic':
            stats_obj = History.objects.last()  # TODO: по id !!!! drone_id=int(message['id'])).last()

            if stats_obj != None:
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
                    'event': str(stats_obj.event),
                    'connection': str(stats_obj.connection),
                    'copter_id': str(stats_obj.drone.id),
                    # 'is_uploaded': str(stats_obj.is_uploaded)
                }
                connection.write_message({
                    'type': message['type'],
                    'data': data
                })
        elif message['type'] == 'upload_route':
            # time.sleep(1)
            record = Route(
                coordinates=json.dumps(message['route']['coordinates']),
                drone=Drone.objects.get(id=message['copter_id']),
                is_done=message['is_done'],
                uid=message['uid'],
                is_sync=message['is_sync']
            )
            record.save()
            points = {}

            for i in message['route']['coordinates']:
                point = DroneCommand(
                    type="waypoint",
                    point=json.dumps(message['route']['coordinates'][i]['coordinates']),
                    drone=Drone.objects.get(id=message['copter_id']),
                    uid=message['route']['coordinates'][i]['uid'],
                    status="0",
                    route_uid=message['uid'],
                    is_sync=False
                )
                point.save()
                point.outer_id = point.id
                point.save(update_fields=['outer_id'])
                points[i] = {
                    'id': point.id,
                    'type': 'waypoint',
                    'coordinates': message['route']['coordinates'][i]['coordinates'],
                    'uid': message['route']['coordinates'][i]['uid'],
                    'status': '0'
                }
            # is_sync = False
            # while is_sync == False:
            #     commands = DroneCommand.objects.filter(status="0")
            #     sync_cmd_len = 0
            #     for command in commands:
            #         if command.is_sync == True:
            #             sync_cmd_len += 1
            #     is_sync = len(commands) == sync_cmd_len
            # if is_sync == True:
            request = {
                'type': 'change_route_status',
                'data': {
                    'uid': message['uid'],
                    'copter_id': message['copter_id'],
                    'points': points,
                    'status': "0"
                }
            }
            connection.write_message(request)
        elif message['type'] == 'check_route_status':
            if 'uid' in message['data']:
                routes = Route.objects.filter(uid=message['data']['uid'])
                if len(routes) > 0:
                    route = routes[0]
                    status = route.status
                    points = DroneCommand.objects.filter(route_uid=message['data']['uid'])
                    points_res = {}
                    if len(points) > 0:
                        for point in points:
                            if point.point != None:
                                points_res[point.id] = {
                                    'type': point.type,
                                    'point': json.loads(point.point),
                                    # 'copter_id':
                                    'uid': point.uid,
                                    'status': point.status,
                                }
                    request = {
                        'type': 'change_route_status',
                        'data': {
                            'uid': message['data']['uid'],
                            'copter_id': message['data']['copter_id'],
                            'points': points_res,
                            'status': status
                        }
                    }
                    connection.write_message(request)
        elif message['type'] == 'run_route':
            commands = DroneCommand.objects.filter(status="0", drone_id=message['copter_id']).order_by("id")
            data = {}
            route_uid = ""
            for cmd in commands:
                cmd.status = "1"
                cmd.is_sync = True
                route_uid = cmd.route_uid
                cmd.save(update_fields=['status', 'is_sync'])
                print("OUTER_ID = " + str(cmd.outer_id))
                data[cmd.id] = {
                    "uid": cmd.uid,
                    "status": cmd.status,
                    "is_sync": cmd.is_sync,
                    "outer_id": cmd.outer_id
                }
            routes = Route.objects.filter(uid=route_uid)
            if len(routes) > 0:
                routes[0].status = "1"
                routes[0].save(update_fields=['status'])
                ex = ExchangeObject.objects.filter(type="route", uid=routes[0].uid).last()
                if ex == None:
                    exchange_object = ExchangeObject(type="route", uid=routes[0].uid)
                    exchange_object.save()
            request = {
                'type': 'run_route',
                'data': data
            }
            connection.drones[int(message['copter_id'])].ws.send(json.dumps(request))
        elif message['type'] == 'cancel_route':
            route = Route.objects.get(uid=message['uid'], drone_id=message['copter_id'], status__in=['0', '1', '2'])
            route.status = "4"
            route.save(update_fields=['status'])
            ex = ExchangeObject.objects.filter(type="route", uid=message['uid']).last()
            if ex == None:
                exchange_object = ExchangeObject(type="route", uid=message['uid'])
                exchange_object.save()
            cancel_cmd = DroneCommand.objects.filter(route_uid=message['uid'], type='cancel', status__in=['0','1','2'])
            if len(cancel_cmd) == 0:
                uid_cmd = str(uuid.uuid1())
                cancel_cmd = DroneCommand(
                    type='cancel',
                    drone_id=message['copter_id'],
                    route_uid=message['uid'],
                    is_async=True,
                    is_sync=False,
                    status="0",
                    uid=uid_cmd
                )
                cancel_cmd.save()
                connection.drones[int(message['copter_id'])].ws.send({
                    'type': 'cmd_sync',
                    'data': {
                        'uid': uid_cmd,
                        'type': 'cancel',
                        'copter_id': message['copter_id'],
                        'point': '',
                        'status': '0',
                        'is_sync': False,
                        'is_async': True,
                        'route_uid': message['uid'],
                    }
                })
