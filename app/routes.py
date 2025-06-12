from datetime import datetime
from flask import render_template, request, redirect, flash
from app import app
from app.models import *
import requests

# Diccionario de iconos
ICONOS_CRIPTOS = {
    'BTC': 'btc.svg', 'ETH': 'eth.svg', 'USDT': 'usdt.svg', 'BNB': 'bnb.svg',
    'ADA': 'ada.svg', 'XRP': 'xrp.svg', 'SOL': 'sol.svg', 'DOT': 'dot.svg',
    'DOGE': 'doge.svg', 'LTC': 'ltc.svg', 'AVAX': 'avax.svg', 'SHIB': 'shib.svg',
    'LINK': 'link.svg', 'MATIC': 'matic.svg', 'UNI': 'uni.svg', 'XLM': 'xlm.svg',
    'ATOM': 'atom.svg', 'ETC': 'etc.svg', 'TRX': 'trx.svg', 'EUR': 'eur.svg'
}

API_KEY = "1da147e1-614b-4a9d-864f-74bcbd0134b0"
TOP_20_COINS = [coin for coin in ICONOS_CRIPTOS if coin != 'EUR']


@app.route("/")
def index():
    registros = select_all()
    return render_template("index.html", data=registros, iconos=ICONOS_CRIPTOS)



@app.route("/purchase", methods=["GET", "POST"])
def purchase():
    monedas_con_saldo = obtener_monedas_con_saldo()  # Solo monedas con saldo > 0
    todas_criptos = obtener_todas_criptomonedas()

    # Si no hay ninguna moneda con saldo (tabla vacía), moneda_from solo EUR
    if not monedas_con_saldo:
        monedas_from = ['EUR']
        monedas_to = [c for c in todas_criptos if c != 'EUR']  # todas menos EUR para comprar
    else:
        # Con movimientos: moneda_from = EUR + monedas con saldo
        monedas_from = ['EUR'] + [m for m in monedas_con_saldo if m != 'EUR']
        monedas_to = ['EUR'] + [c for c in todas_criptos if c not in monedas_from]

    if request.method == "POST":
        accion = request.form.get("accion")

        moneda_from = request.form.get("from_currency")
        moneda_to = request.form.get("to_currency")
        try:
            cantidad_from = float(request.form.get("amount", 0))
        except ValueError:
            flash("Cantidad inválida", "error")
            return redirect("/purchase")

        if moneda_from not in monedas_from:
            flash(f"La moneda origen {moneda_from} no está disponible para operar.", "error")
            return redirect("/purchase")

        if accion == "calcular":
            # Consulta tasa de cambio CoinAPI
            url = f"https://rest.coinapi.io/v1/exchangerate/{moneda_from}/{moneda_to}"
            headers = {'X-CoinAPI-Key': API_KEY}
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                tasa_cambio = data.get("rate")
                if not tasa_cambio:
                    flash("No se pudo obtener la tasa de cambio.", "error")
                    return redirect("/purchase")

                cantidad_to = cantidad_from * tasa_cambio

                return render_template("purchase.html",
                    monedas_from=monedas_from,
                    monedas_to=monedas_to,
                    moneda_from=moneda_from,
                    moneda_to=moneda_to,
                    cantidad_from=cantidad_from,
                    cantidad_to=cantidad_to,
                    tasa_cambio=tasa_cambio,
                    accion='calcular'
                )
            else:
                flash(f"Error CoinAPI: {response.status_code}", "error")
                return redirect("/purchase")

        elif accion == "validar":
            if moneda_from != "EUR":
                saldo = calcular_saldo(moneda_from)
                if saldo < cantidad_from:
                    flash(f"Saldo insuficiente de {moneda_from}. Disponible: {saldo:.6f}", "error")
                    return redirect("/purchase")

            cantidad_to = float(request.form.get("cantidad_to", 0))
            fecha_actual = datetime.now().strftime("%Y-%m-%d")
            hora_actual = datetime.now().strftime("%H:%M:%S")
            insert_movimiento(fecha_actual, hora_actual, moneda_from, cantidad_from, moneda_to, cantidad_to)

            flash("Operación registrada con éxito", "success")
            return redirect("/")

    # GET o cualquier otro caso
    return render_template("purchase.html",
        monedas_from=monedas_from,
        monedas_to=monedas_to,
        accion='inicio'
    )



    



@app.route("/status")
def status():
    return render_template("status.html")
