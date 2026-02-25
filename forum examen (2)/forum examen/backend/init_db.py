#!/usr/bin/env python3
"""
Script pour initialiser la base de données du Forum Chat
"""

import mysql.connector

# Connexion sans mot de passe (utilise le socket Unix)
try:
    conn = mysql.connector.connect(
        unix_socket='/var/run/mysqld/mysqld.sock',
        user='root'
    )
    print("✓ Connexion MySQL réussie (socket)")
    
    cursor = conn.cursor()
    
    # Créer la base de données
    cursor.execute("CREATE DATABASE IF NOT EXISTS forum_chat")
    print("✓ Base de données 'forum_chat' créée")
    
    # Utiliser la base de données
    cursor.execute("USE forum_chat")
    
    # Créer la table etudiant
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS etudiant (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nom VARCHAR(50) NOT NULL,
            prenom VARCHAR(50) NOT NULL,
            pseudo VARCHAR(50) NOT NULL UNIQUE,
            username VARCHAR(50) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            compte_actif BOOLEAN DEFAULT FALSE,
            compte_approuve BOOLEAN DEFAULT FALSE,
            date_inscription DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_username (username),
            INDEX idx_pseudo (pseudo)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    print("✓ Table 'etudiant' créée")
    
    # Créer la table administrateur
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS administrateur (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            nom VARCHAR(50) NOT NULL,
            prenom VARCHAR(50) NOT NULL,
            date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    print("✓ Table 'administrateur' créée")
    
    # Créer la table message
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS message (
            id INT AUTO_INCREMENT PRIMARY KEY,
            id_expediteur INT NOT NULL,
            pseudo_expediteur VARCHAR(50) NOT NULL,
            id_destinataire INT,
            pseudo_destinataire VARCHAR(50),
            contenu TEXT NOT NULL,
            date_envoi DATETIME DEFAULT CURRENT_TIMESTAMP,
            valide BOOLEAN DEFAULT FALSE,
            date_validation DATETIME,
            id_validateur INT,
            est_prive BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (id_expediteur) REFERENCES etudiant(id) ON DELETE CASCADE,
            FOREIGN KEY (id_destinataire) REFERENCES etudiant(id) ON DELETE CASCADE,
            FOREIGN KEY (id_validateur) REFERENCES administrateur(id) ON DELETE SET NULL,
            INDEX idx_expediteur (id_expediteur),
            INDEX idx_destinataire (id_destinataire),
            INDEX idx_date (date_envoi),
            INDEX idx_valide (valide)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    print("✓ Table 'message' créée")
    
    # Créer la table historique_login
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historique_login (
            id INT AUTO_INCREMENT PRIMARY KEY,
            id_etudiant INT NOT NULL,
            username VARCHAR(50) NOT NULL,
            pseudo VARCHAR(50) NOT NULL,
            action VARCHAR(20) NOT NULL,
            date_action DATETIME DEFAULT CURRENT_TIMESTAMP,
            ip_address VARCHAR(45),
            user_agent TEXT,
            session_id VARCHAR(100),
            FOREIGN KEY (id_etudiant) REFERENCES etudiant(id) ON DELETE CASCADE,
            INDEX idx_etudiant (id_etudiant),
            INDEX idx_date (date_action),
            INDEX idx_action (action)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    print("✓ Table 'historique_login' créée")
    
    # Insérer l'admin par défaut (password: admin123)
    import bcrypt
    hashed = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor.execute("SELECT COUNT(*) FROM administrateur WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO administrateur (username, password, nom, prenom) VALUES (%s, %s, %s, %s)",
            ('admin', hashed, 'Admin', 'System')
        )
        print("✓ Administrateur par défaut créé (admin/admin123)")
    
    # Insérer les étudiants de test
    hashed_user = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Étudiant 1: actif mais non approuvé (messages en attente de validation)
    cursor.execute("SELECT COUNT(*) FROM etudiant WHERE username = 'etudiant1'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO etudiant (nom, prenom, pseudo, username, password, compte_actif, compte_approuve)
            VALUES (%s, %s, %s, %s, %s, TRUE, FALSE)
        """, ('Alami', 'Ahmed', 'pseudo1', 'etudiant1', hashed_user))
        print("✓ Étudiant de test 1 créé (actif, non approuvé)")
    
    # Étudiant 2: actif et approuvé (messages validés automatiquement)
    cursor.execute("SELECT COUNT(*) FROM etudiant WHERE username = 'etudiant2'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO etudiant (nom, prenom, pseudo, username, password, compte_actif, compte_approuve)
            VALUES (%s, %s, %s, %s, %s, TRUE, TRUE)
        """, ('Bennani', 'Fatima', 'pseudo2', 'etudiant2', hashed_user))
        print("✓ Étudiant de test 2 créé (actif, approuvé)")
    
    # Étudiant 3: inactif (en attente d'activation)
    cursor.execute("SELECT COUNT(*) FROM etudiant WHERE username = 'etudiant3'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO etudiant (nom, prenom, pseudo, username, password, compte_actif, compte_approuve)
            VALUES (%s, %s, %s, %s, %s, FALSE, FALSE)
        """, ('Chakir', 'Hassan', 'pseudo3', 'etudiant3', hashed_user))
        print("✓ Étudiant de test 3 créé (inactif)")
    
    # Insérer des messages de test
    cursor.execute("SELECT COUNT(*) FROM message")
    if cursor.fetchone()[0] == 0:
        # Message de etudiant2 (approuvé) - validé automatiquement
        cursor.execute("""
            INSERT INTO message (id_expediteur, pseudo_expediteur, id_destinataire, pseudo_destinataire, contenu, valide, est_prive)
            VALUES (2, 'pseudo2', NULL, NULL, 'Bonjour à tous! Bienvenue sur le forum!', TRUE, FALSE)
        """)
        # Message de etudiant1 (non approuvé) - en attente
        cursor.execute("""
            INSERT INTO message (id_expediteur, pseudo_expediteur, id_destinataire, pseudo_destinataire, contenu, valide, est_prive)
            VALUES (1, 'pseudo1', NULL, NULL, 'Salut, comment allez-vous?', FALSE, FALSE)
        """)
        print("✓ Messages de test créés")
    
    conn.commit()
    conn.close()
    print("\n" + "="*50)
    print("✓ Base de données initialisée avec succès!")
    print("="*50)
    print("\nComptes de test disponibles:")
    print("  - Admin: admin / admin123")
    print("  - Étudiant 1: etudiant1 / password123 (actif, non approuvé)")
    print("  - Étudiant 2: etudiant2 / password123 (actif, approuvé)")
    print("  - Étudiant 3: etudiant3 / password123 (inactif)")
    
except Exception as e:
    print(f"✗ Erreur: {e}")
    import traceback
    traceback.print_exc()

