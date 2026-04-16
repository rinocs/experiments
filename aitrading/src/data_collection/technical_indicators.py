import requests
import pandas as pd
import pandas_ta as ta

def get_historical_ohlc_data(coin_id='bitcoin', days='365'):
    """
    Fetches historical OHLC data for a given cryptocurrency from the CoinGecko API.
    """
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc"
    params = {
        'vs_currency': 'usd',
        'days': days
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Convert to a pandas DataFrame
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df

    except requests.exceptions.RequestException as e:
        print(f"Error fetching OHLC data from CoinGecko: {e}")
        return None

def calculate_technical_indicators(coin_id='bitcoin'):
    """
    Calculates technical indicators for a given cryptocurrency.
    """
    df = get_historical_ohlc_data(coin_id)

    if df is None or df.empty:
        return None

    # Calculate indicators using pandas-ta
    df.ta.macd(append=True)
    df.ta.rsi(append=True)
    df.ta.ema(length=20, append=True)
    df.ta.sma(length=200, append=True)

    # Get the latest values, checking if columns exist
    latest_indicators = {
        'macd': df['MACD_12_26_9'].iloc[-1] if 'MACD_12_26_9' in df.columns and not pd.isna(df['MACD_12_26_9'].iloc[-1]) else None,
        'macd_signal': df['MACDs_12_26_9'].iloc[-1] if 'MACDs_12_26_9' in df.columns and not pd.isna(df['MACDs_12_26_9'].iloc[-1]) else None,
        'macd_hist': df['MACDh_12_26_9'].iloc[-1] if 'MACDh_12_26_9' in df.columns and not pd.isna(df['MACDh_12_26_9'].iloc[-1]) else None,
        'rsi': df['RSI_14'].iloc[-1] if 'RSI_14' in df.columns and not pd.isna(df['RSI_14'].iloc[-1]) else None,
        'ema20': df['EMA_20'].iloc[-1] if 'EMA_20' in df.columns and not pd.isna(df['EMA_20'].iloc[-1]) else None,
        'ma200': df['SMA_200'].iloc[-1] if 'SMA_200' in df.columns and not pd.isna(df['SMA_200'].iloc[-1]) else None
    }
    return latest_indicators

if __name__ == '__main__':
    # Example usage
    btc_indicators = calculate_technical_indicators('bitcoin')
    if btc_indicators:
        print("Bitcoin Technical Indicators:")
        for k, v in btc_indicators.items():
            # Check if v is not None before formatting
            if v is not None:
                print(f"  {k.upper()}: {v:.2f}")
            else:
                print(f"  {k.upper()}: Not available")

    eth_indicators = calculate_technical_indicators('ethereum')
    if eth_indicators:
        print("\\nEthereum Technical Indicators:")
        for k, v in eth_indicators.items():
            if v is not None:
                print(f"  {k.upper()}: {v:.2f}")
            else:
                print(f"  {k.upper()}: Not available")
