from datetime import date
from app import app
from flask import render_template,request,redirect
from app.models import *



@app.route("/")
def index():

    registros= select_all()
    
    return render_template("index.html",data=registros)