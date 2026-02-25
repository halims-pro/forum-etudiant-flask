/**
 * auth.js - Fonctions d'authentification
 */

const API_URL = 'http://127.0.0.1:5000';

// ========================================
// CONNEXION
// ========================================

document.addEventListener('DOMContentLoaded', () => {
    // Si l'utilisateur est déjà connecté, rediriger vers le chat
    const userData = localStorage.getItem('user');
    if (userData) {
        window.location.href = 'chat.html';
    }
    
    // Ajouter l'événement au formulaire de connexion
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
});

async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('error-message');
    
    try {
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Stocker les informations utilisateur
            localStorage.setItem('user', JSON.stringify(data.user));
            
            // Rediriger vers le chat
            window.location.href = 'chat.html';
        } else {
            errorDiv.textContent = data.error || 'Erreur de connexion';
            errorDiv.style.display = 'block';
        }
        
    } catch (error) {
        errorDiv.textContent = 'Erreur de connexion au serveur';
        errorDiv.style.display = 'block';
    }
}

// ========================================
// INSCRIPTION
// ========================================

async function handleRegister(e) {
    e.preventDefault();
    
    const nom = document.getElementById('nom').value;
    const prenom = document.getElementById('prenom').value;
    const pseudo = document.getElementById('pseudo').value;
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('error-message');
    const successDiv = document.getElementById('success-message');
    
    try {
        const response = await fetch(`${API_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                nom,
                prenom,
                pseudo,
                username,
                password
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            successDiv.textContent = data.message || 'Inscription réussie !';
            successDiv.style.display = 'block';
            errorDiv.style.display = 'none';
            
            // Rediriger vers la page de connexion après 2 secondes
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 2000);
        } else {
            errorDiv.textContent = data.error || 'Erreur lors de l\'inscription';
            errorDiv.style.display = 'block';
            successDiv.style.display = 'none';
        }
        
    } catch (error) {
        errorDiv.textContent = 'Erreur de connexion au serveur';
        errorDiv.style.display = 'block';
        successDiv.style.display = 'none';
    }
}

// Alias pour compatibilité
function login() {
    // Cette fonction est appelée par le HTML
    handleLogin(new Event('submit'));
}

function register() {
    // Cette fonction est appelée par le HTML
    handleRegister(new Event('submit'));
}

