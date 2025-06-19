import os
CRYPTO_LIST = [
    'BTC', 'ETH', 'BNB', 'USDT', 'ADA', 'SOL', 'XRP', 'DOT', 'LTC', 'DOGE',
    'AVAX', 'SHIB', 'MATIC', 'TRX', 'UNI', 'ATOM', 'LINK', 'XLM', 'BCH', 'VET', 'EUR'
]

ICONOS_CRIPTOS = {
    'BTC': 'btc.svg', 'ETH': 'eth.svg', 'USDT': 'usdt.svg', 'BNB': 'bnb.svg',
    'ADA': 'ada.svg', 'XRP': 'xrp.svg', 'SOL': 'sol.svg', 'DOT': 'dot.svg',
    'DOGE': 'doge.svg', 'LTC': 'ltc.svg', 'AVAX': 'avax.svg', 'SHIB': 'shib.svg',
    'LINK': 'link.svg', 'MATIC': 'matic.svg', 'UNI': 'uni.svg', 'XLM': 'xlm.svg',
    'ATOM': 'atom.svg', 'ETC': 'etc.svg', 'TRX': 'trx.svg', 'EUR': 'eur.svg'
}

API_BASE_URL = "https://rest.coinapi.io/v1/exchangerate"
API_TIMEOUT = 5 # segundos

COINAPI_KEY = os.getenv("COINAPI_KEY")
ORIGIN_DATA="data/cripto.sqlite"