document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');

    // Si ya hay una sesión activa, redirigir al chat
    const token = localStorage.getItem('token');
    if (token) {
        window.location.href = '/chat';
        return;
    }

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
                window.location.href = '/chat';
            } else {
                showError(data.error);
            }
        } catch (error) {
            showError('Error al conectar con el servidor');
        }
    });

    function showError(message) {
        const errorDiv = document.querySelector('.error-message') || document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        
        if (!document.querySelector('.error-message')) {
            loginForm.appendChild(errorDiv);
        }
    }
}); 