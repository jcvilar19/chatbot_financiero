document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.getElementById('chatContainer');
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    
    // Función para agregar un mensaje al chat
    function addMessage(text, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user' : 'system'}`;
        messageDiv.textContent = text;
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    // Función para manejar el envío de mensajes
    async function handleSendMessage() {
        const message = userInput.value.trim();
        if (message) {
            // Agregar mensaje del usuario
            addMessage(message, true);
            
            // Limpiar el input
            userInput.value = '';
            
            // Mostrar indicador de "pensando"
            const thinkingDiv = document.createElement('div');
            thinkingDiv.className = 'message system';
            thinkingDiv.textContent = 'Asistente está pensando...';
            chatContainer.appendChild(thinkingDiv);
            
            try {
                // Enviar mensaje al backend
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        message,
                        user_id: 'C001' // ID de cliente por defecto
                    }),
                });
                
                if (!response.ok) {
                    throw new Error('Error en la respuesta del servidor');
                }
                
                const data = await response.json();
                
                // Remover el mensaje de "pensando"
                chatContainer.removeChild(thinkingDiv);
                
                // Agregar respuesta del asistente
                addMessage(data.message);
            } catch (error) {
                // Remover el mensaje de "pensando"
                chatContainer.removeChild(thinkingDiv);
                
                // Mostrar mensaje de error
                addMessage('Lo siento, ha ocurrido un error. Por favor, intenta nuevamente.');
                console.error('Error:', error);
            }
        }
    }
    
    // Event listeners
    sendButton.addEventListener('click', handleSendMessage);
    
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });
    
    // Habilitar el input y botón
    userInput.disabled = false;
    sendButton.disabled = false;
}); 