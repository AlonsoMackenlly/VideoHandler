import tornado.websocket
import tornado.ioloop
import logging as file_logger
import inspect
from django.conf import settings
from django.contrib.auth.models import User

from control_pane.lib.DroneModules.DroneWsConnection import  _Drone
from control_pane.lib.DroneModules.DroneHubMessages import DroneHubMessages

from importlib import import_module
session_engine = import_module(settings.SESSION_ENGINE)
drones = _Drone.init()

class ClientConnection(object):
    def __init__(self, session):
        self.session = session

class DroneHub(tornado.websocket.WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super(DroneHub, self).__init__(*args, **kwargs)
        global drones
        file_logger.info("HUB CREATING")
        self.drones = drones
        self.connections = []
    def open(self):
        session_key = self.get_cookie(settings.SESSION_COOKIE_NAME)
        session = session_engine.SessionStore(session_key)
        self.connections.append(ClientConnection(session))

    def handle_request(self, response):
        pass

    def on_message(self, message):
        try:
            file_logger.info(message['type'])
            DroneHubMessages.handle(self, message)
        except Exception as e:
            file_logger.info("************************* Error *************************")
            file_logger.info(e)
            file_logger.info("************************* Error *************************")

    def check_origin(self, origin):
        # file_logger.info.info(origin)
        return True