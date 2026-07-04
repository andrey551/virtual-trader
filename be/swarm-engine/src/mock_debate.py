import json
import time
import sys
from src.personas import AGENT_PERSONAS
from src.agents import should_awake_agent


def run_mock_debate(ticker: str, category: str, current_price: float, similar_events: list):
    """
    Simulates a high-fidelity live debate between the 10 specialist agents
    tailored to the specific asset ticker, category, current price, and context.
    Prints JSON messages to stdout to be parsed dynamically by the backend core.
    """
    messages = [
        {
            "code": "TECH_A",
            "msg": f"I notice that the daily RSI of {ticker} has touched deeply oversold levels. The price of {current_price} is currently receiving strong dip-buying demand from the key supporting moving averages."
        },
        {
            "code": "FUND_A",
            "msg": f"Although the technical indicators signal a recovery, from a valuation standpoint, the P/E ratio and intrinsic cash flow value of {ticker} are still under downward adjustment pressure. We should remain cautious to avoid a bull trap."
        },
        {
            "code": "MACRO_A",
            "msg": f"Indeed, the monetary tightening cycle and global CPI inflation have not fully normalized. The DXY holding above 104 points will continue to weigh on risk assets like {ticker}."
        },
        {
            "code": "GEOPOL_A",
            "msg": f"Do not forget that geopolitical risks are escalating. The recent OPEC report points to tightening crude supplies, and trade sanctions could soon spread to the semiconductor supply chain."
        },
        {
            "code": "SENT_A",
            "msg": f"Social media telemetry (Twitter/Reddit) indicates that crowd sentiment for {ticker} is shifting from Extreme Fear towards accumulation. Retail FOMO is beginning to sprout."
        },
        {
            "code": "CRYPTO_A",
            "msg": f"Looking at on-chain metrics for {ticker}, large volumes of coins are being withdrawn from exchanges to cold storage. This indicates that sell-off pressure has dried up and an accumulation phase is forming."
        },
        {
            "code": "FOREX_A",
            "msg": f"I agree. Interest rate differentials and international capital flows are favoring short-term stability for {ticker}."
        },
        {
            "code": "COMM_A",
            "msg": f"In terms of physical supply and demand, extreme weather and shipping disruptions in the Red Sea could drive physical logistics costs for {ticker} up by another 15%."
        },
        {
            "code": "RISK_M",
            "msg": f"Based on the discussed risks, I propose a safe entry zone around {current_price * 0.98:.2f}, with a strict stop loss at {current_price * 0.92:.2f} and a take profit target at {current_price * 1.15:.2f}."
        },
        {
            "code": "MOD_O",
            "msg": f"Synthesizing the specialists' debate: Technical signals support a short-term rebound around {current_price}, though macroeconomic and operational risks remain. The consensus rate stands at 82.5%. Final verdict: BUY."
        }
    ]
    
    # Filter specialists depending on category
    cat_upper = category.upper()
    if cat_upper != "CRYPTO":
        messages = [m for m in messages if m["code"] != "CRYPTO_A"]
    if cat_upper != "FOREX":
        messages = [m for m in messages if m["code"] != "FOREX_A"]
    if cat_upper != "STOCKS" and cat_upper != "INDEX":
        messages = [m for m in messages if m["code"] != "FUND_A"]
        
    for item in messages:
        code = item["code"]
        persona = AGENT_PERSONAS[code]
        agent_name = persona["name"]
        avatar = persona["avatar_code"]
        full_msg = item["msg"]
        
        should_awake, skip_reason = should_awake_agent(code, category, similar_events)
        if not should_awake:
            print(json.dumps({
                "agent_name": agent_name,
                "avatar_code": avatar,
                "message": f"[{agent_name} did not join the debate: {skip_reason}]",
                "status": "COMPLETED"
            }))
            sys.stdout.flush()
            time.sleep(0.5)
            continue
        # 3. Send COMPLETED
        print(json.dumps({
            "agent_name": agent_name,
            "avatar_code": avatar,
            "message": full_msg,
            "status": "COMPLETED"
        }))
        sys.stdout.flush()

        # 4. Send METRICS for tracking
        prompt_tokens = 250
        completion_tokens = max(1, len(full_msg) // 4)
        total_tokens = prompt_tokens + completion_tokens
        model_name = "gemini-2.5-flash" if item["code"] == "MOD_O" else "gemini-2.5-flash-lite"
        print(json.dumps({
            "type": "metrics",
            "agent_name": agent_name,
            "event": "awake",
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "model": model_name
        }))
        sys.stdout.flush()

        if code == "MOD_O":
            drift = 0.015 # +1.5% drift over 5 days
            p5s = [current_price * (1 + drift * 0.0001 * (i + 1)) for i in range(5)]
            p5m = [current_price * (1 + drift * 0.001 * (i + 1)) for i in range(5)]
            p5h = [current_price * (1 + drift * 0.02 * (i + 1)) for i in range(5)]
            p5d = [current_price * (1 + drift * 0.2 * (i + 1)) for i in range(5)]
            print(json.dumps({
                "type": "consensus_forecast",
                "ticker": ticker,
                "verdict": "BUY",
                "confidence": 82.5,
                "predict_price_5s": p5s,
                "predict_price_5m": p5m,
                "predict_price_5h": p5h,
                "predict_price_5d": p5d,
                "baseline_trajectory": p5d,
                "advanced_trajectory": p5d,
                "validation_status": "VALIDATED",
                "evaluation_analysis": "Mock evaluation: Mathematical projections align properly with the qualitative consensus verdict of BUY.",
                "confidence_adjustment": 0.0
            }))
            sys.stdout.flush()

        time.sleep(1.0) # pause between agents

