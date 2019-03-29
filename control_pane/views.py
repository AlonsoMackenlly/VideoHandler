from django.conf import settings
from control_pane.models import Drone, History, DronePlane, Route, DroneCommand, ExchangeObject, Stream
from django.shortcuts import render
import json


# Create your views here.
def index(request):
    if not request.user.is_authenticated:
        return render(request, "control_pane/access.html")
    else:
        return render(request, 'control_pane/index.html', {'show_head': 'Y'})


def deleteData(request):
    History.objects.filter().delete()
    ExchangeObject.objects.filter().delete()
    Route.objects.filter().delete()
    DroneCommand.objects.filter().delete()


def control(request):
    if not request.user.is_authenticated:
        return render(request, "control_pane/access.html")
    else:
        bases = DronePlane.objects.filter().values()
        js_params = {
            'copters': {},
            'bases': {}
        }
        for base in bases:
            js_params['bases'] = {
                base['id']: {
                    'id': base['id'],
                    'name': base['name'],
                    'coordinates_lat': base['coordinates_lat'],
                    'coordinates_lon': base['coordinates_lon'],
                }
            }
            drones = Drone.objects.filter(drone_plane_id=base['id']).order_by('id').values()
            routes = {}
            i = 0
            drones_view = []
            for drone in drones:
                properties = History.objects.filter(drone_id=drone['id']).last()
                rtl = ""
                if drone['rtl'] is not None and drone['rtl'] != "":
                    rtl = json.loads(drone['rtl'])
                camera_color = Stream.objects.filter(id=drone['camera_color_id']).last()
                color_cam = None
                if camera_color is not None:
                    color_cam = settings.DRONE_IP + ":" + settings.VIDEO_PORT + "/stream?title=" + camera_color.title
                thermal_cam = None
                camera_thermal = Stream.objects.filter(id=drone['camera_thermal_id']).last()
                if camera_thermal is not None:
                    thermal_cam = settings.DRONE_IP + ":" + settings.VIDEO_PORT + "/stream?title=" + camera_thermal.title
                js_params['copters'][drone['id']] = {
                    'id': drone['id'],
                    'name': drone['name'],
                    'base_id': base['id'],
                    'camera_color': color_cam,
                    'camera_thermal': thermal_cam,
                    'home_location': rtl,
                    'properties': {

                    }
                }
                print(js_params['copters'][drone['id']])
                if properties is not None:
                    js_params['copters'][drone['id']]['properties'] = {
                        'last_heartbeat': properties.last_heartbeat,  # TODO: дополнить остальными свойствами
                        'coordinates_lon': properties.coordinates_lon,
                        'coordinates_lat': properties.coordinates_lat,
                        'coordinates_alt': properties.coordinates_alt,
                        'air_speed': properties.air_speed,
                        'ground_speed': properties.ground_speed,
                        'is_armable': properties.is_armable,
                        'is_armed': properties.is_armed,
                        'status': properties.status,
                        'last_heartbeat': properties.last_heartbeat,
                        'mode': properties.mode,
                        'battery_voltage': properties.battery_voltage,
                        'battery_level': properties.battery_level,
                        'gps_fixed': properties.gps_fixed,
                        'connection': properties.connection,
                    }
                else:
                    js_params['copters'][drone['id']]['properties'] = {

                    }
                route = Route.objects.filter(drone_id=drone['id'], status__in=['0', '1', '3']).last()
                if route is None:
                    route = Route.objects.filter(drone_id=drone['id'], status__in=['2', '4']).last()
                if route is None:
                    routes[drone['id']] = {}
                    route = {
                        'commands': {},
                        'drone_id': drone['id'],
                        'status': -1,
                        'uid': 0
                    }
                else:
                    points = DroneCommand.objects.filter(drone_id=drone['id'], type='waypoint',
                                                         route_uid=route.uid).order_by('order').values()
                    points_result = {}
                    for point in points:
                        points_result[point['id']] = {}
                        points_result[point['id']]['id'] = point['id']
                        points_result[point['id']]['type'] = point['type']
                        points_result[point['id']]['drone_id'] = point['drone_id']
                        points_result[point['id']]['uid'] = point['uid']
                        points_result[point['id']]['status'] = point['status']
                        points_result[point['id']]['geo'] = json.loads(point['point'])  # TODO: оставить какой-то из них
                        points_result[point['id']]['coordinates'] = json.loads(point['point'])
                        points_result[point['id']]['order'] = point['order']
                        points_result[point['id']]['route_uid'] = point['route_uid']

                    cmds = {}
                    for key in sorted(points_result.keys()):
                        cmds[int(points_result[key]['order'])] = points_result[key]
                    commands_result = {}
                    for key in sorted(cmds.keys()):
                        commands_result[int(key)] = cmds[key]
                    commands_result_by_id = {}
                    for key in sorted(cmds.keys()):
                        commands_result_by_id[int(cmds[key]['id'])] = cmds[key]
                    routes[drone['id']] = {
                        'commands': commands_result_by_id,
                        'drone_id': route.drone.id,
                        'is_done': route.is_done,
                        'status': route.status,
                        'uid': route.uid
                    }
                    route = routes[drone['id']]
                drone['route'] = route

                drones_view.append(drone)
                js_params['copters'][drone['id']]['route'] = route
                i += 1
        js_params = json.dumps(js_params)
        drones = Drone.objects.filter().values()

        for drone in drones:
            drone['properties'] = History.objects.filter(drone_id=drone['id']).last()
        return render(request, 'control_pane/control.html',
                      {'show_head': 'N', 'COPTERS': drones_view, 'COPTERS_MULTIPLE': settings.COPTERS_MULTIPLE,
                       'WS_CONNECTION_STRING': settings.WS_CONNECTION_STRING, 'js_params': js_params})

def stream_list(request):
    streams = Stream.objects.order_by('title')
    DRONE_IP = settings.DRONE_IP
    DRONE_PORT = settings.DRONE_PORT
    VIDEO_PORT = settings.VIDEO_PORT
    return render(request, "control_pane/stream_list.html", {'streams': streams, 'DRONE_IP': DRONE_IP, 'DRONE_PORT':DRONE_PORT, 'VIDEO_PORT': VIDEO_PORT})


def stream(request, pk):
    stream_pk = Stream.objects.get(pk=pk)
    DRONE_IP = settings.DRONE_IP
    DRONE_PORT = settings.DRONE_PORT
    VIDEO_PORT = settings.VIDEO_PORT
    return render(request, "control_pane/stream.html", {'stream_pk': stream_pk, 'DRONE_IP': DRONE_IP, 'DRONE_PORT':DRONE_PORT, 'VIDEO_PORT': VIDEO_PORT})