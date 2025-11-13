import json
from abc import ABC, abstractmethod

class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    """
    @abstractmethod
    def get_trading_decision(self, prompt):
        """
        Get a trading decision from the LLM.
        """
        pass

class MockLLMProvider(BaseLLMProvider):
    """
    A mock LLM provider for testing purposes.
    """
    def get_trading_decision(self, prompt):
        """
        Returns a mock trading decision in the expected JSON format.
        """
        print("--- Mock LLM Provider ---")
        print("Received Prompt:")
        print(prompt)
        print("-------------------------")

        mock_response = {
            "operation": "open",
            "symbol": "BTC",
            "direction": "long",
            "target_position": 0.5,
            "leverage": 2,
            "reasoning": "The mock LLM provider decided to open a long position on BTC because the mock data looked promising."
        }
        return json.dumps(mock_response)

if __name__ == '__main__':
    # Example usage
    mock_provider = MockLLMProvider()

    # Create a dummy prompt
    dummy_prompt = """
    You are a cryptocurrency trading agent with a $10,000 virtual portfolio.
    Analyze the market and portfolio data provided.
    Respond ONLY with a JSON object containing: operation (open/close/hold),
    symbol, direction (long/short), target_position, leverage, and reasoning.

    Here is the data:
    ... (some data) ...
    """

    decision = mock_provider.get_trading_decision(dummy_prompt)

    print("Mock LLM Decision:")
    print(json.dumps(json.loads(decision), indent=2))
