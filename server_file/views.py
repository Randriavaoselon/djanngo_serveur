import socket
import threading
import os
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Variable globale pour stocker la connexion du client
client_socket = None
file_list = []  # Liste des fichiers et dossiers à afficher

# Fonction pour gérer le serveur socket
def socket_server():
    global client_socket, file_list
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", 5000))
    server_socket.listen(5)

    while True:
        try:
            client_socket, addr = server_socket.accept()
            print(f"Client connecté depuis {addr}")
            # Envoi immédiat de la liste des répertoires dès que le client se connecte
            response = list_directory("C:\\")  # Remplacez par le répertoire souhaité
            client_socket.send(response.encode('utf-8'))
            while True:
                command = client_socket.recv(1024).decode('utf-8')
                if command.startswith("LIST"):
                    # Envoie de la liste des fichiers et dossiers
                    response = list_directory("C:\\")  # Remplacez par le répertoire souhaité
                    client_socket.send(response.encode('utf-8'))
                elif command.startswith("CHANGE_DIR"):
                    # Changer de répertoire
                    new_dir = command.split(" ", 1)[1]
                    client_socket.send(f"CHANGED_TO:{new_dir}".encode('utf-8'))
                elif command.startswith("DOWNLOAD"):
                    # Télécharger un fichier
                    file_name = command.split(" ", 1)[1]
                    file_path = os.path.join("C:\\Server_Files", file_name)  # Répertoire de destination sur le serveur
                    if os.path.exists(file_path) and os.path.isfile(file_path):
                        client_socket.send("READY".encode('utf-8'))
                        save_file(client_socket, file_path)
                    else:
                        client_socket.send("ERROR: File not found".encode('utf-8'))
                elif command == "DISCONNECT":
                    print("Client déconnecté.")
                    break
        except Exception as e:
            print(f"Erreur de connexion : {str(e)}")
            break

# Démarrer le serveur socket dans un thread séparé
def start_socket_server():
    thread = threading.Thread(target=socket_server)
    thread.daemon = True
    thread.start()

# Démarrer le serveur socket
start_socket_server()

# Fonction pour lister les fichiers d'un répertoire
def list_directory(directory):
    """Retourne la liste des fichiers et dossiers (y compris cachés) dans un répertoire donné."""
    try:
        items = os.listdir(directory)
        result = []
        for item in items:
            path = os.path.join(directory, item)
            if os.path.isdir(path):
                result.append(f"[DIR] {item}")
            else:
                result.append(f"[FILE] {item}")
        return "\n".join(result)
    except Exception as e:
        return f"ERROR: {str(e)}"

def save_file(client_socket, file_path):
    """Enregistre un fichier envoyé par le client."""
    try:
        with open(file_path, "wb") as f:
            while True:
                data = client_socket.recv(1024)
                if data == b"END_OF_FILE":
                    break
                f.write(data)
        print(f"Fichier reçu et sauvegardé sous {file_path}")
    except Exception as e:
        print(f"Erreur lors de la réception du fichier : {e}")

# Vue Django pour obtenir la liste des fichiers
@csrf_exempt
def get_file_list(request):
    global file_list
    if client_socket:
        client_socket.send("LIST".encode('utf-8'))
        data = client_socket.recv(4096).decode('utf-8')
        file_list = data.split("\n")
        return JsonResponse({'file_list': file_list})
    return JsonResponse({'error': 'No client connected'}, status=400)

# Vue Django pour changer de répertoire
@csrf_exempt
def change_directory(request):
    folder_name = request.POST.get('folder_name', '')
    if client_socket:
        client_socket.send(f"CHANGE_DIR {folder_name}".encode('utf-8'))
        response = client_socket.recv(1024).decode('utf-8')
        return JsonResponse({'response': response})
    return JsonResponse({'error': 'No client connected'}, status=400)




# import socket
# import threading
# import os
# from django.shortcuts import render
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt

# # Variable globale pour stocker la connexion du client
# client_socket = None
# file_list = []  # Liste des fichiers et dossiers à afficher

# # Fonction pour gérer le serveur socket
# def socket_server():
#     global client_socket, file_list
#     server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     server_socket.bind(("0.0.0.0", 5000))
#     server_socket.listen(5)

#     while True:
#         try:
#             client_socket, addr = server_socket.accept()
#             print(f"Client connecté depuis {addr}")
#             while True:
#                 command = client_socket.recv(1024).decode('utf-8')
#                 if command.startswith("LIST"):
#                     # Envoie de la liste des fichiers et dossiers
#                     response = list_directory("C:\\")  # Remplacez par le répertoire souhaité
#                     client_socket.send(response.encode('utf-8'))
#                 elif command.startswith("CHANGE_DIR"):
#                     # Changer de répertoire
#                     new_dir = command.split(" ", 1)[1]
#                     client_socket.send(f"CHANGED_TO:{new_dir}".encode('utf-8'))
#                 elif command.startswith("DOWNLOAD"):
#                     # Télécharger un fichier
#                     file_name = command.split(" ", 1)[1]
#                     file_path = os.path.join("C:\\Server_Files", file_name)  # Répertoire de destination sur le serveur
#                     if os.path.exists(file_path) and os.path.isfile(file_path):
#                         client_socket.send("READY".encode('utf-8'))
#                         save_file(client_socket, file_path)
#                     else:
#                         client_socket.send("ERROR: File not found".encode('utf-8'))
#                 elif command == "DISCONNECT":
#                     print("Client déconnecté.")
#                     break
#         except Exception as e:
#             print(f"Erreur de connexion : {str(e)}")
#             break

# # Démarrer le serveur socket dans un thread séparé
# def start_socket_server():
#     thread = threading.Thread(target=socket_server)
#     thread.daemon = True
#     thread.start()

# # Démarrer le serveur socket
# start_socket_server()

# # Fonction pour lister les fichiers d'un répertoire
# def list_directory(directory):
#     """Retourne la liste des fichiers et dossiers (y compris cachés) dans un répertoire donné."""
#     try:
#         items = os.listdir(directory)
#         result = []
#         for item in items:
#             path = os.path.join(directory, item)
#             if os.path.isdir(path):
#                 result.append(f"[DIR] {item}")
#             else:
#                 result.append(f"[FILE] {item}")
#         return "\n".join(result)
#     except Exception as e:
#         return f"ERROR: {str(e)}"

# def save_file(client_socket, file_path):
#     """Enregistre un fichier envoyé par le client."""
#     try:
#         with open(file_path, "wb") as f:
#             while True:
#                 data = client_socket.recv(1024)
#                 if data == b"END_OF_FILE":
#                     break
#                 f.write(data)
#         print(f"Fichier reçu et sauvegardé sous {file_path}")
#     except Exception as e:
#         print(f"Erreur lors de la réception du fichier : {e}")

# # Vue Django pour obtenir la liste des fichiers
# @csrf_exempt
# def get_file_list(request):
#     global file_list
#     if client_socket:
#         client_socket.send("LIST".encode('utf-8'))
#         data = client_socket.recv(4096).decode('utf-8')
#         file_list = data.split("\n")
#         return JsonResponse({'file_list': file_list})
#     return JsonResponse({'error': 'No client connected'}, status=400)

# # Vue Django pour changer de répertoire
# @csrf_exempt
# def change_directory(request):
#     folder_name = request.POST.get('folder_name', '')
#     if client_socket:
#         client_socket.send(f"CHANGE_DIR {folder_name}".encode('utf-8'))
#         response = client_socket.recv(1024).decode('utf-8')
#         return JsonResponse({'response': response})
#     return JsonResponse({'error': 'No client connected'}, status=400)




# import socket
# import threading
# from django.shortcuts import render
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt

# # Variable globale pour stocker la connexion du client
# client_socket = None
# file_list = []  # Liste des fichiers et dossiers à afficher

# # Fonction pour gérer le serveur socket
# def socket_server():
#     global client_socket, file_list
#     server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     server_socket.bind(("0.0.0.0", 5000))
#     server_socket.listen(5)

#     while True:
#         try:
#             client_socket, addr = server_socket.accept()
#             print(f"Client connecté depuis {addr}")
#             while True:
#                 command = client_socket.recv(1024).decode('utf-8')
#                 if command.startswith("LIST"):
#                     # Envoie de la liste des fichiers et dossiers
#                     response = list_directory("C:\\")  # Remplacez par le répertoire souhaité
#                     client_socket.send(response.encode('utf-8'))
#                 elif command.startswith("CHANGE_DIR"):
#                     # Changer de répertoire
#                     new_dir = command.split(" ", 1)[1]
#                     # Logique pour changer de répertoire ici (mettre à jour le chemin et renvoyer)
#                     client_socket.send(f"CHANGED_TO:{new_dir}".encode('utf-8'))
#                 elif command == "DISCONNECT":
#                     print("Client déconnecté.")
#                     break
#         except Exception as e:
#             print(f"Erreur de connexion : {str(e)}")
#             break

# # Démarrer le serveur socket dans un thread séparé
# def start_socket_server():
#     thread = threading.Thread(target=socket_server)
#     thread.daemon = True
#     thread.start()

# # Démarrer le serveur socket
# start_socket_server()

# # Fonction pour lister les fichiers d'un répertoire
# def list_directory(directory):
#     """Retourne la liste des fichiers et dossiers (y compris cachés) dans un répertoire donné."""
#     try:
#         items = os.listdir(directory)
#         result = []
#         for item in items:
#             path = os.path.join(directory, item)
#             if os.path.isdir(path):
#                 result.append(f"[DIR] {item}")
#             else:
#                 result.append(f"[FILE] {item}")
#         return "\n".join(result)
#     except Exception as e:
#         return f"ERROR: {str(e)}"

# # Vue Django pour obtenir la liste des fichiers
# @csrf_exempt
# def get_file_list(request):
#     global file_list
#     if client_socket:
#         client_socket.send("LIST".encode('utf-8'))
#         data = client_socket.recv(4096).decode('utf-8')
#         file_list = data.split("\n")
#         return JsonResponse({'file_list': file_list})
#     return JsonResponse({'error': 'No client connected'}, status=400)

# # Vue Django pour changer de répertoire
# @csrf_exempt
# def change_directory(request):
#     folder_name = request.POST.get('folder_name', '')
#     if client_socket:
#         client_socket.send(f"CHANGE_DIR {folder_name}".encode('utf-8'))
#         response = client_socket.recv(1024).decode('utf-8')
#         return JsonResponse({'response': response})
#     return JsonResponse({'error': 'No client connected'}, status=400)

