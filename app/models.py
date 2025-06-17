import requests
from .conexion import Conexion
from app import COINAPI_KEY
from config import *

def select_all():
    con = Conexion("SELECT * FROM criptomonedas ORDER BY Fecha DESC, Hora DESC")
    rows = con.fetch_all()
    con.close()
    return rows

def insert_movimiento(fecha, hora, moneda_from, cantidad_from, moneda_to, cantidad_to, precio_unitario):
    con = Conexion(
        """INSERT INTO criptomonedas 
           (Fecha, Hora, Moneda_From, Cantidad_From, Moneda_To, Cantidad_To, Precio_unitario)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (fecha, hora, moneda_from, cantidad_from, moneda_to, cantidad_to, precio_unitario)
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
    monedas = [row['moneda'] if isinstance(row, dict) else row[0] for row in resultados]
    
    if "EUR" not in monedas:
        monedas.insert(0, "EUR")
    else:
        monedas = ["EUR"] + [m for m in monedas if m != "EUR"]
    return monedas

def obtener_todas_criptomonedas():
    return CRYPTO_LIST

def total_euros_invertidos():
    con = Conexion("""
        SELECT SUM(Cantidad_From)
        FROM criptomonedas
        WHERE Moneda_From = 'EUR'
    """)
    total = con.res.fetchone()[0] or 0
    con.close()
    return total

def calcular_ventas():
    con = Conexion("SELECT SUM(Cantidad_To) FROM criptomonedas WHERE Moneda_To = 'EUR'")
    ventas = con.res.fetchone()[0] or 0
    con.close()
    return ventas

def valor_total_en_euro():
    monedas = obtener_monedas_con_saldo()
    total = 0
    for moneda in monedas:
        if moneda != "EUR":
            url = f"https://rest.coinapi.io/v1/exchangerate/{moneda}/EUR"
            headers = {'X-CoinAPI-Key': COINAPI_KEY}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                tasa = response.json().get("rate", 0)
                total += calcular_saldo(moneda) * tasa
    return total