from src.trading_agent import TradingAgent
from src.llm_interface.llm_provider import MockLLMProvider
import json
import time

def main():
    """
    Main function to run the AI trading agent.
    """
    # Initialize the LLM provider (using the mock provider for now)
    llm_provider = MockLLMProvider()

    # Initialize the trading agent
    agent = TradingAgent(llm_provider=llm_provider)

    # --- Configuration ---
    # In a real application, you would load this from a config file or environment variables
    COIN_TO_TRADE = 'bitcoin'
    TRADING_INTERVAL_SECONDS = 180 # 3 minutes, as mentioned in the video

    print("--- AI Trading Agent Initialized ---")
    print(f"Trading on: {COIN_TO_TRADE.capitalize()}")
    print(f"Trading interval: {TRADING_INTERVAL_SECONDS} seconds")
    print("------------------------------------")

    # Main trading loop
    try:
        while True:
            print(f"\\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] --- Starting new trading cycle ---")

            # 1. Collect market data
            print("Collecting market data...")
            agent.collect_market_data(coin_id=COIN_TO_TRADE)
            print("Market data collected.")

            # Optional: Display the collected data for debugging
            # print("\\n--- Collected Market Data ---")
            # for key, value in agent.market_data.items():
            #     print(f"\\n--- {key.upper()} ---")
            #     if value:
            #         if isinstance(value, list):
            #             for item in value[:2]: # show first 2 news items
            #                 print(item)
            #         else:
            #             print(value)
            #     else:
            #         print("No data")
            # print("-----------------------------\\n")

            # 2. Make a trading decision
            print("Making a trading decision...")
            decision = agent.make_decision()

            if decision:
                print("\\n--- Trading Decision ---")
                print(json.dumps(decision, indent=2))
                print("------------------------")

                # In a real application, you would add logic here to execute the trade
                # on the Hyperliquid testnet.
                # e.g., execute_trade(decision)

            else:
                print("Could not make a trading decision in this cycle.")

            # 3. Wait for the next trading interval
            print(f"\\n--- Cycle complete. Waiting for {TRADING_INTERVAL_SECONDS} seconds... ---")
            time.sleep(TRADING_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\\n--- Trading agent stopped by user. ---")

if __name__ == '__main__':
    main()
