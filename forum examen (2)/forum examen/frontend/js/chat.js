/**
 * chat.js - Gestion du chat en temps réel
 */

// Configuration
const API_URL = 'http://127.0.0.1:5000';

// Variables globales
let socket;
let currentUser = null;

// ========================================
// INITIALISATION
// ========================================

document.addEventListener('DOMContentLoaded', () => {
    // Vérifier si l'utilisateur est connecté
    const userData = localStorage.getItem('user');
    if (!userData) {
        window.location.href = 'index.html';
        return;
    }
    
    currentUser = JSON.parse(userData);
    
    // Afficher les infos utilisateur
    document.getElementById('username-display').textContent = currentUser.pseudo || currentUser.username;
    
    // Afficher le badge selon le statut d'approbation
    const badge = document.getElementById('user-badge');
    if (currentUser.compte_approuve) {
        badge.textContent = '⭐ Approuvé';
        badge.classList.add('approved');
    } else {
        badge.textContent = '⏳ En attente';
    }
    
    // Afficher la notice si non approuvé
    if (!currentUser.compte_approuve) {
        document.getElementById('pending-notice').style.display = 'block';
    }
    
    // Initialiser Socket.IO
    initializeSocket();
    
    // Charger les messages existants
    loadMessages();
});

// ========================================
// WEBSOCKET
// ========================================

function initializeSocket() {
    socket = io(API_URL);
    
    socket.on('connect', () => {
        console.log('✓ Connecté au serveur');
        updateConnectionStatus(true);
        
        // Envoyer l'événement de connexion utilisateur
        socket.emit('user_connected', {
            username: currentUser.username,
            pseudo: currentUser.pseudo
        });
    });
    
    socket.on('disconnect', () => {
        console.log('✗ Déconnecté du serveur');
        updateConnectionStatus(false);
    });
    
    // Nouveau message reçu
    socket.on('new_message', (data) => {
        displayMessage(data);
        scrollToBottom();
    });
    
    // Message en attente de validation
    socket.on('message_pending_validation', (data) => {
        alert(data.message);
    });
    
    // Notification d'erreur
    socket.on('error', (data) => {
        alert(data.message);
    });
    
    // Notification admin
    socket.on('admin_notification', (data) => {
        console.log('Notification:', data);
    });
}

function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connection-status');
    if (connected) {
        statusEl.textContent = 'Connecté';
        statusEl.className = 'connection-status status-connected';
    } else {
        statusEl.textContent = 'Déconnecté';
        statusEl.className = 'connection-status status-disconnected';
    }
}

// ========================================
// MESSAGES
// ========================================

async function loadMessages() {
    try {
        const response = await fetch(`${API_URL}/messages?limit=100`);
        const messages = await response.json();
        
        const messagesContainer = document.getElementById('messages');
        messagesContainer.innerHTML = '';
        
        // Afficher les messages dans l'ordre chronologique
        messages.reverse().forEach(message => {
            displayMessage(message);
        });
        
        scrollToBottom();
        
    } catch (error) {
        console.error('Erreur lors du chargement des messages:', error);
    }
}

function displayMessage(data) {
    const messagesContainer = document.getElementById('messages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message' + (data.is_private ? ' private' : '');
    
    // Formater la date
    const timestamp = data.timestamp ? new Date(data.timestamp).toLocaleString('fr-FR') : '';
    
    messageDiv.innerHTML = `
        <div class="msg-header">
            <span class="msg-author">${data.from || data.pseudo_expediteur}</span>
            <span class="msg-time">${timestamp}</span>
        </div>
        <div class="msg-content">${escapeHtml(data.content || data.contenu)}</div>
    `;
    
    messagesContainer.appendChild(messageDiv);
}

function sendMessage() {
    const input = document.getElementById('message-input');
    const content = input.value.trim();
    
    if (!content) {
        return;
    }
    
    // Envoyer via WebSocket
    socket.emit('send_message', {
        username: currentUser.username,
        pseudo: currentUser.pseudo,
        content: content
    });
    
    // Vider l'input
    input.value = '';
    input.focus();
}

function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

function scrollToBottom() {
    const messagesContainer = document.getElementById('messages');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
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

// ========================================
// DÉCONNEXION
// ========================================

function logout() {
    if (confirm('Voulez-vous vraiment vous déconnecter ?')) {
        localStorage.removeItem('user');
        window.location.href = 'index.html';
    }
}

