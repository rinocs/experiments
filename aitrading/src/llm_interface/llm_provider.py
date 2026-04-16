import os
import json
from dotenv import load_dotenv
from datapizza.clients.openai import OpenAIClient

# Load environment variables from .env file
load_dotenv()

class LLMProvider:
    """
    An LLM provider that uses the datapizza-ai library.
    """
    def __init__(self, provider='openai', api_key=None):
        """
        Initializes the LLM provider.

        Args:
            provider (str): The LLM provider to use (e.g., 'openai').
            api_key (str): The API key for the provider. If not provided, it will
                           be read from the environment variables.
        """
        self.provider = provider
        self.client = self._get_client(api_key)

    def _get_client(self, api_key):
        """
        Returns a client for the specified provider.
        """
        if self.provider == 'openai':
            key = api_key or os.getenv('OPENAI_API_KEY')
            if not key:
                raise ValueError("OpenAI API key not found.")
            return OpenAIClient(api_key=key)
        # Add other providers here as needed
        # elif self.provider == 'google':
        #     # ...

        # For now, if the provider is not 'openai', we'll return a mock client
        else:
            return self._get_mock_client()

    def _get_mock_client(self):
        """
        Returns a mock client for testing.
        """
        class MockClient:
            def invoke(self, prompt):
                print("--- Mock LLM Provider ---")
                print("Received Prompt:")
                print(prompt)
                print("-------------------------")

                mock_response = {
                    "operation": "hold",
                    "symbol": "BTC",
                    "direction": "none",
                    "target_position": 0,
                    "leverage": 0,
                    "reasoning": "The mock LLM provider suggests holding due to market uncertainty."
                }

                # The datapizza-ai library returns an object with a 'text' attribute
                class MockResult:
                    def __init__(self, text):
                        self.text = text

                return MockResult(json.dumps(mock_response))

        return MockClient()

    def get_trading_decision(self, prompt):
        """
        Get a trading decision from the LLM.
        """
        result = self.client.invoke(prompt)
        return result.text

if __name__ == '__main__':
    # Example usage with a mock provider
    mock_provider = LLMProvider(provider='mock')

    dummy_prompt = "Give me a trading decision."
    decision = mock_provider.get_trading_decision(dummy_prompt)

    print("Mock LLM Decision:")
    print(json.dumps(json.loads(decision), indent=2))

    # Example usage with OpenAI (requires an API key in the .env file)
    # try:
    #     openai_provider = LLMProvider(provider='openai')
    #     decision = openai_provider.get_trading_decision("Give me a short trading decision for BTC.")
    #     print("\\nOpenAI LLM Decision:")
    #     print(json.dumps(json.loads(decision), indent=2))
    # except (ValueError, Exception) as e:
    #     print(f"\\nCould not initialize OpenAI provider: {e}")
