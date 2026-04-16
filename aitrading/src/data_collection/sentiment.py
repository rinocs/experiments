import requests

def get_fear_and_greed_index():
    """
    Fetches the current Fear and Greed Index from alternative.me.
    """
    url = "https://api.alternative.me/fng/"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        # The data is in a list, so we take the first element
        if data['data']:
            return data['data'][0]
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Fear and Greed Index: {e}")
        return None

if __name__ == '__main__':
    # Example usage
    fng_data = get_fear_and_greed_index()
    if fng_data:
        print("Fear and Greed Index:")
        print(f"  Value: {fng_data['value']}")
        print(f"  Classification: {fng_data['value_classification']}")
        print(f"  Last Updated: {fng_data['timestamp']}")
