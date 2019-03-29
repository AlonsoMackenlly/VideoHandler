import tornado.web
from django.conf import settings

# if settings.COPTERS_MULTIPLE == True:
#     from control_pane.lib.DroneModules.DroneHub import DroneHub
# else:
from control_pane.lib.DroneModules.DroneDirect import DroneDirect

# if settings.COPTERS_MULTIPLE == True:
#     application = tornado.web.Application([
#         (r'/', DroneHub),
#     ])
# else:
application = tornado.web.Application([
    (r'/', DroneDirect),
])