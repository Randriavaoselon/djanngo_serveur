#!/bin/bash

# Démarrer le serveur Django
echo "Démarrage du serveur Django..."
(cd ../PR1 && python3.13 manage.py runserver) &

# Démarrer le serveur React
echo "Démarrage du serveur React..."
npm start
