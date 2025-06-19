# 📊 Resumen de Inversiones

Aplicación web para el seguimiento y gestión de inversiones en criptomonedas y activos financieros.

![Captura de pantalla de la aplicación](https://github.com/tudor204/Echange-cripto/blob/main/app/images/index.png) <!-- Reemplaza con una imagen real de tu proyecto -->

## ✨ Características principales

- 📈 Registro detallado de transacciones de compra/venta
- 💰 Cálculo automático de balances y ganancias
- 📊 Visualización del estado actual de las inversiones
- 📤 Exportación de datos en formato PDF
- 🔍 Filtrado y búsqueda de transacciones históricas
- 📱 Diseño responsive para todos los dispositivos

(https://github.com/tudor204/Echange-cripto/blob/main/app/images/purchase.png)

## 🛠 Tecnologías utilizadas

- **Frontend**: HTML5, CSS3, JavaScript
- **Backend**: Python (Flask)
- **Base de datos**: SQLite
- **Librerías**: 
  - Pico.css (Framework CSS minimalista)
  - Google Fonts (Poppins y Roboto Mono)
- **Herramientas**: Git, GitHub

## 🚀 Instalación y configuración

1. Clona el repositorio:
   ```bash
   git clone https://github.com/tu-usuario/resumen-inversiones.git
   cd resumen-inversiones
Crea un entorno virtual (recomendado):

bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
Instala las dependencias:

bash
pip install -r requirements.txt
Configura las variables de entorno:

bash
cp .env.example .env
# Edita el archivo .env con tus configuraciones
Inicia la aplicación:

bash
flask run
Abre tu navegador en:

text
http://localhost:5000
📂 Estructura del proyecto
text
resumen-inversiones/
├── app.py                  # Aplicación principal Flask
├── config.py               # Configuraciones
├── requirements.txt        # Dependencias Python
├── static/                 # Archivos estáticos
│   ├── css/                # Hojas de estilo
│   └── js/                 # JavaScript
├── templates/              # Plantillas HTML
│   ├── base.html           # Plantilla base
│   ├── index.html          # Vista principal
│   ├── purchase.html       # Formulario de compra
│   └── status.html         # Estado de inversiones
└── database/               # Gestión de base de datos
    ├── models.py           # Modelos de datos
    └── queries.py          # Consultas SQL

(https://github.com/tudor204/Echange-cripto/blob/main/app/images/status.png)