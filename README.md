# Prototipo de Asistente Bancario de IA

Este proyecto es un prototipo de asistente bancario de IA para Banamex, Inbursa y BBVA, usando OpenAI y Oracle.

## Estructura del Proyecto

```
prototipo_banco/
│
├── data/                  # Datos del sistema (clientes, productos)
├── src/
│   ├── config/           # Configuraciones del sistema
│   ├── models/           # Modelos de datos
│   ├── repositories/     # Acceso a datos
│   ├── services/         # Lógica de negocio
│   ├── chatbot/          # Gestión del chatbot
│   └── frontend/         # Interfaz web
└── main.py               # Punto de entrada de la aplicación
```

## Requisitos

- Python 3.8+
- Dependencias listadas en requirements.txt

## Instalación

1. Clonar el repositorio
2. Crear un entorno virtual: `python -m venv venv`
3. Activar el entorno virtual: `source venv/bin/activate`
4. Instalar dependencias: `pip install -r requirements.txt`

## Uso

Para iniciar la aplicación:
```bash
python main.py
```
