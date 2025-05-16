import os
from flask import Flask, request, jsonify, render_template
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv
import logging
import json

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

app = Flask(
    __name__,
    template_folder='../frontend/templates',
    static_folder='../frontend/static'
)

# Configuración
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
PRODUCTS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'BD Productos Inbursa.xlsx')

# Inicializar cliente de OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Historial de conversación global
conversation_history = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def process_message():
    try:
        # Obtener el mensaje del usuario
        data = request.get_json()
        user_message = data.get('message', '')
        logger.debug(f"Mensaje recibido: {user_message}")

        # Cargar productos
        df_products = pd.read_excel(PRODUCTS_FILE)
        logger.debug(f"Productos cargados: {len(df_products)}")

        # Crear el mensaje del sistema para OpenAI
        system_message = f"""
Eres Paco, el asistente virtual de Inbursa.
Tienes acceso completo al catálogo de productos de Inbursa. Tu objetivo es ayudar, informar y recomendar productos financieros de manera personalizada y proactiva, siempre en español.

Contexto disponible:
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

INSTRUCCIONES:
1. Analiza la información del usuario y su mensaje.
2. Utiliza palabras clave presentes en la base de datos para identificar necesidades, intereses o eventos relevantes (por ejemplo: "ahorro", "viaje", "retiro", "inversión", "protección", "educación", "jubilación", "emergencia", etc.).
3. Si detectas una oportunidad, recomienda el producto más adecuado del catálogo.
4. Explica brevemente por qué ese producto es relevante, usando datos concretos del catálogo.
5. Si el usuario pregunta por un producto específico, responde con detalles exactos (características, tasas, requisitos, beneficios).
6. Si el producto no existe, sugiere alternativas disponibles.
7. Responde siempre en español, de manera clara, profesional y amable.
8. Presenta la información en listas o párrafos cortos, fáciles de leer.
9. No saludes ni te despidas, ve directo a la respuesta.
"""

        # Construir la lista de mensajes para la API
        messages = [{"role": "system", "content": system_message}]
        # Añadir historial de conversación (últimos 10 mensajes)
        for msg in conversation_history[-10:]:
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
        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": ai_response})
        # Limitar el tamaño del historial
        if len(conversation_history) > 50:
            conversation_history[:] = conversation_history[-50:]

        return jsonify({'response': ai_response})

    except Exception as e:
        logger.error(f"Error en process_message: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/clear-history', methods=['POST'])
def clear_history():
    conversation_history.clear()
    return jsonify({'message': 'Historial de conversación eliminado'})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8082, debug=True)