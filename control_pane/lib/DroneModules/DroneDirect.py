import tornado.websocket
import tornado.ioloop
from django.conf import settings
from django.contrib.auth.models import User
from control_pane.models import History
from control_pane.lib.DroneModules.DroneDirectConnection import _Drone
from control_pane.lib.DroneModules.DroneDirectMessages import DroneDirectMessages
from importlib import import_module
import inspect
import logging as file_logger
from threading import  Thread
from control_pane.lib.DroneModules.DataService import log
session_engine = import_module(settings.SESSION_ENGINE)
file_logger = file_logger.getLogger(__name__)
drone = _Drone()

# def function_logger(file_level, console_level=None):
#     function_name = inspect.stack()[1][3]
#     logger = logging.getLogger(function_name)
#     logger.setLevel(logging.DEBUG)  # By default, logs all messages
#
#     if console_level != None:
#         ch = logging.StreamHandler()  # StreamHandler logs to console
#         ch.setLevel(console_level)
#         ch_format = logging.Formatter('%(asctime)s - %(message)s')
#         ch.setFormatter(ch_format)
#         logger.addHandler(ch)
#
#         fh = logging.FileHandler("/root/django_drone/hub.log".format(function_name))
#         fh.setLevel(file_level)
#         fh_format = logging.Formatter('%(asctime)s - %(lineno)d - %(levelname)-8s - %(message)s')
#         fh.setFormatter(fh_format)
#         logger.addHandler(fh)
#
#     return logger
#
# file_logger = function_logger(logging.INFO)
class ClientConnection(object):
    def __init__(self, session, connection):
        self.session = session
        self.connection = connection


class DroneDirect(tornado.websocket.WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super(DroneDirect, self).__init__(*args, **kwargs)
        try:
            self.connections = []
            log("created DroneDirect!")
        except Exception as e:
            log(e)
    def open(self):
        global drone
        self.drone = drone
        # log("open connection")
        # session_key = self.get_cookie(settings.SESSION_COOKIE_NAME)
        # session = session_engine.SessionStore(session_key)
        # self.connections.append(ClientConnection(session, self))
        self.drone.connection = self

    def handle_request(self, response):
        log(response)

    def on_message(self, message):
        try:
            DroneDirectMessages.handle(self, message)
        except Exception as e:
            log(e)
    def check_origin(self, origin):
        # log(origin)
        return True
    def on_error(self, error):
        self.drone.connection = None
        self.connections = []
        log('connection error = ' + str(error))

    def on_close(self):
        self.drone.connection = None
        self.connections = []
        log('connection closed')
