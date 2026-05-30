import argparse
import os
import sys

# Ensure swarm-engine parent directory is in PYTHONPATH to allow modular sub-imports
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from src.config import GEMINI_API_KEY
from src.mock_debate import run_mock_debate
from src.graph import create_swarm_graph

def main():
    parser = argparse.ArgumentParser(description="Virtual Trader Swarm Agent Engine CLI")
    parser.add_argument("--ticker", type=str, required=True, help="Asset ticker symbol (e.g. AAPL, BTC-USD)")
    parser.add_argument("--category", type=str, default="CRYPTO", help="Asset category (STOCKS, CRYPTO, FOREX, INDEX)")
    parser.add_argument("--price", type=float, default=100.0, help="Current asset price")
    
    args = parser.parse_args()
    
    # Check if Gemini API key is configured
    if not GEMINI_API_KEY:
        # Fallback to high-fidelity mock stream if offline
        run_mock_debate(
            ticker=args.ticker,
            category=args.category,
            current_price=args.price,
            similar_events=[]
        )
    else:
        # Run real LangGraph agent graph
        graph = create_swarm_graph()
        initial_state = {
            "ticker": args.ticker,
            "category": args.category,
            "current_price": args.price,
            "market_data": {},
            "similar_historical_events": [],
            "opinions": {},
            "debate_history": [],
            "risk_profile": {},
            "consensus_verdict": "HOLD",
            "consensus_confidence": 50.0
        }
        # Run graph execution loop
        graph.invoke(initial_state)

if __name__ == "__main__":
    main()
