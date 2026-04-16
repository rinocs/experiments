import requests
import pandas as pd

def get_historical_data(coin_id='bitcoin', days=1):
    """
    Fetches historical price data for a given cryptocurrency from the CoinGecko API.
    """
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {
        'vs_currency': 'usd',
        'days': days,
        'interval': 'daily'
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()

        # The API returns prices, market_caps, and total_volumes. We only need prices for pivot points.
        # We need to get the high, low, and close for the previous day.
        # The 'prices' data is a list of [timestamp, price]. We need OHLC data.
        # Let's adjust the API call to get OHLC data.

        url_ohlc = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc"
        params_ohlc = {
            'vs_currency': 'usd',
            'days': '1' # We need the previous day's data
        }

        response_ohlc = requests.get(url_ohlc, params=params_ohlc)
        response_ohlc.raise_for_status()
        ohlc_data = response_ohlc.json()

        # The last entry is the most recent (today's, which is incomplete). The second to last is yesterday's.
        if len(ohlc_data) > 1:
            previous_day_ohlc = ohlc_data[-2] # Yesterday's OHLC
            high = previous_day_ohlc[2]
            low = previous_day_ohlc[3]
            close = previous_day_ohlc[4]
            return high, low, close
        else:
            return None, None, None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from CoinGecko: {e}")
        return None, None, None

def calculate_pivot_points(coin_id='bitcoin'):
    """
    Calculates pivot points for a given cryptocurrency.
    """
    high, low, close = get_historical_data(coin_id)

    if high is None or low is None or close is None:
        return None

    pp = (high + low + close) / 3
    r1 = (2 * pp) - low
    s1 = (2 * pp) - high
    r2 = pp + (high - low)
    s2 = pp - (high - low)

    pivot_points = {
        'pp': pp,
        'r1': r1,
        's1': s1,
        'r2': r2,
        's2': s2
    }
    return pivot_points

if __name__ == '__main__':
    # Example usage
    btc_pivot_points = calculate_pivot_points('bitcoin')
    if btc_pivot_points:
        print("Bitcoin Pivot Points:")
        for k, v in btc_pivot_points.items():
            print(f"  {k.upper()}: {v:.2f}")

    eth_pivot_points = calculate_pivot_points('ethereum')
    if eth_pivot_points:
        print("\\nEthereum Pivot Points:")
        for k, v in eth_pivot_points.items():
            print(f"  {k.upper()}: {v:.2f}")
