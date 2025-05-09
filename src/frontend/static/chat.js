document.addEventListener('DOMContentLoaded', () => {
    const messageInput = document.querySelector('.chat-input input');
    const sendButton = document.querySelector('.chat-input button');
    const chatMessages = document.querySelector('.chat-messages');
    const userInfo = document.querySelector('.user-info');
    const logoutButton = document.querySelector('.logout-button');
    
    // Añadir botón para limpiar historial
    const headerElement = document.querySelector('.chat-header');
    const clearHistoryButton = document.createElement('button');
    clearHistoryButton.className = 'clear-history-button';
    clearHistoryButton.textContent = 'Limpiar Conversación';
    clearHistoryButton.style.marginRight = '10px';
    headerElement.insertBefore(clearHistoryButton, logoutButton);

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
        
        // Añadir indicador de "pensando"
        const thinkingDiv = document.createElement('div');
        thinkingDiv.className = 'message bot-message thinking';
        thinkingDiv.textContent = 'Pensando...';
        chatMessages.appendChild(thinkingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ message })
            });

            // Eliminar el indicador de "pensando"
            chatMessages.removeChild(thinkingDiv);
            
            const data = await response.json();
            
            if (response.ok) {
                // Dar formato a la respuesta
                const formattedResponse = formatResponse(data.response);
                addMessage(formattedResponse, 'bot');
            } else if (response.status === 401) {
                // Si el token expiró, volver al login
                logout();
            } else {
                addMessage('Lo siento, ha ocurrido un error al procesar tu mensaje.', 'bot');
            }
        } catch (error) {
            // Eliminar el indicador de "pensando" en caso de error
            if (document.querySelector('.thinking')) {
                chatMessages.removeChild(document.querySelector('.thinking'));
            }
            addMessage('Error de conexión con el servidor.', 'bot');
        }
    }

    // Función para formatear la respuesta
    function formatResponse(text) {
        // Si hay elementos de lista numerados, asegurarse de que se muestren con saltos de línea
        return text.replace(/(\d+\.\s.*?)(?=\d+\.|$)/g, '$1\n\n')
                   .replace(/\n{3,}/g, '\n\n'); // Evitar demasiados saltos de línea
    }

    function addMessage(text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        if (type === 'bot' && window.marked) {
            // Renderizar Markdown como HTML para mensajes del bot
            messageDiv.innerHTML = marked.parse(text);
        } else if (text.includes('\n')) {
            messageDiv.innerHTML = text.split('\n').map(line => {
                return line.trim() ? `<p>${line}</p>` : '<br>';
            }).join('');
        } else {
            messageDiv.textContent = text;
        }
        
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
    
    // Manejar la limpieza del historial
    clearHistoryButton.addEventListener('click', async () => {
        try {
            const response = await fetch('/clear-history', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                // Limpiar chat en la interfaz
                chatMessages.innerHTML = '';
                addMessage('El historial de conversación ha sido borrado.', 'bot');
            } else if (response.status === 401) {
                logout();
            } else {
                addMessage('No se pudo limpiar el historial.', 'bot');
            }
        } catch (error) {
            addMessage('Error al comunicarse con el servidor.', 'bot');
        }
    });
});