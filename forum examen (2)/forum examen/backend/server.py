"""
Serveur Flask pour Forum de Discussion - EST Salé
API REST + WebSocket (Socket.IO)
"""

from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import bcrypt
from db_manager import DatabaseManager
import configparser
from datetime import datetime
import uuid

# Configuration
config = configparser.ConfigParser()
config.read('config.ini')

app = Flask(__name__)
app.config['SECRET_KEY'] = config['SERVER'].get('secret_key', 'votre_secret_key_ici')
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

# Gestionnaire de base de données
db_manager = DatabaseManager()

# Dictionnaire pour stocker les utilisateurs connectés
# Format: {username: {'sid': socket_id, 'pseudo': pseudo}}
connected_users = {}

# ========================================
# ROUTES D'AUTHENTIFICATION
# ========================================

@app.route('/register', methods=['POST'])
def register():
    """
    Inscription d'un nouvel étudiant
    Body: {nom, prenom, pseudo, username, password}
    """
    try:
        data = request.json
        nom = data.get('nom')
        prenom = data.get('prenom')
        pseudo = data.get('pseudo')
        username = data.get('username')
        password = data.get('password')
        
        # Validation
        if not all([nom, prenom, pseudo, username, password]):
            return jsonify({"error": "Tous les champs sont requis"}), 400
        
        # Vérifier si l'utilisateur existe déjà
        if db_manager.get_user_by_username(username):
            return jsonify({"error": "Ce username existe déjà"}), 409
        
        # Hash du mot de passe
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Ajouter l'utilisateur (compte INACTIF par défaut)
        user_id = db_manager.add_user(
            nom, prenom, pseudo, username, 
            hashed_password.decode('utf-8')
        )
        
        if user_id:
            return jsonify({
                "message": "Inscription réussie. Votre compte sera activé par un administrateur.",
                "user_id": user_id,
                "status": "INACTIF"
            }), 201
        else:
            return jsonify({"error": "Erreur lors de l'inscription"}), 500
            
    except Exception as e:
        print(f"Erreur dans /register: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    """
    Connexion d'un étudiant
    Body: {username, password}
    """
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        
        if not username or not password:
            return jsonify({"error": "Username et password requis"}), 400
        
        # Récupérer l'utilisateur
        user = db_manager.get_user_by_username(username)
        
        if not user:
            return jsonify({"error": "Identifiants incorrects"}), 401
        
        # Vérifier le mot de passe
        if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return jsonify({"error": "Identifiants incorrects"}), 401
        
        # Vérifier si le compte est actif
        if not user['compte_actif']:
            return jsonify({
                "error": "Votre compte n'est pas encore activé. Veuillez contacter l'administrateur.",
                "status": "INACTIF"
            }), 403
        
        # Créer une session
        session_id = str(uuid.uuid4())
        session['user_id'] = user['id']
        session['username'] = username
        session['session_id'] = session_id
        
        # Enregistrer la connexion
        db_manager.log_login(
            user['id'], username, user['pseudo'], 
            'LOGIN', ip_address, user_agent, session_id
        )
        
        return jsonify({
            "message": "Connexion réussie",
            "user": {
                "id": user['id'],
                "username": user['username'],
                "pseudo": user['pseudo'],
                "nom": user['nom'],
                "prenom": user['prenom'],
                "compte_approuve": user['compte_approuve']
            },
            "session_id": session_id
        }), 200
        
    except Exception as e:
        print(f"Erreur dans /login: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/logout', methods=['POST'])
def logout():
    """Déconnexion d'un utilisateur"""
    try:
        username = session.get('username')
        if username:
            user = db_manager.get_user_by_username(username)
            if user:
                db_manager.log_login(
                    user['id'], username, user['pseudo'], 
                    'LOGOUT', request.remote_addr, 
                    request.headers.get('User-Agent'),
                    session.get('session_id')
                )
        
        session.clear()
        return jsonify({"message": "Déconnexion réussie"}), 200
        
    except Exception as e:
        print(f"Erreur dans /logout: {e}")
        return jsonify({"error": str(e)}), 500

# ========================================
# ROUTES DES MESSAGES
# ========================================

@app.route('/messages', methods=['GET'])
def get_messages():
    """Récupère tous les messages validés"""
    try:
        limit = request.args.get('limit', 100, type=int)
        messages = db_manager.get_messages(limit)
        
        # Formater les dates
        for msg in messages:
            if msg.get('date_envoi'):
                msg['date_envoi'] = msg['date_envoi'].isoformat()
            if msg.get('date_validation'):
                msg['date_validation'] = msg['date_validation'].isoformat()
        
        return jsonify(messages), 200
        
    except Exception as e:
        print(f"Erreur dans /messages: {e}")
        return jsonify({"error": str(e)}), 500

# ========================================
# ROUTES D'ADMINISTRATION
# ========================================

@app.route('/admin/login', methods=['POST'])
def admin_login():
    """Connexion administrateur"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "Identifiants requis"}), 400
        
        admin = db_manager.get_admin_by_username(username)
        
        if not admin:
            return jsonify({"error": "Identifiants incorrects"}), 401
        
        if not bcrypt.checkpw(password.encode('utf-8'), admin['password'].encode('utf-8')):
            return jsonify({"error": "Identifiants incorrects"}), 401
        
        session['admin_id'] = admin['id']
        session['admin_username'] = username
        session['is_admin'] = True
        
        return jsonify({
            "message": "Connexion admin réussie",
            "admin": {
                "id": admin['id'],
                "username": admin['username'],
                "nom": admin['nom'],
                "prenom": admin['prenom']
            }
        }), 200
        
    except Exception as e:
        print(f"Erreur dans /admin/login: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/admin/stats', methods=['GET'])
def get_admin_stats():
    """Récupère les statistiques pour l'admin"""
    try:
        stats = db_manager.get_stats()
        return jsonify(stats), 200
    except Exception as e:
        print(f"Erreur dans /admin/stats: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/admin/pending_accounts', methods=['GET'])
def get_pending_accounts():
    """Récupère les comptes en attente d'activation"""
    try:
        accounts = db_manager.get_inactive_accounts()
        
        # Formater les dates
        for acc in accounts:
            if acc.get('date_inscription'):
                acc['date_inscription'] = acc['date_inscription'].isoformat()
        
        return jsonify(accounts), 200
        
    except Exception as e:
        print(f"Erreur dans /admin/pending_accounts: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/admin/unapproved_accounts', methods=['GET'])
def get_unapproved_accounts():
    """Récupère les comptes actifs mais non approuvés"""
    try:
        accounts = db_manager.get_active_not_approved_accounts()
        
        for acc in accounts:
            if acc.get('date_inscription'):
                acc['date_inscription'] = acc['date_inscription'].isoformat()
        
        return jsonify(accounts), 200
        
    except Exception as e:
        print(f"Erreur: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/admin/activate', methods=['POST'])
def activate_account():
    """
    Active un compte étudiant (étape 1)
    Body: {username}
    """
    try:
        data = request.json
        username = data.get('username')
        
        if not username:
            return jsonify({"error": "Username requis"}), 400
        
        if db_manager.activate_user(username):
            return jsonify({
                "message": f"Compte {username} activé. L'étudiant peut se connecter mais ses messages nécessitent validation."
            }), 200
        else:
            return jsonify({"error": "Erreur lors de l'activation"}), 500
            
    except Exception as e:
        print(f"Erreur dans /admin/activate: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/admin/approve', methods=['POST'])
def approve_account():
    """
    Approuve définitivement un compte (étape 2)
    Les messages de cet utilisateur seront distribués automatiquement
    Body: {username}
    """
    try:
        data = request.json
        username = data.get('username')
        
        if not username:
            return jsonify({"error": "Username requis"}), 400
        
        user = db_manager.get_user_by_username(username)
        if not user:
            return jsonify({"error": "Utilisateur non trouvé"}), 404
        
        if not user['compte_actif']:
            return jsonify({"error": "Le compte doit d'abord être activé"}), 400
        
        if db_manager.approve_user(username):
            return jsonify({
                "message": f"Compte {username} approuvé définitivement. Messages distribués automatiquement."
            }), 200
        else:
            return jsonify({"error": "Erreur lors de l'approbation"}), 500
            
    except Exception as e:
        print(f"Erreur dans /admin/approve: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/admin/pending_messages', methods=['GET'])
def get_pending_messages():
    """Récupère tous les messages en attente de validation"""
    try:
        messages = db_manager.get_pending_messages()
        
        # Formater les dates
        for msg in messages:
            if msg.get('date_envoi'):
                msg['date_envoi'] = msg['date_envoi'].isoformat()
        
        return jsonify(messages), 200
        
    except Exception as e:
        print(f"Erreur dans /admin/pending_messages: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/admin/validate_message', methods=['POST'])
def validate_message():
    """
    Valide un message (permet sa distribution)
    Body: {message_id}
    """
    try:
        data = request.json
        message_id = data.get('message_id')
        admin_id = session.get('admin_id', 1)  # ID de l'admin
        
        if not message_id:
            return jsonify({"error": "message_id requis"}), 400
        
        # Valider le message
        if db_manager.validate_message(message_id, admin_id):
            # Récupérer le message validé
            message = db_manager.get_message_by_id(message_id)
            
            if message:
                # Diffuser le message via WebSocket
                socketio.emit('new_message', {
                    'id': message['id'],
                    'from': message['pseudo_expediteur'],
                    'from_id': message['id_expediteur'],
                    'to': message['pseudo_destinataire'],
                    'to_id': message['id_destinataire'],
                    'content': message['contenu'],
                    'timestamp': message['date_envoi'].isoformat(),
                    'is_private': message['est_prive']
                }, broadcast=True)
            
            return jsonify({"message": "Message validé et distribué"}), 200
        else:
            return jsonify({"error": "Erreur lors de la validation"}), 500
            
    except Exception as e:
        print(f"Erreur dans /admin/validate_message: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/admin/reject_message', methods=['POST'])
def reject_message():
    """
    Rejette un message (supprime)
    Body: {message_id}
    """
    try:
        data = request.json
        message_id = data.get('message_id')
        
        if not message_id:
            return jsonify({"error": "message_id requis"}), 400
        
        if db_manager.reject_message(message_id):
            return jsonify({"message": "Message rejeté"}), 200
        else:
            return jsonify({"error": "Erreur lors du rejet"}), 500
            
    except Exception as e:
        print(f"Erreur dans /admin/reject_message: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/admin/users', methods=['GET'])
def get_all_users():
    """Récupère tous les utilisateurs actifs"""
    try:
        users = db_manager.get_all_active_users()
        
        for user in users:
            if user.get('date_inscription'):
                user['date_inscription'] = user['date_inscription'].isoformat()
        
        return jsonify(users), 200
        
    except Exception as e:
        print(f"Erreur: {e}")
        return jsonify({"error": str(e)}), 500

# ========================================
# WEBSOCKET (SOCKET.IO)
# ========================================

@socketio.on('connect')
def handle_connect():
    """Gestion de la connexion WebSocket"""
    print(f" Client connecté: {request.sid}")
    emit('connected', {'message': 'Connecté au serveur'})

@socketio.on('disconnect')
def handle_disconnect():
    """Gestion de la déconnexion WebSocket"""
    print(f" Client déconnecté: {request.sid}")
    
    # Retirer l'utilisateur de la liste des connectés
    for username, info in list(connected_users.items()):
        if info['sid'] == request.sid:
            del connected_users[username]
            # Notifier les autres utilisateurs
            socketio.emit('user_disconnected', {
                'username': username,
                'pseudo': info['pseudo']
            }, broadcast=True)
            break

@socketio.on('user_connected')
def handle_user_connected(data):
    """Notification qu'un utilisateur s'est connecté au chat"""
    username = data.get('username')
    pseudo = data.get('pseudo')
    
    if username and pseudo:
        connected_users[username] = {
            'sid': request.sid,
            'pseudo': pseudo
        }
        
        # Notifier tous les clients
        socketio.emit('user_connected', {
            'username': username,
            'pseudo': pseudo,
            'connected_users': [{'username': u, 'pseudo': i['pseudo']} 
                               for u, i in connected_users.items()]
        }, broadcast=True)
        
        print(f" {pseudo} rejoint le chat")

@socketio.on('send_message')
def handle_send_message(data):
    """
    Réception et traitement d'un message
    Data: {
        username, pseudo, content, 
        to_username (optionnel), to_pseudo (optionnel)
    }
    """
    try:
        username = data.get('username')
        pseudo = data.get('pseudo')
        content = data.get('content')
        to_username = data.get('to_username')  # None pour message public
        to_pseudo = data.get('to_pseudo')
        
        if not all([username, pseudo, content]):
            emit('error', {'message': 'Données incomplètes'})
            return
        
        # Récupérer l'utilisateur
        user = db_manager.get_user_by_username(username)
        if not user:
            emit('error', {'message': 'Utilisateur non trouvé'})
            return
        
        # Déterminer si le message est privé
        est_prive = to_username is not None
        
        # Récupérer l'ID du destinataire si privé
        id_destinataire = None
        if est_prive and to_username:
            dest_user = db_manager.get_user_by_username(to_username)
            if dest_user:
                id_destinataire = dest_user['id']
        
        # Vérifier si l'utilisateur est approuvé
        auto_validate = user['compte_approuve']
        
        # Sauvegarder le message
        message_id = db_manager.add_message(
            id_expediteur=user['id'],
            pseudo_expediteur=pseudo,
            id_destinataire=id_destinataire,
            pseudo_destinataire=to_pseudo,
            contenu=content,
            est_prive=est_prive,
            auto_validate=auto_validate
        )
        
        if message_id:
            message_data = {
                'id': message_id,
                'from': pseudo,
                'from_id': user['id'],
                'to': to_pseudo,
                'to_id': id_destinataire,
                'content': content,
                'timestamp': datetime.now().isoformat(),
                'is_private': est_prive
            }
            
            if auto_validate:
                # Distribution immédiate (utilisateur approuvé)
                if est_prive:
                    # Message privé - envoyer seulement à l'expéditeur et au destinataire
                    emit('new_message', message_data, room=request.sid)
                    if to_username in connected_users:
                        emit('new_message', message_data, 
                             room=connected_users[to_username]['sid'])
                else:
                    # Message public - broadcast à tous
                    emit('new_message', message_data, broadcast=True)
                
                print(f" Message de {pseudo} distribué automatiquement")
            else:
                # En attente de validation (utilisateur non approuvé)
                # Notifier l'expéditeur
                emit('message_pending_validation', {
                    'message': 'Votre message est en attente de validation par un administrateur.'
                }, room=request.sid)
                
                # Notifier les admins via une room spéciale
                emit('admin_notification', {
                    'type': 'new_pending_message',
                    'message': message_data
                }, room='admin')
                
                print(f"⏳ Message de {pseudo} en attente de validation")
        
    except Exception as e:
        print(f"Erreur dans send_message: {e}")
        emit('error', {'message': str(e)})

@socketio.on('join_admin_room')
def handle_join_admin():
    """Admin rejoint la room pour recevoir les notifications"""
    join_room('admin')
    print(" Admin a rejoint la room admin")

@socketio.on('leave_admin_room')
def handle_leave_admin():
    """Admin quitte la room"""
    leave_room('admin')
    print(" Admin a quitté la room admin")

# ========================================
# LANCEMENT DU SERVEUR
# ========================================

# Servir les fichiers statiques du frontend
@app.route('/')
def index():
    """Page d'accueil - redirige vers le frontend"""
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Servir les fichiers statiques (HTML, CSS, JS)"""
    return send_from_directory('../frontend', filename)

if __name__ == '__main__':
    host = config['SERVER'].get('host', '127.0.0.1')
    port = int(config['SERVER'].get('port', 5000))
    debug = config['SERVER'].getboolean('debug', True)
    
    print(f"""
    ╔════════════════════════════════════════╗
    ║  Forum de Discussion - EST Salé        ║
    ║  Serveur Flask + Socket.IO             ║
    ╚════════════════════════════════════════╝
    
     Serveur démarré sur http://{host}:{port}
     Mode debug: {debug}
    """)
    
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)

