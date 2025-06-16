from datetime import datetime
from flask import render_template, request, redirect, flash
from app import app
from app.models import *
import requests


@app.route("/")
def index():
    registros = select_all()
    return render_template("index.html", data=registros, iconos=ICONOS_CRIPTOS)

@app.route("/purchase", methods=["GET", "POST"])
def purchase():
    monedas_con_saldo = obtener_monedas_con_saldo()
    todas_criptos = obtener_todas_criptomonedas()

    if not monedas_con_saldo:
        monedas_from = ['EUR']
        monedas_to = ['BTC']  # Solo permitir BTC si no hay saldo
    else:
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

        # ✅ Validar combinaciones permitidas
        if moneda_from == "EUR":
            if moneda_to != "BTC":
                flash("Solo puedes comprar BTC con euros", "error")
                return redirect("/purchase")
        elif moneda_from == "BTC":
            # BTC → EUR o BTC → otra cripto está permitido
            pass
        elif moneda_from != "EUR":
            if moneda_to == "EUR":
                flash("No puedes vender otras criptomonedas por euros directamente", "error")
                return redirect("/purchase")
        else:
            flash("Combinación no permitida", "error")
            return redirect("/purchase")

        if accion == "calcular":
            url = f"https://rest.coinapi.io/v1/exchangerate/{moneda_from}/{moneda_to}"
            headers = {'X-CoinAPI-Key': COINAPI_KEY}
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                tasa_cambio = data.get("rate")
                if not tasa_cambio:
                    flash("No se pudo obtener la tasa", "error")
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
                flash(f"Error API: {response.status_code}", "error")
                return redirect("/purchase")

        elif accion == "validar":
            if moneda_from != "EUR":
                saldo = calcular_saldo(moneda_from)
                if saldo < cantidad_from:
                    flash(f"Saldo insuficiente. Disponible: {saldo:.6f}", "error")
                    return redirect("/purchase")

            cantidad_to = float(request.form.get("cantidad_to", 0))
            fecha_actual = datetime.now().strftime("%Y-%m-%d")
            hora_actual = datetime.now().strftime("%H:%M:%S")
            insert_movimiento(fecha_actual, hora_actual, moneda_from, cantidad_from, moneda_to, cantidad_to)
            flash("Operación registrada", "success")
            return redirect("/")

    return render_template("purchase.html",
        monedas_from=monedas_from,
        monedas_to=monedas_to,
        accion='inicio'
    )


@app.route("/status")
def status():
    # 1. Invertido = suma de Cantidad_From donde Moneda_From = EUR
    invertido = total_euros_invertidos()

    # 2. Recuperado = suma de Cantidad_To donde Moneda_To = EUR
    recuperado = calcular_beneficio() + invertido  # ya tienes ventas - invertido = beneficio
    # Por tanto recuperado = beneficio + invertido = recuperado total

    # 3. Valor de compra = invertido - recuperado
    valor_compra = invertido - recuperado

    # 4. Calcular saldo por cripto
    monedas = [m for m in obtener_monedas_con_saldo() if m != "EUR"]
    saldo_por_moneda = {m: calcular_saldo(m) for m in monedas}

    # 5. Obtener valor actual en EUR por cada cripto
    total_actual = 0
    cripto_valores = {}
    for m, saldo in saldo_por_moneda.items():
        url = f"https://rest.coinapi.io/v1/exchangerate/{m}/EUR"
        headers = {'X-CoinAPI-Key': COINAPI_KEY}
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200:
            tasa = resp.json().get("rate", 0)
            euros = saldo * tasa
        else:
            tasa = 0
            euros = 0
        cripto_valores[m] = {"saldo": saldo, "tasa": tasa, "euros": euros}
        total_actual += euros

    ganancia_perdida = total_actual - valor_compra

    return render_template("status.html",
        invertido=invertido,
        recuperado=recuperado,
        valor_compra=valor_compra,
        cripto_valores=cripto_valores,
        total_actual=total_actual,
        ganancia_perdida=ganancia_perdida
    )
