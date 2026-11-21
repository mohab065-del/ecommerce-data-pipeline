import requests
import pandas as pd

API_URL = "https://api.frankfurter.dev/v2/rates"


def fetch_exchange_rates(base_currency="BRL", quote_currency="USD", start_year=2016, end_date=None):
    end = pd.Timestamp(end_date) if end_date else pd.Timestamp.today().normalize()
    frames = []

    for year in range(start_year, end.year + 1):
        range_end = min(pd.Timestamp(f"{year}-12-31"), end)
        params = {
            "base": base_currency,
            "quotes": quote_currency,
            "from": f"{year}-01-01",
            "to": range_end.strftime("%Y-%m-%d"),
        }
        response = requests.get(API_URL, params=params, timeout=30)
        response.raise_for_status()
        frames.append(pd.DataFrame(response.json()))

        df = pd.concat(frames, ignore_index=True)
    return df.drop_duplicates(subset=["date", "base", "quote"])


if __name__ == "__main__":
    exchange_rates = fetch_exchange_rates()
    print(exchange_rates.shape)
    print(exchange_rates.head())
    print(exchange_rates.tail())