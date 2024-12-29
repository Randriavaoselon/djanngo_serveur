from django.urls import re_path
from .consumers import VideoStreamConsumer

websocket_urlpatterns = [
    re_path(r'ws/video/(?P<client_id>\w+)/$', VideoStreamConsumer.as_asgi()),
]
