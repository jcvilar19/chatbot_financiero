import os
from flask import Flask, request, jsonify, render_template, session
import pandas as pd
import jwt
from datetime import datetime, timedelta
from openai import OpenAI
from dotenv import load_dotenv
import logging
import json

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
app.secret_key = SECRET_KEY
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
CLIENTES_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'clientes.xlsx')

# Inicializar cliente de OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Diccionario para almacenar conversaciones por usuario
conversation_history = {}

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
            'name': 'Juan Pérez',
            'customer_id': '1001',
            'bank_name': 'Inbursa',
            'account_number': '1234567890',
            'saldo': 50000.0,
            'customer_type': 'Premium'
        }

        # Inicializar historial de conversación para este usuario si no existe
        if username not in conversation_history:
            conversation_history[username] = []

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
        username = token_data['username']
        logger.debug(f"Mensaje recibido de {username}: {user_message}")

        # Obtener información del usuario
        df = pd.read_excel(CLIENTES_FILE)
        user = df[df['username'] == username].iloc[0]
        logger.debug(f"Información del usuario recuperada: {user['name']}")

        # Crear el mensaje del sistema para OpenAI
        system_message = f"""
Eres Paco, el asistente virtual de Inbursa.
Tienes acceso completo a la base de datos de clientes y al catálogo de productos de Inbursa. Tu objetivo es ayudar, informar y recomendar productos financieros de manera personalizada y proactiva, siempre en español.

Contexto disponible:
- Datos del cliente: nombre, tipo de cuenta, número de cuenta, saldo y cualquier otra información relevante de la base de datos.
- Catálogo de productos: lista completa de productos y servicios de Inbursa, con todas sus características, beneficios, requisitos y palabras clave asociadas.

EXPLICACIÓN DE LAS COLUMNAS DEL CATÁLOGO DE PRODUCTOS (acceso: {{producto['nombre_columna']}}):
- Título de Variable: Nombre de la variable o campo. (Ejemplo: {{producto['Título de Variable']}})
- id_producto: Identificador único del producto. (Ejemplo: {{producto['id_producto']}})
- tipo_producto: Categoría general del producto (ejemplo: inversión, seguro, crédito, etc.). (Ejemplo: {{producto['tipo_producto']}})
- subtipo_producto: Subcategoría específica del producto. (Ejemplo: {{producto['subtipo_producto']}})
- nombre_producto: Nombre comercial del producto. (Ejemplo: {{producto['nombre_producto']}})
- descripción_corta: Descripción breve del producto. (Ejemplo: {{producto['descripción_corta']}})
- descripcion_comercial: Descripción comercial o de marketing del producto. (Ejemplo: {{producto['descripcion_comercial']}})
- beneficios_clave: Beneficios principales que ofrece el producto. (Ejemplo: {{producto['beneficios_clave']}})
- coberturas: Coberturas incluidas (aplica para seguros). (Ejemplo: {{producto['coberturas']}})
- sumas_aseguradas: Montos asegurados o cubiertos (aplica para seguros). (Ejemplo: {{producto['sumas_aseguradas']}})
- Saldo: Saldo relacionado o requerido para el producto (si aplica). (Ejemplo: {{producto['Saldo']}})
- modalidades_pago: Formas de pago disponibles para el producto. (Ejemplo: {{producto['modalidades_pago']}})
- plazo_contrato: Plazo mínimo o máximo del contrato del producto. (Ejemplo: {{producto['plazo_contrato']}})
- precio_aproximado: Precio o costo estimado del producto. (Ejemplo: {{producto['precio_aproximado']}})
- edad_minima: Edad mínima requerida para contratar el producto. (Ejemplo: {{producto['edad_minima']}})
- edad_maxima: Edad máxima permitida para contratar el producto. (Ejemplo: {{producto['edad_maxima']}})
- ocupaciones: Ocupaciones recomendadas o permitidas para el producto. (Ejemplo: {{producto['ocupaciones']}})
- situaciones_relevantes: Situaciones de vida o eventos donde el producto es relevante. (Ejemplo: {{producto['situaciones_relevantes']}})
- nivel_ingresos_sugerido: Nivel de ingresos recomendado para el producto. (Ejemplo: {{producto['nivel_ingresos_sugerido']}})
- segmento_cliente_objetivo: Segmento de clientes al que va dirigido el producto. (Ejemplo: {{producto['segmento_cliente_objetivo']}})
- trigger_venta: Palabras clave o situaciones que disparan la recomendación del producto. (Ejemplo: {{producto['trigger_venta']}})
- canales_disponibles: Canales donde se puede contratar o consultar el producto. (Ejemplo: {{producto['canales_disponibles']}})
- palabras_clave_asociadas: Palabras clave para identificar necesidades relacionadas con el producto. (Ejemplo: {{producto['palabras_clave_asociadas']}})
- intenciones_clientes: Intenciones o motivos típicos de los clientes para contratar el producto. (Ejemplo: {{producto['intenciones_clientes']}})
- Respuesta_IA: Respuesta sugerida para la IA al recomendar este producto. (Ejemplo: {{producto['Respuesta_IA']}})

INFORMACIÓN DEL CLIENTE:
- Nombre: {user['name']}
- Tipo de cuenta: {user['customer_type']}
- Número de cuenta: {user['account_number']}
- Saldo actual: ${user['saldo']:,.2f}

INSTRUCCIONES:
1. Personalización:
   - Analiza la información del cliente y su historial de conversación.
   - Utiliza palabras clave presentes en la base de datos para identificar necesidades, intereses o eventos relevantes (por ejemplo: "ahorro", "viaje", "retiro", "inversión", "protección", "educación", "jubilación", "emergencia", etc.).
2. Recomendación proactiva:
   - Si detectas una oportunidad (por ejemplo, el cliente menciona una meta, necesidad o situación que se puede cubrir con un producto de Inbursa), recomienda el producto más adecuado del catálogo.
   - Explica brevemente por qué ese producto es relevante para el cliente, usando datos concretos de su perfil o conversación.
   - Si el cliente muestra interés, ofrece detalles adicionales y guía sobre cómo contratarlo.
3. Precisión y transparencia:
   - Usa siempre la información real y actualizada de la base de datos y el catálogo.
   - Si el cliente pregunta por un producto específico, responde con detalles exactos (características, tasas, requisitos, beneficios).
   - Si el producto no existe, sugiere alternativas disponibles.
4. Formato y tono:
   - Responde siempre en español, de manera clara, profesional y amable.
   - Presenta la información en listas o párrafos cortos, fáciles de leer.
   - No saludes ni te despidas, ve directo a la respuesta.
   - Si el cliente solicita hablar con un humano, indícale que será transferido a un asesor.
5. Consultas frecuentes:
   - Si preguntan por saldo, tipo de cuenta, número de cuenta o banco, responde con la información correspondiente del cliente.
   - Si el cliente solicita su información personal, proporciónala de forma clara y segura.

EJEMPLOS DE COMPORTAMIENTO ESPERADO:
- Si el cliente menciona "quiero ahorrar para un viaje", responde:
  "Detecto que tienes interés en ahorrar para un viaje. Te recomiendo nuestro Plan de Ahorro Inbursa, que te permite... [características y beneficios]. ¿Te gustaría saber más?"
- Si el cliente pregunta: "¿Qué productos de inversión ofrecen?"
  Responde con la lista exacta de productos de inversión disponibles, con una breve descripción de cada uno.
"""

        # Obtener o inicializar el historial de conversación
        if username not in conversation_history:
            conversation_history[username] = []
        
        # Construir la lista de mensajes para la API
        messages = [{"role": "system", "content": system_message}]
        
        # Añadir historial de conversación (últimos 10 mensajes para evitar superar límites)
        for msg in conversation_history[username][-10:]:
            messages.append(msg)
        
        # Añadir el mensaje actual del usuario
        messages.append({"role": "user", "content": user_message})
        
        logger.debug("Enviando solicitud a OpenAI...")
        
        # Realizar la llamada a la API de OpenAI
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7
        )

        # Obtener la respuesta
        ai_response = completion.choices[0].message.content
        logger.debug(f"Respuesta recibida de OpenAI: {ai_response}")
        
        # Guardar el mensaje del usuario y la respuesta en el historial
        conversation_history[username].append({"role": "user", "content": user_message})
        conversation_history[username].append({"role": "assistant", "content": ai_response})
        
        # Limitar el tamaño del historial (opcional, para evitar problemas de memoria)
        if len(conversation_history[username]) > 50:  # Mantener solo los últimos 25 pares de mensajes
            conversation_history[username] = conversation_history[username][-50:]

        return jsonify({'response': ai_response})

    except Exception as e:
        logger.error(f"Error en process_message: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/clear-history', methods=['POST'])
def clear_history():
    token_data = verify_token()
    if not token_data:
        return jsonify({'error': 'No autorizado'}), 401
    
    username = token_data['username']
    if username in conversation_history:
        conversation_history[username] = []
    
    return jsonify({'message': 'Historial de conversación eliminado'})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8082, debug=True)