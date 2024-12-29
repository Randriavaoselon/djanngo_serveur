from rest_framework import serializers
from .models import Client

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['client_name', 'client_ip', 'frame', 'mouse_x', 'mouse_y', 'timestamp']