# Forum Étudiant en Temps Réel

Ce projet est une plateforme d'entraide entre étudiants.

## Technologies utilisées
* **Backend** : FastAPI (Python) - Port 8000
* **Base de données** : MariaDB / MySQL - Port 3306
* **Temps réel** : Socket.IO / WebSockets
* **Documentation** : Swagger UI (générée automatiquement par FastAPI)

## Installation
1. Lancer la base de données MariaDB
2. `pip install fastapi uvicorn python-socketio`
3. `uvicorn main:app --reload`
