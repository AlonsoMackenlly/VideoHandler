from django import template
from control_pane.models import History, Route, Drone, DroneCommand
register = template.Library()

@register.simple_tag
def get_point_uid(coordinates, i):
    return coordinates[i]['uid']
@register.simple_tag
def get_point_status(coordinates, i):
    return coordinates[i]['status']