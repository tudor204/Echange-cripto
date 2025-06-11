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


