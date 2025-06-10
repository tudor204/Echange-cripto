import os
from dotenv import load_dotenv
from flask import Flask

load_dotenv()  # Carga variables del .env

app= Flask(__name__)
app.secret_key = os.urandom(24)  # Para usar flash()

COINAPI_KEY = os.getenv("COINAPI_KEY")
ORIGIN_DATA="data/cripto.sqlite"

if not COINAPI_KEY:
    raise ValueError("La variable COINAPI_KEY no está definida en .env")



from app.routes import * 