from datetime import datetime
from flask import render_template, request, redirect, flash, Response
from app import app
from app.models import *
import requests
from config import CRYPTO_LIST

#Importaciones para PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO # Para manejar el PDF en memoria


@app.route("/download_pdf")
def download_pdf():
    # Obtener los registros de movimientos (la misma lógica que en la vista index)
    registros = select_all()

    # Configuración del PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()

    # Título
    title_style = styles['h2']
    title_style.alignment = 1 # Center
    title = Paragraph("Historial de Movimientos de Criptomonedas", title_style)

    # Preparar los datos para la tabla del PDF
    # Encabezados de la tabla
    data = [
        ["Fecha", "Hora", "Moneda usada", "Cantidad From", "Moneda Comprada", "Cantidad To", "Precio unidad"]
    ]
    # Añadir filas de datos
    for mov in registros:
        data.append([
            mov['Fecha'],
            mov['Hora'],
            mov['Moneda_From'],
            f"{mov['Cantidad_From']:.6f}", # Formato flotante
            mov['Moneda_To'],
            f"{mov['Cantidad_To']:.6f}",
            f"{mov['Precio_unitario']:.5f}"
        ])

    # Crear la tabla
    table = Table(data)

    # Estilo de la tabla
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3a86ff')), # Color de fondo del encabezado
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), # Color de texto del encabezado
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')), # Fondo alterno para filas de datos
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dddddd')), # Bordes de la tabla
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')), # Borde exterior de la tabla
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ])
    # Colores alternos para filas de datos (opcional, pero mejora la legibilidad)
    for i in range(1, len(data)):
        if i % 2 == 0: # Filas pares (contando desde la primera fila de datos como 1)
            table_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#ffffff'))
        else: # Filas impares
            table_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f0f0f0'))

    table.setStyle(table_style)

    # Construir el documento PDF
    elements = [title, Paragraph("<br/><br/>", styles['Normal']), table] # Añade espacio después del título
    doc.build(elements)

    # Regresar el PDF como una respuesta HTTP
    buffer.seek(0)
    return Response(buffer.getvalue(), mimetype='application/pdf',
                    headers={'Content-Disposition': 'attachment;filename=movimientos_cripto.pdf'})



@app.route("/")
def index():
    registros = select_all()
    return render_template("index.html", data=registros, iconos=ICONOS_CRIPTOS)



@app.route("/purchase", methods=["GET", "POST"])
def purchase():
    monedas_con_saldo = obtener_monedas_con_saldo()
    # Asegúrate de que EUR siempre esté disponible como opción "From" si no hay saldo de criptos
    monedas_from_display = ['EUR'] + [m for m in monedas_con_saldo if m != 'EUR']
    # Ahora, todas las criptos de CRYPTO_LIST (que incluye EUR) son opciones válidas para 'To'
    todas_las_criptos_disponibles = CRYPTO_LIST

    # --- Inicializar variables que podrían no existir ---
    cantidad_to = None
    tasa_cambio = None
    moneda_from = request.form.get("from_currency") if request.method == "POST" else None
    moneda_to = request.form.get("to_currency") if request.method == "POST" else None
    cantidad_from = float(request.form.get("amount", 0)) if request.method == "POST" else None
    # --- Fin de inicialización ---

    if request.method == "POST":
        accion = request.form.get("accion")
        moneda_from = request.form.get("from_currency")
        moneda_to = request.form.get("to_currency")

        try:
            cantidad_from = float(request.form.get("amount", 0))
        except ValueError:
            flash("Cantidad inválida. Por favor, introduce un número válido.", "error")
            return render_template("purchase.html",
                monedas_from=monedas_from_display,
                todas_criptos=todas_las_criptos_disponibles,
                moneda_from=moneda_from,
                moneda_to=moneda_to,
                cantidad_from=cantidad_from,
                cantidad_to=cantidad_to,
                tasa_cambio=tasa_cambio,
                accion='inicio'
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
                cantidad_to=cantidad_to,
                tasa_cambio=tasa_cambio,
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
                cantidad_to=cantidad_to,
                tasa_cambio=tasa_cambio,
                accion='inicio'
            )

        # Acción: calcular tasa
        if accion == "calcular":
            url = f"https://rest.coinapi.io/v1/exchangerate/{moneda_from}/{moneda_to}"
            headers = {'X-CoinAPI-Key': COINAPI_KEY}
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                tasa_cambio = data.get("rate")
                if not tasa_cambio:
                    flash("No se pudo obtener la tasa de cambio para esta operación.", "error")
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

                cantidad_to = cantidad_from * tasa_cambio

                return render_template("purchase.html",
                    monedas_from=monedas_from_display,
                    todas_criptos=todas_las_criptos_disponibles,
                    moneda_from=moneda_from,
                    moneda_to=moneda_to,
                    cantidad_from=cantidad_from,
                    cantidad_to=cantidad_to,
                    tasa_cambio=tasa_cambio,
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
            # Si Moneda_From es EUR, no necesitamos verificar el saldo
            if moneda_from != "EUR":
                saldo = calcular_saldo(moneda_from)
                cantidad_to = float(request.form.get("cantidad_to", 0))
                tasa_cambio = float(request.form.get("tasa_cambio_oculto", 0))

                if saldo < cantidad_from:
                    flash(f"Saldo insuficiente. Disponible: {saldo:.6f} {moneda_from}. No puedes operar con más de lo que posees.", "error")
                    return render_template("purchase.html",
                        monedas_from=monedas_from_display,
                        todas_criptos=todas_las_criptos_disponibles,
                        moneda_from=moneda_from,
                        moneda_to=moneda_to,
                        cantidad_from=cantidad_from,
                        cantidad_to=cantidad_to,
                        tasa_cambio=tasa_cambio,
                        accion='calcular'
                    )

            # Para que la cantidad_to y tasa_cambio estén siempre definidas para el insert
            cantidad_to = float(request.form.get("cantidad_to", 0))
            tasa_cambio = float(request.form.get("tasa_cambio_oculto", 0))

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
        moneda_from=moneda_from if moneda_from else 'EUR',
        moneda_to=moneda_to if moneda_to else 'BTC', # Se mantiene BTC como default si no hay selección previa
        cantidad_from=cantidad_from,
        cantidad_to=cantidad_to,
        tasa_cambio=tasa_cambio,
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