
import requests
import pandas as pd


def fetch_exchange_rates(base_currency="BRL", quote_currency="USD"):
    url = "https://api.frankfurter.dev/v2/rates"

    params = {
        "base": base_currency,
        "quotes": quote_currency
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    rates = response.json()

    df = pd.DataFrame(rates)

    return df


if __name__ == "__main__":
    exchange_rates = fetch_exchange_rates()

    print("Exchange Rates:")
    print(exchange_rates)
