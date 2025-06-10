from flask import Flask

app= Flask(__name__)

app.config.from_object("config")



ORIGIN_DATA="data/cripto.sqlite"

from app.routes import * 