import threading
import json
from src.data_collection import pivot_points, sentiment, news, technical_indicators
from src.llm_interface.llm_provider import MockLLMProvider # Start with the mock provider

class TradingAgent:
    def __init__(self, llm_provider):
        self.llm_provider = llm_provider
        self.market_data = {}

    def _collect_pivot_points(self, coin_id):
        self.market_data['pivot_points'] = pivot_points.calculate_pivot_points(coin_id)

    def _collect_sentiment(self):
        self.market_data['sentiment'] = sentiment.get_fear_and_greed_index()

    def _collect_news(self):
        self.market_data['news'] = news.get_crypto_news()

    def _collect_technical_indicators(self, coin_id):
        self.market_data['technical_indicators'] = technical_indicators.calculate_technical_indicators(coin_id)

    def collect_market_data(self, coin_id='bitcoin'):
        """
        Collects market data from all sources in parallel using threading.
        """
        self.market_data = {} # Reset data

        # Create threads for each data collection function
        pivot_thread = threading.Thread(target=self._collect_pivot_points, args=(coin_id,))
        sentiment_thread = threading.Thread(target=self._collect_sentiment)
        news_thread = threading.Thread(target=self._collect_news)
        indicators_thread = threading.Thread(target=self._collect_technical_indicators, args=(coin_id,))

        threads = [pivot_thread, sentiment_thread, news_thread, indicators_thread]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

    def format_prompt(self):
        """
        Formats the collected market data into a prompt for the LLM.
        """
        # Start with the base prompt
        prompt = """
You are a cryptocurrency trading agent with a $10,000 virtual portfolio.
Analyze the market and portfolio data provided.
Respond ONLY with a JSON object containing: operation (open/close/hold),
symbol, direction (long/short), target_position, leverage, and reasoning.

Here is the current market data:
"""
        # Add the collected data to the prompt
        for key, value in self.market_data.items():
            prompt += f"\\n--- {key.upper()} ---\\n"
            if value:
                if isinstance(value, dict):
                    # Handle the sentiment data which has a nested structure
                    if 'value' in value and 'value_classification' in value:
                         prompt += f"  Value: {value['value']}\\n"
                         prompt += f"  Classification: {value['value_classification']}\\n"
                    else:
                        for sub_key, sub_value in value.items():
                            prompt += f"  {sub_key}: {sub_value}\\n"
                elif isinstance(value, list):
                    for i, item in enumerate(value[:5]): # Limit news items to 5
                        prompt += f"  - {item.get('title', 'No Title')}\\n"
                else:
                    prompt += f"  {value}\\n"
            else:
                prompt += "  Data not available.\\n"

        return prompt

    def make_decision(self):
        """
        Makes a trading decision based on the market data.
        """
        prompt = self.format_prompt()
        decision_json = self.llm_provider.get_trading_decision(prompt)
        try:
            decision = json.loads(decision_json)
            return decision
        except json.JSONDecodeError as e:
            print(f"Error decoding LLM response: {e}")
            return None

if __name__ == '__main__':
    # Example usage
    mock_llm = MockLLMProvider()
    agent = TradingAgent(llm_provider=mock_llm)

    print("Collecting market data for Bitcoin...")
    agent.collect_market_data(coin_id='bitcoin')

    print("\\n--- Collected Market Data ---")
    # A simple way to pretty-print the collected data
    for key, value in agent.market_data.items():
        print(f"\\n--- {key.upper()} ---")
        if value:
            if isinstance(value, list):
                for item in value[:2]: # show first 2 news items
                    print(item)
            else:
                print(value)
        else:
            print("No data")
    print("-----------------------------\\n")

    print("Making a trading decision...")
    decision = agent.make_decision()

    if decision:
        print("\\n--- Trading Decision ---")
        print(json.dumps(decision, indent=2))
        print("------------------------")
