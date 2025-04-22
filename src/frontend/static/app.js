document.addEventListener('DOMContentLoaded', () => {
    const loginScreen = document.getElementById('loginScreen');
    const chatScreen = document.getElementById('chatScreen');
    const loginForm = document.getElementById('loginForm');
    const messageInput = document.querySelector('.chat-input input');
    const sendButton = document.querySelector('.chat-input button');
    const chatMessages = document.querySelector('.chat-messages');
    const userInfo = document.querySelector('.user-info');
    const logoutButton = document.querySelector('.logout-button');

    let token = localStorage.getItem('token');
    let currentUser = JSON.parse(localStorage.getItem('currentUser'));

    // Función para mostrar la pantalla de login
    function showLogin() {
        loginScreen.style.display = 'flex';
        chatScreen.style.display = 'none';
        document.querySelector('#username').value = '';
        document.querySelector('#password').value = '';
        const errorMessage = document.querySelector('.error-message');
        if (errorMessage) {
            errorMessage.remove();
        }
    }

    // Función para mostrar la pantalla de chat
    function showChat(user) {
        loginScreen.style.display = 'none';
        chatScreen.style.display = 'flex';
        userInfo.textContent = user.name;
        messageInput.value = '';
        messageInput.focus();
        chatMessages.innerHTML = ''; // Limpiar mensajes anteriores
        addMessage('¡Bienvenido! ¿En qué puedo ayudarte hoy?', 'bot');
    }

    // Verificar si hay una sesión activa
    if (token && currentUser) {
        showChat(currentUser);
    } else {
        showLogin();
    }

    // Manejar el envío del formulario de login
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.querySelector('#username').value;
        const password = document.querySelector('#password').value;

        try {
            const response = await fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, password }),
            });

            const data = await response.json();

            if (response.ok) {
                localStorage.setItem('token', data.token);
                localStorage.setItem('currentUser', JSON.stringify(data.user));
                token = data.token;
                currentUser = data.user;
                showChat(data.user);
            } else {
                showError(data.error);
            }
        } catch (error) {
            showError('Error al conectar con el servidor');
        }
    });

    // Mostrar mensajes de error en el login
    function showError(message) {
        const errorDiv = document.querySelector('.error-message') || document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        
        if (!document.querySelector('.error-message')) {
            loginForm.appendChild(errorDiv);
        }
    }

    // Manejar el envío de mensajes en el chat
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    sendButton.addEventListener('click', (e) => {
        e.preventDefault();
        sendMessage();
    });

    async function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;

        addMessage(message, 'user');
        messageInput.value = '';

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ message })
            });

            const data = await response.json();
            
            if (response.ok) {
                addMessage(data.response, 'bot');
            } else if (response.status === 401) {
                // Si el token expiró, volver al login
                localStorage.removeItem('token');
                localStorage.removeItem('currentUser');
                showLogin();
                showError('Tu sesión ha expirado. Por favor, inicia sesión nuevamente.');
            } else {
                addMessage('Lo siento, ha ocurrido un error al procesar tu mensaje.', 'bot');
            }
        } catch (error) {
            addMessage('Error de conexión con el servidor.', 'bot');
        }
    }

    function addMessage(text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        messageDiv.textContent = text;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Manejar el cierre de sesión
    logoutButton.addEventListener('click', () => {
        localStorage.removeItem('token');
        localStorage.removeItem('currentUser');
        token = null;
        currentUser = null;
        showLogin();
    });
}); 