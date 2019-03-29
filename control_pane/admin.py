from django.contrib import admin
from .models import Event, History, Drone, DronePlane, Route, DroneCommand, ExchangeObject, Stream

admin.site.register(Event)
admin.site.register(History)
admin.site.register(Drone)
admin.site.register(Stream)
admin.site.register(DronePlane)
admin.site.register(DroneCommand)
admin.site.register(Route)
admin.site.register(ExchangeObject)





