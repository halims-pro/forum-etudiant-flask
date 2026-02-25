"""
Database Manager pour Forum Chat
Gestion de toutes les opérations sur la base de données MySQL
"""

import mysql.connector
from mysql.connector import Error
from datetime import datetime
import configparser

class DatabaseManager:
    def __init__(self, config_file='config.ini'):
        """Initialise la connexion à la base de données"""
        config = configparser.ConfigParser()
        config.read(config_file)
        
        try:
            self.connection = mysql.connector.connect(
                host=config['DATABASE']['host'],
                user=config['DATABASE']['user'],
                password=config['DATABASE']['password'],
                database=config['DATABASE']['database']
            )
            if self.connection.is_connected():
                print("Connexion à MySQL réussie")
        except Error as e:
            print(f" Erreur de connexion à MySQL: {e}")
            raise
    
    def __del__(self):
        """Ferme la connexion à la base de données"""
        if hasattr(self, 'connection') and self.connection.is_connected():
            self.connection.close()
            print("Connexion MySQL fermée")
    
    # ========================================
    # GESTION DES ÉTUDIANTS
    # ========================================
    
    def add_user(self, nom, prenom, pseudo, username, password):
        """
        Ajoute un nouvel étudiant (compte INACTIF et NON APPROUVÉ par défaut)
        
        Args:
            nom (str): Nom de famille
            prenom (str): Prénom
            pseudo (str): Pseudo unique
            username (str): Username unique
            password (str): Mot de passe hashé (bcrypt)
            
        Returns:
            int: ID de l'utilisateur créé, ou None si erreur
        """
        try:
            cursor = self.connection.cursor()
            query = """
                INSERT INTO etudiant (nom, prenom, pseudo, username, password, 
                                     compte_actif, compte_approuve) 
                VALUES (%s, %s, %s, %s, %s, FALSE, FALSE)
            """
            cursor.execute(query, (nom, prenom, pseudo, username, password))
            self.connection.commit()
            user_id = cursor.lastrowid
            print(f"Utilisateur {username} créé (ID: {user_id})")
            return user_id
        except Error as e:
            print(f" Erreur lors de l'ajout de l'utilisateur: {e}")
            return None
        finally:
            cursor.close()
    
    def get_user_by_username(self, username):
        """
        Récupère un utilisateur par son username
        
        Args:
            username (str): Username à rechercher
            
        Returns:
            dict: Informations de l'utilisateur, ou None si non trouvé
        """
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM etudiant WHERE username = %s"
            cursor.execute(query, (username,))
            user = cursor.fetchone()
            return user
        except Error as e:
            print(f" Erreur lors de la récupération de l'utilisateur: {e}")
            return None
        finally:
            cursor.close()
    
    def get_user_by_id(self, user_id):
        """Récupère un utilisateur par son ID"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM etudiant WHERE id = %s"
            cursor.execute(query, (user_id,))
            return cursor.fetchone()
        except Error as e:
            print(f" Erreur: {e}")
            return None
        finally:
            cursor.close()
    
    def activate_user(self, username):
        """
        Active un compte étudiant (compte_actif = TRUE)
        Le compte peut maintenant se connecter mais ses messages 
        nécessitent toujours une validation
        
        Args:
            username (str): Username à activer
            
        Returns:
            bool: True si succès, False sinon
        """
        try:
            cursor = self.connection.cursor()
            query = "UPDATE etudiant SET compte_actif = TRUE WHERE username = %s"
            cursor.execute(query, (username,))
            self.connection.commit()
            print(f"Compte {username} activé")
            return True
        except Error as e:
            print(f" Erreur lors de l'activation: {e}")
            return False
        finally:
            cursor.close()
    
    def approve_user(self, username):
        """
        Approuve définitivement un compte (compte_approuve = TRUE)
        Les messages de cet utilisateur seront distribués automatiquement
        sans validation
        
        Args:
            username (str): Username à approuver
            
        Returns:
            bool: True si succès, False sinon
        """
        try:
            cursor = self.connection.cursor()
            query = "UPDATE etudiant SET compte_approuve = TRUE WHERE username = %s"
            cursor.execute(query, (username,))
            self.connection.commit()
            print(f"Compte {username} approuvé définitivement")
            return True
        except Error as e:
            print(f" Erreur lors de l'approbation: {e}")
            return False
        finally:
            cursor.close()
    
    def get_inactive_accounts(self):
        """Récupère tous les comptes inactifs en attente d'activation"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT id, nom, prenom, pseudo, username, date_inscription 
                FROM etudiant 
                WHERE compte_actif = FALSE 
                ORDER BY date_inscription DESC
            """
            cursor.execute(query)
            return cursor.fetchall()
        except Error as e:
            print(f" Erreur: {e}")
            return []
        finally:
            cursor.close()
    
    def get_active_not_approved_accounts(self):
        """Récupère les comptes actifs mais non approuvés"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT id, nom, prenom, pseudo, username, date_inscription 
                FROM etudiant 
                WHERE compte_actif = TRUE AND compte_approuve = FALSE 
                ORDER BY date_inscription DESC
            """
            cursor.execute(query)
            return cursor.fetchall()
        except Error as e:
            print(f" Erreur: {e}")
            return []
        finally:
            cursor.close()
    
    def get_all_active_users(self):
        """Récupère tous les utilisateurs actifs avec leur statut"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT id, nom, prenom, pseudo, username, 
                       compte_actif, compte_approuve, date_inscription 
                FROM etudiant 
                WHERE compte_actif = TRUE 
                ORDER BY pseudo ASC
            """
            cursor.execute(query)
            return cursor.fetchall()
        except Error as e:
            print(f" Erreur: {e}")
            return []
        finally:
            cursor.close()
    
    # ========================================
    # GESTION DES MESSAGES
    # ========================================
    
    def add_message(self, id_expediteur, pseudo_expediteur, id_destinataire, 
                   pseudo_destinataire, contenu, est_prive=False, 
                   auto_validate=False):
        """
        Ajoute un message dans la base de données
        
        Args:
            id_expediteur (int): ID de l'expéditeur
            pseudo_expediteur (str): Pseudo de l'expéditeur
            id_destinataire (int): ID du destinataire (None pour message public)
            pseudo_destinataire (str): Pseudo du destinataire (None pour public)
            contenu (str): Contenu du message
            est_prive (bool): Message privé ou public
            auto_validate (bool): Si True, valide automatiquement le message
            
        Returns:
            int: ID du message créé
        """
        try:
            cursor = self.connection.cursor()
            query = """
                INSERT INTO message (id_expediteur, pseudo_expediteur, 
                                   id_destinataire, pseudo_destinataire, 
                                   contenu, est_prive, valide) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                id_expediteur, pseudo_expediteur, 
                id_destinataire, pseudo_destinataire,
                contenu, est_prive, auto_validate
            ))
            self.connection.commit()
            message_id = cursor.lastrowid
            return message_id
        except Error as e:
            print(f" Erreur lors de l'ajout du message: {e}")
            return None
        finally:
            cursor.close()
    
    def validate_message(self, message_id, admin_id):
        """
        Valide un message (permet sa distribution)
        
        Args:
            message_id (int): ID du message à valider
            admin_id (int): ID de l'admin qui valide
            
        Returns:
            bool: True si succès
        """
        try:
            cursor = self.connection.cursor()
            query = """
                UPDATE message 
                SET valide = TRUE, 
                    date_validation = NOW(), 
                    id_validateur = %s 
                WHERE id = %s
            """
            cursor.execute(query, (admin_id, message_id))
            self.connection.commit()
            print(f"Message {message_id} validé")
            return True
        except Error as e:
            print(f" Erreur lors de la validation: {e}")
            return False
        finally:
            cursor.close()
    
    def reject_message(self, message_id):
        """Supprime un message (rejet par admin)"""
        try:
            cursor = self.connection.cursor()
            query = "DELETE FROM message WHERE id = %s"
            cursor.execute(query, (message_id,))
            self.connection.commit()
            return True
        except Error as e:
            print(f" Erreur: {e}")
            return False
        finally:
            cursor.close()
    
    def get_messages(self, limit=100):
        """Récupère tous les messages validés (publics et privés)"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT m.*, e.pseudo as expediteur_pseudo 
                FROM message m 
                JOIN etudiant e ON m.id_expediteur = e.id 
                WHERE m.valide = TRUE 
                ORDER BY m.date_envoi DESC 
                LIMIT %s
            """
            cursor.execute(query, (limit,))
            return cursor.fetchall()
        except Error as e:
            print(f" Erreur: {e}")
            return []
        finally:
            cursor.close()
    
    def get_pending_messages(self):
        """Récupère tous les messages en attente de validation"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT m.*, e.pseudo as expediteur_pseudo, e.nom, e.prenom 
                FROM message m 
                JOIN etudiant e ON m.id_expediteur = e.id 
                WHERE m.valide = FALSE 
                ORDER BY m.date_envoi DESC
            """
            cursor.execute(query)
            return cursor.fetchall()
        except Error as e:
            print(f" Erreur: {e}")
            return []
        finally:
            cursor.close()
    
    def get_message_by_id(self, message_id):
        """Récupère un message par son ID"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT m.*, e.pseudo as expediteur_pseudo 
                FROM message m 
                JOIN etudiant e ON m.id_expediteur = e.id 
                WHERE m.id = %s
            """
            cursor.execute(query, (message_id,))
            return cursor.fetchone()
        except Error as e:
            print(f" Erreur: {e}")
            return None
        finally:
            cursor.close()
    
    # ========================================
    # HISTORIQUE DES CONNEXIONS
    # ========================================
    
    def log_login(self, id_etudiant, username, pseudo, action, ip_address=None, 
                 user_agent=None, session_id=None):
        """
        Enregistre une connexion ou déconnexion
        
        Args:
            id_etudiant (int): ID de l'étudiant
            username (str): Username
            pseudo (str): Pseudo
            action (str): 'LOGIN' ou 'LOGOUT'
            ip_address (str): Adresse IP
            user_agent (str): User agent du navigateur
            session_id (str): ID de session
        """
        try:
            cursor = self.connection.cursor()
            query = """
                INSERT INTO historique_login 
                (id_etudiant, username, pseudo, action, ip_address, 
                 user_agent, session_id) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                id_etudiant, username, pseudo, action, 
                ip_address, user_agent, session_id
            ))
            self.connection.commit()
            print(f"{action} enregistré pour {username}")
        except Error as e:
            print(f" Erreur lors de l'enregistrement du log: {e}")
        finally:
            cursor.close()
    
    def get_login_history(self, username=None, limit=50):
        """Récupère l'historique des connexions"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            if username:
                query = """
                    SELECT * FROM historique_login 
                    WHERE username = %s 
                    ORDER BY date_action DESC 
                    LIMIT %s
                """
                cursor.execute(query, (username, limit))
            else:
                query = """
                    SELECT * FROM historique_login 
                    ORDER BY date_action DESC 
                    LIMIT %s
                """
                cursor.execute(query, (limit,))
            return cursor.fetchall()
        except Error as e:
            print(f" Erreur: {e}")
            return []
        finally:
            cursor.close()
    
    # ========================================
    # ADMINISTRATEURS
    # ========================================
    
    def get_admin_by_username(self, username):
        """Récupère un administrateur par son username"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM administrateur WHERE username = %s"
            cursor.execute(query, (username,))
            return cursor.fetchone()
        except Error as e:
            print(f" Erreur: {e}")
            return None
        finally:
            cursor.close()
    
    # ========================================
    # STATISTIQUES
    # ========================================
    
    def get_stats(self):
        """Récupère des statistiques globales"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            stats = {}
            
            # Nombre total d'étudiants
            cursor.execute("SELECT COUNT(*) as total FROM etudiant")
            stats['total_users'] = cursor.fetchone()['total']
            
            # Comptes actifs
            cursor.execute("SELECT COUNT(*) as total FROM etudiant WHERE compte_actif = TRUE")
            stats['active_users'] = cursor.fetchone()['total']
            
            # Comptes approuvés
            cursor.execute("SELECT COUNT(*) as total FROM etudiant WHERE compte_approuve = TRUE")
            stats['approved_users'] = cursor.fetchone()['total']
            
            # Messages totaux
            cursor.execute("SELECT COUNT(*) as total FROM message")
            stats['total_messages'] = cursor.fetchone()['total']
            
            # Messages validés
            cursor.execute("SELECT COUNT(*) as total FROM message WHERE valide = TRUE")
            stats['validated_messages'] = cursor.fetchone()['total']
            
            # Messages en attente
            cursor.execute("SELECT COUNT(*) as total FROM message WHERE valide = FALSE")
            stats['pending_messages'] = cursor.fetchone()['total']
            
            return stats
        except Error as e:
            print(f" Erreur: {e}")
            return {}
        finally:
            cursor.close()

