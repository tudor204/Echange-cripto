import requests

API_KEY = "1da147e1-614b-4a9d-864f-74bcbd0134b0"
from_currency = "BTC"
to_currency = "EUR"

url = f"https://rest.coinapi.io/v1/exchangerate/{from_currency}/{to_currency}"
headers = {'X-CoinAPI-Key': API_KEY}

response = requests.get(url, headers=headers)
if response.status_code == 200:
    data = response.json()
    print(f"Tasa de cambio {from_currency} a {to_currency}: {data.get('rate')}")
else:
    print(f"Error: {response.status_code} - {response.text}")
