-- =============================================
-- Forum de Discussion - EST Salé
-- Base de données MySQL
-- =============================================

CREATE DATABASE IF NOT EXISTS forum_chat;
USE forum_chat;

-- =============================================
-- Table: etudiant
-- Description: Stocke les informations des étudiants
-- =============================================
CREATE TABLE IF NOT EXISTS etudiant (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(50) NOT NULL,
    prenom VARCHAR(50) NOT NULL,
    pseudo VARCHAR(50) NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    compte_actif BOOLEAN DEFAULT FALSE,      -- Activation par admin
    compte_approuve BOOLEAN DEFAULT FALSE,   -- Approbation finale pour distribution auto
    date_inscription DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_pseudo (pseudo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================
-- Table: administrateur
-- Description: Stocke les informations des administrateurs
-- =============================================
CREATE TABLE IF NOT EXISTS administrateur (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    nom VARCHAR(50) NOT NULL,
    prenom VARCHAR(50) NOT NULL,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================
-- Table: message
-- Description: Stocke tous les messages échangés
-- =============================================
CREATE TABLE IF NOT EXISTS message (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_expediteur INT NOT NULL,
    pseudo_expediteur VARCHAR(50) NOT NULL,
    id_destinataire INT,                     -- NULL pour message public (ALL)
    pseudo_destinataire VARCHAR(50),         -- NULL pour message public
    contenu TEXT NOT NULL,
    date_envoi DATETIME DEFAULT CURRENT_TIMESTAMP,
    valide BOOLEAN DEFAULT FALSE,            -- Validation par admin
    date_validation DATETIME,
    id_validateur INT,                       -- Admin qui a validé
    est_prive BOOLEAN DEFAULT FALSE,         -- Message privé ou public
    FOREIGN KEY (id_expediteur) REFERENCES etudiant(id) ON DELETE CASCADE,
    FOREIGN KEY (id_destinataire) REFERENCES etudiant(id) ON DELETE CASCADE,
    FOREIGN KEY (id_validateur) REFERENCES administrateur(id) ON DELETE SET NULL,
    INDEX idx_expediteur (id_expediteur),
    INDEX idx_destinataire (id_destinataire),
    INDEX idx_date (date_envoi),
    INDEX idx_valide (valide)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================
-- Table: historique_login
-- Description: Journal de toutes les connexions/déconnexions
-- =============================================
CREATE TABLE IF NOT EXISTS historique_login (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_etudiant INT NOT NULL,
    username VARCHAR(50) NOT NULL,
    pseudo VARCHAR(50) NOT NULL,
    action VARCHAR(20) NOT NULL,             -- 'LOGIN' ou 'LOGOUT'
    date_action DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),                  -- Support IPv4 et IPv6
    user_agent TEXT,                         -- Navigateur/OS
    session_id VARCHAR(100),
    FOREIGN KEY (id_etudiant) REFERENCES etudiant(id) ON DELETE CASCADE,
    INDEX idx_etudiant (id_etudiant),
    INDEX idx_date (date_action),
    INDEX idx_action (action)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================
-- Données de test - Administrateur par défaut
-- =============================================
-- Mot de passe: admin123 (hashé avec bcrypt)
INSERT INTO administrateur (username, password, nom, prenom) VALUES 
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYPxKfZ8cLG', 'Admin', 'System');

-- =============================================
-- Étudiants de test
-- =============================================
-- Mot de passe pour tous: password123
INSERT INTO etudiant (nom, prenom, pseudo, username, password, compte_actif, compte_approuve) VALUES
('Alami', 'Ahmed', 'pseudo1', 'etudiant1', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYPxKfZ8cLG', TRUE, FALSE),
('Bennani', 'Fatima', 'pseudo2', 'etudiant2', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYPxKfZ8cLG', TRUE, TRUE),
('Chakir', 'Hassan', 'pseudo3', 'etudiant3', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYPxKfZ8cLG', FALSE, FALSE);

-- =============================================
-- Messages de test
-- =============================================
INSERT INTO message (id_expediteur, pseudo_expediteur, id_destinataire, pseudo_destinataire, contenu, valide, est_prive) VALUES
(2, 'pseudo2', NULL, NULL, 'Bonjour à tous!', TRUE, FALSE),
(1, 'pseudo1', NULL, NULL, 'Salut, comment allez-vous?', FALSE, FALSE);

