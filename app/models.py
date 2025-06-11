import requests
from .conexion import Conexion
from app import COINAPI_KEY

def get_exchange_rate(from_currency, to_currency):
    url = f"https://rest.coinapi.io/v1/exchangerate/{from_currency}/{to_currency}"
    headers = {'X-CoinAPI-Key': COINAPI_KEY}
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 200:
        return response.json().get('rate', 0)
    return 0

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


def get_top_cryptos(limit=20):
    url = "https://rest.coinapi.io/v1/assets"
    headers = {'X-CoinAPI-Key': COINAPI_KEY}
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        # Filtrar solo cripto y con precio_usd definido
        crypto = [a for a in data if a.get('type_is_crypto') == 1 and a.get('price_usd')]
        # Ordenar por volumen diario en USD (mayor a menor)
        crypto_sorted = sorted(
            crypto,
            key=lambda x: float(x.get('volume_1day_usd', 0)),
            reverse=True
        )
        return [a['asset_id'] for a in crypto_sorted[:limit]]
    return ['BTC', 'ETH', 'USDT', 'BNB', 'XRP']  # fallback