from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^control/$', views.control, name='control'),
    url(r'^delete/$', views.deleteData, name='deleteData'),
    url(r'^streams$', views.stream_list, name='stream_list'),
    url(r'^stream/(?P<pk>\d+)/$', views.stream, name='stream'),

    # url(r'^contact/$', views.contact, name='contact'),
]