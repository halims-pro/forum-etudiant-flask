/**
 * admin.js - Interface d'administration
 * Gestion des comptes et validation des messages
 */

// Configuration - à importer depuis config.js
const API_URL = 'http://127.0.0.1:5000';

// Connexion Socket.IO
let socket;

// ========================================
// INITIALISATION
// ========================================

document.addEventListener('DOMContentLoaded', async () => {
    // Vérifier si l'admin est connecté
    const adminUsername = localStorage.getItem('admin_username');
    if (!adminUsername) {
        window.location.href = 'admin_login.html';
        return;
    }
    
    // Afficher le nom de l'admin
    document.getElementById('admin-name').textContent = adminUsername;
    
    // Initialiser Socket.IO
    initializeSocket();
    
    // Charger les données initiales
    await loadStats();
    await loadPendingAccounts();
    await loadUnapprovedAccounts();
    await loadPendingMessages();
    await loadAllUsers();
    
    // Rafraîchir automatiquement toutes les 30 secondes
    setInterval(async () => {
        await loadStats();
        await loadPendingAccounts();
        await loadUnapprovedAccounts();
        await loadPendingMessages();
    }, 30000);
    
    // Gérer la déconnexion
    document.getElementById('logout-btn')?.addEventListener('click', logout);
});

// ========================================
// WEBSOCKET
// ========================================

function initializeSocket() {
    socket = io(API_URL);
    
    socket.on('connect', () => {
        console.log('✓ Connecté au serveur WebSocket');
        // Rejoindre la room admin pour recevoir les notifications
        socket.emit('join_admin_room');
    });
    
    socket.on('admin_notification', async (data) => {
        console.log('🔔 Notification admin:', data);
        
        if (data.type === 'new_pending_message') {
            // Nouveau message en attente
            showNotification('Nouveau message en attente de validation');
            await loadPendingMessages();
            await loadStats();
        }
    });
    
    socket.on('disconnect', () => {
        console.log('✗ Déconnecté du serveur WebSocket');
    });
}

// ========================================
// STATISTIQUES
// ========================================

async function loadStats() {
    try {
        const response = await fetch(`${API_URL}/admin/stats`);
        const stats = await response.json();
        
        // Mettre à jour les cartes de statistiques
        document.getElementById('stat-total-users').textContent = stats.total_users || 0;
        document.getElementById('stat-active-users').textContent = stats.active_users || 0;
        document.getElementById('stat-approved-users').textContent = stats.approved_users || 0;
        document.getElementById('stat-total-messages').textContent = stats.total_messages || 0;
        document.getElementById('stat-validated-messages').textContent = stats.validated_messages || 0;
        document.getElementById('stat-pending-messages').textContent = stats.pending_messages || 0;
        
    } catch (error) {
        console.error('Erreur lors du chargement des stats:', error);
    }
}

// ========================================
// GESTION DES COMPTES
// ========================================

async function loadPendingAccounts() {
    try {
        const response = await fetch(`${API_URL}/admin/pending_accounts`);
        const accounts = await response.json();
        
        const container = document.getElementById('pending-accounts-list');
        
        if (accounts.length === 0) {
            container.innerHTML = '<p class="no-data">Aucun compte en attente d\'activation</p>';
            return;
        }
        
        container.innerHTML = accounts.map(account => `
            <div class="account-card">
                <div class="account-info">
                    <h4>${account.nom} ${account.prenom}</h4>
                    <p><strong>Pseudo:</strong> ${account.pseudo}</p>
                    <p><strong>Username:</strong> ${account.username}</p>
                    <p><strong>Inscription:</strong> ${formatDate(account.date_inscription)}</p>
                </div>
                <div class="account-actions">
                    <button class="btn btn-success" onclick="activateAccount('${account.username}', '${account.pseudo}')">
                        ✓ Activer
                    </button>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Erreur lors du chargement des comptes en attente:', error);
    }
}

async function loadUnapprovedAccounts() {
    try {
        const response = await fetch(`${API_URL}/admin/unapproved_accounts`);
        const accounts = await response.json();
        
        const container = document.getElementById('unapproved-accounts-list');
        
        if (accounts.length === 0) {
            container.innerHTML = '<p class="no-data">Aucun compte à approuver</p>';
            return;
        }
        
        container.innerHTML = accounts.map(account => `
            <div class="account-card">
                <div class="account-info">
                    <h4>${account.nom} ${account.prenom}</h4>
                    <p><strong>Pseudo:</strong> ${account.pseudo}</p>
                    <p><strong>Username:</strong> ${account.username}</p>
                    <p><strong>Statut:</strong> <span class="badge badge-warning">Actif mais non approuvé</span></p>
                </div>
                <div class="account-actions">
                    <button class="btn btn-primary" onclick="approveAccount('${account.username}', '${account.pseudo}')">
                        ⭐ Approuver (Distribution auto)
                    </button>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Erreur lors du chargement des comptes non approuvés:', error);
    }
}

async function loadAllUsers() {
    try {
        const response = await fetch(`${API_URL}/admin/users`);
        const users = await response.json();
        
        const container = document.getElementById('all-users-list');
        
        if (users.length === 0) {
            container.innerHTML = '<p class="no-data">Aucun utilisateur actif</p>';
            return;
        }
        
        container.innerHTML = `
            <table class="users-table">
                <thead>
                    <tr>
                        <th>Nom</th>
                        <th>Prénom</th>
                        <th>Pseudo</th>
                        <th>Username</th>
                        <th>Statut</th>
                        <th>Inscription</th>
                    </tr>
                </thead>
                <tbody>
                    ${users.map(user => `
                        <tr>
                            <td>${user.nom}</td>
                            <td>${user.prenom}</td>
                            <td>${user.pseudo}</td>
                            <td>${user.username}</td>
                            <td>
                                ${user.compte_approuve 
                                    ? '<span class="badge badge-success">✓ Approuvé</span>' 
                                    : '<span class="badge badge-warning">⏳ Non approuvé</span>'}
                            </td>
                            <td>${formatDate(user.date_inscription)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        
    } catch (error) {
        console.error('Erreur lors du chargement des utilisateurs:', error);
    }
}

async function activateAccount(username, pseudo) {
    if (!confirm(`Voulez-vous activer le compte de ${pseudo} (${username}) ?\n\nL'étudiant pourra se connecter mais ses messages nécessiteront une validation.`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/admin/activate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification(`✓ Compte ${pseudo} activé avec succès`, 'success');
            await loadPendingAccounts();
            await loadUnapprovedAccounts();
            await loadStats();
        } else {
            showNotification(`✗ Erreur: ${data.error}`, 'error');
        }
        
    } catch (error) {
        console.error('Erreur lors de l\'activation:', error);
        showNotification('✗ Erreur lors de l\'activation', 'error');
    }
}

async function approveAccount(username, pseudo) {
    if (!confirm(`Voulez-vous approuver définitivement le compte de ${pseudo} (${username}) ?\n\n⚠️ Les messages de cet utilisateur seront distribués AUTOMATIQUEMENT sans validation.`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/admin/approve`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification(`✓ Compte ${pseudo} approuvé définitivement`, 'success');
            await loadUnapprovedAccounts();
            await loadAllUsers();
            await loadStats();
        } else {
            showNotification(`✗ Erreur: ${data.error}`, 'error');
        }
        
    } catch (error) {
        console.error('Erreur lors de l\'approbation:', error);
        showNotification('✗ Erreur lors de l\'approbation', 'error');
    }
}

// ========================================
// GESTION DES MESSAGES
// ========================================

async function loadPendingMessages() {
    try {
        const response = await fetch(`${API_URL}/admin/pending_messages`);
        const messages = await response.json();
        
        const container = document.getElementById('pending-messages-list');
        
        if (messages.length === 0) {
            container.innerHTML = '<p class="no-data">Aucun message en attente de validation</p>';
            return;
        }
        
        container.innerHTML = messages.map(message => `
            <div class="message-card">
                <div class="message-header">
                    <div class="message-author">
                        <strong>${message.nom} ${message.prenom}</strong> (${message.expediteur_pseudo})
                    </div>
                    <div class="message-time">
                        ${formatDate(message.date_envoi)}
                    </div>
                </div>
                <div class="message-content">
                    ${escapeHtml(message.contenu)}
                </div>
                <div class="message-meta">
                    <span class="message-type">
                        ${message.est_prive 
                            ? `📧 Privé → ${message.pseudo_destinataire || 'N/A'}` 
                            : '📢 Public'}
                    </span>
                </div>
                <div class="message-actions">
                    <button class="btn btn-success" onclick="validateMessage(${message.id}, '${message.expediteur_pseudo}')">
                        ✓ Valider
                    </button>
                    <button class="btn btn-danger" onclick="rejectMessage(${message.id}, '${message.expediteur_pseudo}')">
                        ✗ Rejeter
                    </button>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Erreur lors du chargement des messages en attente:', error);
    }
}

async function validateMessage(messageId, pseudo) {
    try {
        const response = await fetch(`${API_URL}/admin/validate_message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message_id: messageId })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification(`✓ Message de ${pseudo} validé et distribué`, 'success');
            await loadPendingMessages();
            await loadStats();
        } else {
            showNotification(`✗ Erreur: ${data.error}`, 'error');
        }
        
    } catch (error) {
        console.error('Erreur lors de la validation:', error);
        showNotification('✗ Erreur lors de la validation', 'error');
    }
}

async function rejectMessage(messageId, pseudo) {
    if (!confirm(`Voulez-vous rejeter ce message de ${pseudo} ?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/admin/reject_message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message_id: messageId })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification(`✓ Message de ${pseudo} rejeté`, 'success');
            await loadPendingMessages();
            await loadStats();
        } else {
            showNotification(`✗ Erreur: ${data.error}`, 'error');
        }
        
    } catch (error) {
        console.error('Erreur lors du rejet:', error);
        showNotification('✗ Erreur lors du rejet', 'error');
    }
}

// ========================================
// UTILITAIRES
// ========================================

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString('fr-FR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '<',
        '>': '>',
        '"': '"',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

function showNotification(message, type = 'info') {
    // Créer la notification
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Ajouter au DOM
    const container = document.getElementById('notification_container') || createNotificationContainer();
    container.appendChild(notification);
    
    // Supprimer après 5 secondes
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

function createNotificationContainer() {
    const container = document.createElement('div');
    container.id = 'notification_container';
    container.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
    `;
    document.body.appendChild(container);
    return container;
}

function logout() {
    if (confirm('Voulez-vous vraiment vous déconnecter ?')) {
        localStorage.removeItem('admin_username');
        localStorage.removeItem('admin_id');
        window.location.href = 'admin_login.html';
    }
}

