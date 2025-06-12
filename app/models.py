import requests
from .conexion import Conexion
from app import COINAPI_KEY


def select_all():
    con = Conexion(
        "SELECT * FROM criptomonedas ORDER BY Fecha DESC, Hora DESC"
    )
    rows = con.fetch_all()
    con.close()
    return rows


def insert_movimiento(fecha, hora, moneda_from, cantidad_from, moneda_to, cantidad_to):
    con = Conexion(
        """INSERT INTO criptomonedas 
           (Fecha, Hora, Moneda_From, Cantidad_From, Moneda_To, Cantidad_To)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (fecha, hora, moneda_from, cantidad_from, moneda_to, cantidad_to)
    )
    con.close()


def calcular_saldo(moneda):
    con = Conexion(
        """SELECT
             SUM(CASE WHEN Moneda_To = ? THEN Cantidad_To ELSE 0 END) -
             SUM(CASE WHEN Moneda_From = ? THEN Cantidad_From ELSE 0 END) AS Saldo
           FROM criptomonedas""",
        (moneda, moneda)
    )
    saldo = con.res.fetchone()[0] or 0
    con.close()
    return saldo


def obtener_monedas_con_saldo():
    con = Conexion("""
        SELECT moneda FROM (
            SELECT Moneda_To as moneda, 
                   SUM(Cantidad_To) - 
                   COALESCE((SELECT SUM(Cantidad_From) FROM criptomonedas WHERE Moneda_From = Moneda_To), 0) AS saldo
            FROM criptomonedas
            GROUP BY Moneda_To
        )
        WHERE saldo > 0
    """)
    resultados = con.fetch_all()
    con.close()
    # Ajustar extracción para lista de diccionarios o tuplas:
    monedas = [row['moneda'] if isinstance(row, dict) else row[0] for row in resultados]

    # Aseguramos que 'EUR' siempre esté en la lista y al inicio
    if "EUR" not in monedas:
        monedas.insert(0, "EUR")
    else:
        # Lo movemos al inicio si está en otra posición
        monedas = ["EUR"] + [m for m in monedas if m != "EUR"]
    return monedas

def obtener_todas_criptomonedas():
    # Lista fija o dinámica, aquí un ejemplo fijo de 20 monedas + EUR
    return ['BTC', 'ETH', 'BNB', 'USDT', 'ADA', 'SOL', 'XRP', 'DOT', 'LTC', 'DOGE', 
            'AVAX', 'SHIB', 'MATIC', 'TRX', 'UNI', 'ATOM', 'LINK', 'XLM', 'BCH', 'VET', 'EUR']


