import os
from flask import Flask, request, jsonify, render_template
import pandas as pd
import jwt
from datetime import datetime, timedelta
from openai import OpenAI
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__, 
    template_folder='../frontend/templates',
    static_folder='../frontend/static')

# Configuración
SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
CLIENTES_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'clientes.xlsx')

# Inicializar cliente de OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    try:
        df = pd.read_excel(CLIENTES_FILE)
        user = df[df['username'] == username]
        
        if user.empty or user.iloc[0]['password'] != password:
            return jsonify({'error': 'Credenciales inválidas'}), 401

        token = jwt.encode({
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=1)
        }, SECRET_KEY, algorithm='HS256')

        user_data = {
            'name': user.iloc[0]['name'],
            'customer_id': str(user.iloc[0]['customer_id']),
            'bank_name': user.iloc[0]['bank_name'],
            'account_number': str(user.iloc[0]['account_number']),
            'saldo': float(user.iloc[0]['saldo']),
            'customer_type': user.iloc[0]['customer_type']
        }

        return jsonify({'token': token, 'user': user_data})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def verify_token():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    except:
        return None

@app.route('/chat', methods=['POST'])
def process_message():
    token_data = verify_token()
    if not token_data:
        return jsonify({'error': 'No autorizado'}), 401

    try:
        # Obtener el mensaje del usuario
        data = request.get_json()
        user_message = data.get('message', '')
        logger.debug(f"Mensaje recibido: {user_message}")

        # Obtener información del usuario
        df = pd.read_excel(CLIENTES_FILE)
        user = df[df['username'] == token_data['username']].iloc[0]
        logger.debug(f"Información del usuario recuperada: {user['name']}")

        # Crear el mensaje del sistema para OpenAI
        system_message = f"""
        Te llamas Paco, eres un asistente bancario virtual del banco {user['bank_name']}.
        Estás atendiendo a {user['name']}.

        Información del cliente:
        - Nombre: {user['name']}
        - Tipo de cuenta: {user['customer_type']}
        - Número de cuenta: {user['account_number']}
        - Saldo actual: ${user['saldo']:,.2f}

        Instrucciones:
        1. Responde siempre en español
        2. Responde siempre basandote en los productos y servicios que ofrece el banco.
        3. Nunca saludes al cliente, solo responde a lo que te pida. 
        4. Antes de responder a cada nueva solicitud, lee toda la conversación pasada para recuperar esta información si es necesario.
        5. Siempre da tus respuestas en un formato limpio y fácil de leer.
            4.1 Si vas a dar una lista, separa cada elemento enumerado con un salto de línea
        6. Siempre responder de forma amable y coherente
        7. Sé amable y profesional
        8. Proporciona la información del cliente cuando la solicite
        9. Para consultas específicas, responde exactamente así:
           - Si preguntan por saldo: "Tu saldo actual es: ${user['saldo']:,.2f}"
           - Si preguntan por tipo de cuenta: "Tu tipo de cuenta es: {user['customer_type']}"
           - Si preguntan por número de cuenta: "Tu número de cuenta es: {user['account_number']}"
           - Si preguntan por banco: "Tu banco es: {user['bank_name']}"
        10. Para otras consultas, proporciona información bancaria relevante 
        11. Siempre que veas la oportunidad, ofrece productos y servicios del banco. 
        12. Si el cliente te pide que habla con un humano, pídele que espere un momento y se conectará con un asesor.  
        """

        logger.debug("Enviando solicitud a OpenAI...")
        
        # Realizar la llamada a la API de OpenAI
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ]
        )

        # Obtener la respuesta
        ai_response = completion.choices[0].message.content
        logger.debug(f"Respuesta recibida de OpenAI: {ai_response}")

        return jsonify({'response': ai_response})

    except Exception as e:
        logger.error(f"Error en process_message: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8082, debug=True) 