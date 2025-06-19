from datetime import datetime
from flask import render_template, request, redirect, flash, Response
from app import app
from app.models import *
import requests
from config import CRYPTO_LIST

# Importaciones para PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
from reportlab.lib import colors as reportlab_colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import matplotlib 
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

@app.route("/download_pdf")
def download_pdf():
    # Obtener los registros de movimientos
    registros = select_all()
    
    # Obtener datos para los gráficos
    invertido = total_euros_invertidos()
    con = Conexion("SELECT SUM(Cantidad_To) as total FROM criptomonedas WHERE Moneda_To = 'EUR'")
    recuperado = con.res.fetchone()[0] or 0
    con.close()
    valor_compra = invertido - recuperado
    
    monedas = [m for m in obtener_monedas_con_saldo() if m != "EUR"]
    saldo_por_moneda = {m: calcular_saldo(m) for m in monedas}
    total_actual = 0
    cripto_valores = {}
    
    for m, saldo in saldo_por_moneda.items():
        url = f"https://rest.coinapi.io/v1/exchangerate/{m}/EUR"
        headers = {'X-CoinAPI-Key': COINAPI_KEY}
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                tasa = resp.json().get("rate", 0)
                euros = saldo * tasa
            else:
                tasa = 0
                euros = 0
            cripto_valores[m] = {"saldo": saldo, "tasa": tasa, "euros": euros}
            total_actual += euros
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Error API CoinAPI para {m}: {str(e)}")
            cripto_valores[m] = {"saldo": saldo, "tasa": 0, "euros": 0}
    
    # Datos para gráficos
    meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun']
    historial = [
        invertido * 0.8,
        invertido * 0.9,
        invertido,
        total_actual * 0.9,
        total_actual * 0.95,
        total_actual
    ]
    
    # Crear gráficos con matplotlib
    # Gráfico de evolución
    fig1, ax1 = plt.subplots(figsize=(8, 4))
    ax1.plot(meses, historial, marker='o', color='#4bc0c0')
    ax1.set_title('Evolución de la Inversión', pad=20)
    ax1.set_ylabel('EUR')
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.fill_between(meses, historial, color=(75/255, 192/255, 192/255, 0.1))
    buf1 = BytesIO()
    plt.savefig(buf1, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig1)
    buf1.seek(0)
    
    # Gráfico de distribución
    labels = list(cripto_valores.keys())
    sizes = [v['euros'] for v in cripto_valores.values()]
    fig2, ax2 = plt.subplots(figsize=(8, 4))
    pie_colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']
    ax2.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,
           colors=pie_colors)
    ax2.axis('equal')
    ax2.set_title('Distribución de la Cartera', pad=20)
    buf2 = BytesIO()
    plt.savefig(buf2, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig2)
    buf2.seek(0)
    
    # Configuración del PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Contenido del PDF
    elements = []
    
    # Título principal
    title_style = styles['h2']
    title_style.alignment = 1
    elements.append(Paragraph("Informe Completo de Inversiones", title_style))
    elements.append(Spacer(1, 24))
    
    # Sección de resumen
    elements.append(Paragraph("Resumen de Inversión", styles['h3']))
    
    # Datos del resumen
    summary_data = [
        ["Invertido:", f"{invertido:,.2f} EUR"],
        ["Recuperado:", f"{recuperado:,.2f} EUR"],
        ["Valor de compra:", f"{valor_compra:,.2f} EUR"],
        ["Valor actual:", f"{total_actual:,.2f} EUR"],
        ["Ganancia/Pérdida:", f"{total_actual - valor_compra:,.2f} EUR"]
    ]
    
    summary_table = Table(summary_data, colWidths=[200, 100])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 24))
    
    # Gráficos
    elements.append(Paragraph("Gráficos de Inversión", styles['h3']))
    elements.append(Spacer(1, 12))
    
    # Añadir gráficos al PDF
    img1 = Image(buf1, width=400, height=200)
    elements.append(img1)
    elements.append(Spacer(1, 24))
    
    img2 = Image(buf2, width=400, height=200)
    elements.append(img2)
    elements.append(Spacer(1, 24))
    
    # Detalle de criptomonedas
    elements.append(Paragraph("Detalle de Criptomonedas", styles['h3']))
    crypto_data = [["Moneda", "Saldo", "Precio (EUR)", "Valor (EUR)"]] + [
        [m, f"{info['saldo']:.6f}", f"{info['tasa']:.2f}", f"{info['euros']:.2f}"]
        for m, info in cripto_valores.items()
    ]
    crypto_table = Table(crypto_data)
    crypto_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), reportlab_colors.HexColor('#3a86ff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), reportlab_colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), reportlab_colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 1, reportlab_colors.HexColor('#dddddd')),
    ]))
    elements.append(crypto_table)
    elements.append(Spacer(1, 24))
    
    # Movimientos
    elements.append(Paragraph("Historial de Movimientos", styles['h3']))
    
    # Preparar los datos para la tabla de movimientos
    mov_data = [
        ["Fecha", "Hora", "Moneda usada", "Cantidad From", "Moneda Comprada", "Cantidad To", "Precio unidad"]
    ]
    for mov in registros:
        mov_data.append([
            mov['Fecha'],
            mov['Hora'],
            mov['Moneda_From'],
            f"{mov['Cantidad_From']:.6f}",
            mov['Moneda_To'],
            f"{mov['Cantidad_To']:.6f}",
            f"{mov['Precio_unitario']:.5f}"
        ])
    
    mov_table = Table(mov_data)
    mov_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), reportlab_colors.HexColor('#3a86ff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), reportlab_colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), reportlab_colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 1, reportlab_colors.HexColor('#dddddd')),
        ('BOX', (0, 0), (-1, -1), 1, reportlab_colors.HexColor('#cccccc')),
    ]))
    
    # Alternar colores de fila
    for i in range(1, len(mov_data)):
        if i % 2 == 0:
            mov_table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), reportlab_colors.HexColor('#ffffff'))]))
        else:
            mov_table.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), reportlab_colors.HexColor('#f0f0f0'))]))
    
    elements.append(mov_table)
    
    # Construir el documento PDF
    doc.build(elements)
    
    # Regresar el PDF como una respuesta HTTP
    buffer.seek(0)
    return Response(buffer.getvalue(), mimetype='application/pdf',
                    headers={'Content-Disposition': 'attachment;filename=informe_completo_inversiones.pdf'})


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

        # Validaciones de combinaciones no permitidas 
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
        moneda_to=moneda_to if moneda_to else 'BTC', 
        cantidad_from=cantidad_from,
        cantidad_to=cantidad_to,
        tasa_cambio=tasa_cambio,
        accion='inicio'
    )

@app.route("/status")
def status():
    try:
        # 1. Cálculo de inversión 
        invertido = total_euros_invertidos()

        con = Conexion("""
            SELECT SUM(Cantidad_To) as total
            FROM criptomonedas
            WHERE Moneda_To = 'EUR'
        """)
        recuperado = con.res.fetchone()[0] or 0
        con.close()

        valor_compra = invertido - recuperado

        # 2. Valor actual de las criptomonedas
        monedas = [m for m in obtener_monedas_con_saldo() if m != "EUR"]
        saldo_por_moneda = {m: calcular_saldo(m) for m in monedas}
        total_actual = 0
        cripto_valores = {}
        
        for m, saldo in saldo_por_moneda.items():
            url = f"https://rest.coinapi.io/v1/exchangerate/{m}/EUR"
            headers = {'X-CoinAPI-Key': COINAPI_KEY}
            try:
                resp = requests.get(url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    tasa = resp.json().get("rate", 0)
                    euros = saldo * tasa
                else:
                    tasa = 0
                    euros = 0
                cripto_valores[m] = {"saldo": saldo, "tasa": tasa, "euros": euros}
                total_actual += euros
            except requests.exceptions.RequestException as e:
                app.logger.error(f"Error API CoinAPI para {m}: {str(e)}")
                cripto_valores[m] = {"saldo": saldo, "tasa": 0, "euros": 0}

        ganancia_perdida = total_actual - valor_compra

        # 3. Datos para gráfico histórico 
        meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun']
        historial = [
            invertido * 0.8,  # Simulación mes 1
            invertido * 0.9,  # Simulación mes 2
            invertido,         # Mes 3
            total_actual * 0.9, # Mes 4
            total_actual * 0.95, # Mes 5
            total_actual       # Mes actual
        ]

        return render_template("status.html",
            invertido=invertido,
            recuperado=recuperado,
            valor_compra=valor_compra,
            cripto_valores=cripto_valores,
            total_actual=total_actual,
            ganancia_perdida=ganancia_perdida,
            historial=historial,
            meses=meses
        )

    except Exception as e:
        app.logger.error(f"Error en /status: {str(e)}")
        flash("Error al calcular el estado de la inversión", "error")
        return redirect("/")