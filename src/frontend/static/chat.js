document.addEventListener('DOMContentLoaded', () => {
    const messageInput = document.querySelector('.chat-input input');
    const sendButton = document.querySelector('.chat-input button');
    const chatMessages = document.querySelector('.chat-messages');
    const userInfo = document.querySelector('.user-info');
    const logoutButton = document.querySelector('.logout-button');

    // Verificar si hay una sesión activa
    const token = localStorage.getItem('token');
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));

    if (!token || !currentUser) {
        window.location.href = '/';
        return;
    }

    // Mostrar información del usuario
    userInfo.textContent = currentUser.name;
    addMessage('¡Bienvenido! ¿En qué puedo ayudarte hoy?', 'bot');

    // Manejar el envío de mensajes
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
                logout();
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
    logoutButton.addEventListener('click', logout);

    function logout() {
        localStorage.removeItem('token');
        localStorage.removeItem('currentUser');
        window.location.href = '/';
    }
}); 