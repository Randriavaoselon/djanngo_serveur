import cv2
import numpy as np
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import ClientInfo

class VideoStreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.client_id = self.scope['url_route']['kwargs']['client_id']
        await self.channel_layer.group_add(f"video_{self.client_id}", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(f"video_{self.client_id}", self.channel_name)

    async def send_video_frame(self, event):
        frame_data = event['frame']
        await self.send(bytes_data=frame_data)

def handle_client(conn, client_id):
    """
    Gère la réception et la diffusion des frames d'un client.
    """
    try:
        while True:
            # Lire la taille de la frame
            frame_size_data = conn.recv(4)
            if not frame_size_data:
                break
            frame_size = int.from_bytes(frame_size_data, 'big')

            # Lire les données de la frame
            frame_data = b""
            while len(frame_data) < frame_size:
                packet = conn.recv(frame_size - len(frame_data))
                if not packet:
                    break
                frame_data += packet

            # Décoder la frame
            frame = np.frombuffer(frame_data, dtype=np.uint8)
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

            if frame is not None:
                _, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()

                # Envoyer la frame via WebSocket
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"video_{client_id}",
                    {
                        "type": "send_video_frame",
                        "frame": frame_bytes,
                    }
                )
    finally:
        conn.close()
