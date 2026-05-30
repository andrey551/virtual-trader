import sys
import os

# Ensure src path is visible
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from src.mock_debate import run_mock_debate

def test_mock_flow():
    print("Running unit test for Mock Debate Flow...")
    try:
        # Run mock debate for BTC-USD
        run_mock_debate(
            ticker="BTC-USD",
            category="CRYPTO",
            current_price=67250.45,
            similar_events=[]
        )
        print("Mock Debate Flow test completed successfully!")
    except Exception as e:
        print(f"Test failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_mock_flow()
