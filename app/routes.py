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
    monedas_from_display = ['EUR'] + [m for m in monedas_con_saldo if m != 'EUR']
    todas_las_criptos_disponibles = CRYPTO_LIST

    # --- Inicializar variables que podrían no existir ---
    cantidad_to = None # O 0.0, dependiendo de cómo quieras mostrarlo
    tasa_cambio = None # O 0.0
    moneda_from = request.form.get("from_currency") if request.method == "POST" else None
    moneda_to = request.form.get("to_currency") if request.method == "POST" else None
    cantidad_from = float(request.form.get("amount", 0)) if request.method == "POST" else None
    # --- Fin de inicialización ---

    if request.method == "POST":
        accion = request.form.get("accion")
        moneda_from = request.form.get("from_currency") # Reasignar si es POST
        moneda_to = request.form.get("to_currency")     # Reasignar si es POST

        try:
            cantidad_from = float(request.form.get("amount", 0))
        except ValueError:
            flash("Cantidad inválida. Por favor, introduce un número válido.", "error")
            # En caso de error, renderizar con los datos disponibles
            return render_template("purchase.html",
                monedas_from=monedas_from_display,
                todas_criptos=todas_las_criptos_disponibles,
                moneda_from=moneda_from, # Mantener la selección inválida
                moneda_to=moneda_to,     # Mantener la selección inválida
                cantidad_from=cantidad_from,
                cantidad_to=cantidad_to, # Será None/0
                tasa_cambio=tasa_cambio, # Será None/0
                accion='inicio' # O 'calcular' si venía de un cálculo previo
            )

        # Validaciones de combinaciones no permitidas (estas se mantienen)
        if moneda_from == moneda_to:
            flash("No puedes operar con la misma criptomoneda como origen y destino. Selecciona monedas diferentes.", "error")
            return render_template("purchase.html",
                monedas_from=monedas_from_display,
                todas_criptos=todas_las_criptos_disponibles,
                moneda_from=moneda_from,
                moneda_to=moneda_to,
                cantidad_from=cantidad_from,
                cantidad_to=cantidad_to, # Será None/0
                tasa_cambio=tasa_cambio, # Será None/0
                accion='inicio'
            )

        if moneda_from == "EUR" and moneda_to != "BTC":
            flash("Para comprar criptomonedas con euros, solo puedes adquirir Bitcoin (BTC) directamente. Si deseas otra criptomoneda, te recomendamos comprar BTC y luego intercambiarlo.", "error")
            return render_template("purchase.html",
                monedas_from=monedas_from_display,
                todas_criptos=todas_las_criptos_disponibles,
                moneda_from=moneda_from,
                moneda_to=moneda_to,
                cantidad_from=cantidad_from,
                cantidad_to=cantidad_to, # Será None/0
                tasa_cambio=tasa_cambio, # Será None/0
                accion='inicio'
            )

        if moneda_from != "EUR" and moneda_to == "EUR" and moneda_from != "BTC":
            flash(f"Operación no permitida: No puedes vender {moneda_from} directamente a EUR. Nuestro sistema requiere que todas las ventas a Euros se realicen desde Bitcoin (BTC). Por favor, convierte tus {moneda_from} a BTC primero.", "error")
            return render_template("purchase.html",
                monedas_from=monedas_from_display,
                todas_criptos=todas_las_criptos_disponibles,
                moneda_from=moneda_from,
                moneda_to=moneda_to,
                cantidad_from=cantidad_from,
                cantidad_to=cantidad_to, # Será None/0
                tasa_cambio=tasa_cambio, # Será None/0
                accion='inicio'
            )

        if moneda_from not in monedas_from_display or moneda_to not in todas_las_criptos_disponibles:
            flash("La combinación seleccionada no está permitida. Revisa las opciones disponibles.", "error")
            return render_template("purchase.html",
                monedas_from=monedas_from_display,
                todas_criptos=todas_las_criptos_disponibles,
                moneda_from=moneda_from,
                moneda_to=moneda_to,
                cantidad_from=cantidad_from,
                cantidad_to=cantidad_to, # Será None/0
                tasa_cambio=tasa_cambio, # Será None/0
                accion='inicio'
            )

        # Acción: calcular tasa
        if accion == "calcular":
            url = f"https://rest.coinapi.io/v1/exchangerate/{moneda_from}/{moneda_to}"
            headers = {'X-CoinAPI-Key': COINAPI_KEY}
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                tasa_cambio = data.get("rate") # Ahora tasa_cambio se asigna aquí
                if not tasa_cambio:
                    flash("No se pudo obtener la tasa de cambio para esta operación.", "error")
                    return render_template("purchase.html",
                        monedas_from=monedas_from_display,
                        todas_criptos=todas_las_criptos_disponibles,
                        moneda_from=moneda_from,
                        moneda_to=moneda_to,
                        cantidad_from=cantidad_from,
                        cantidad_to=None, # Resetear o mantener None si no se calculó
                        tasa_cambio=None, # Resetear o mantener None si no se calculó
                        accion='inicio'
                    )

                cantidad_to = cantidad_from * tasa_cambio # Ahora cantidad_to se asigna aquí

                return render_template("purchase.html",
                    monedas_from=monedas_from_display,
                    todas_criptos=todas_las_criptos_disponibles,
                    moneda_from=moneda_from,
                    moneda_to=moneda_to,
                    cantidad_from=cantidad_from,
                    cantidad_to=cantidad_to, # Ahora definida
                    tasa_cambio=tasa_cambio, # Ahora definida
                    accion='calcular'
                )
            else:
                flash(f"Error al consultar la API de tasas de cambio: {response.status_code}. Inténtalo de nuevo más tarde.", "error")
                return render_template("purchase.html",
                    monedas_from=monedas_from_display,
                    todas_criptos=todas_las_criptos_disponibles,
                    moneda_from=moneda_from,
                    moneda_to=moneda_to,
                    cantidad_from=cantidad_from,
                    cantidad_to=None,
                    tasa_cambio=None,
                    accion='inicio'
                )

        # Acción: validar y guardar operación
        elif accion == "validar":
            if moneda_from != "EUR":
                saldo = calcular_saldo(moneda_from)
                # routes.py (dentro de elif accion == "validar":)

# ... (tu código anterior) ...

                cantidad_to = float(request.form.get("cantidad_to", 0))
                # Recuperar la tasa_cambio del campo oculto. Si no está (ej. validación inicial GET), usa None o 0.0
                tasa_cambio = float(request.form.get("tasa_cambio_oculto", 0)) # Asegurarse de que sea float


                if moneda_from != "EUR":
                    saldo = calcular_saldo(moneda_from)
                    # cantidad_to ya se obtuvo de request.form.get("cantidad_to", 0)

                    if saldo < cantidad_from:
                        flash(f"Saldo insuficiente. Disponible: {saldo:.6f} {moneda_from}. No puedes operar con más de lo que posees.", "error")
                        return render_template("purchase.html",
                            monedas_from=monedas_from_display,
                            todas_criptos=todas_las_criptos_disponibles,
                            moneda_from=moneda_from,
                            moneda_to=moneda_to,
                            cantidad_from=cantidad_from,
                            cantidad_to=cantidad_to, # Ahora definida
                            tasa_cambio=tasa_cambio, # ¡Ahora definida y recuperada del formulario!
                            accion='calcular' # Mantener el estado 'calcular'
                        )


                

            cantidad_to = float(request.form.get("cantidad_to", 0)) # Obtener cantidad_to del campo oculto

            fecha_actual = datetime.now().strftime("%Y-%m-%d")
            hora_actual = datetime.now().strftime("%H:%M:%S")

            precio_unitario = cantidad_from / cantidad_to if cantidad_to != 0 else 0

            insert_movimiento(
                fecha_actual,
                hora_actual,
                moneda_from,
                cantidad_from,
                moneda_to,
                cantidad_to,
                precio_unitario
            )

            flash("Operación registrada correctamente. ¡Éxito!", "success")
            return redirect("/")

    # GET o cualquier otro caso donde no se haya hecho un POST 'calcular' o 'validar' exitoso
    return render_template("purchase.html",
        monedas_from=monedas_from_display,
        todas_criptos=todas_las_criptos_disponibles,
        moneda_from=moneda_from if moneda_from else 'EUR', # Si es GET, selecciona EUR por defecto
        moneda_to=moneda_to if moneda_to else 'BTC', # Si es GET, selecciona BTC por defecto
        cantidad_from=cantidad_from,
        cantidad_to=cantidad_to, # Será None/0
        tasa_cambio=tasa_cambio, # Será None/0
        accion='inicio'
    )



@app.route("/status")
def status():
    # 1. Invertido = suma de Cantidad_From donde Moneda_From = EUR
    invertido = total_euros_invertidos()

    # 2. Recuperado = suma de Cantidad_To donde Moneda_To = EUR (CORRECCIÓN CLAVE)
    con = Conexion("""
        SELECT SUM(Cantidad_To) as total
        FROM criptomonedas
        WHERE Moneda_To = 'EUR'
    """)
    recuperado = con.res.fetchone()[0] or 0  # Si es None, usa 0
    con.close()

    # 3. Valor de compra = invertido - recuperado
    valor_compra = invertido - recuperado

    # 4. Valor actual (sin cambios, está correcto)
    monedas = [m for m in obtener_monedas_con_saldo() if m != "EUR"]
    saldo_por_moneda = {m: calcular_saldo(m) for m in monedas}
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