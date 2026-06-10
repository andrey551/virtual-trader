import json
import sys
import asyncio
from langgraph.graph import StateGraph, END
from src.state import SwarmState, AgentOpinion, DebateMessage
from src.personas import AGENT_PERSONAS
from src.agents import (
    stream_agent_speech,
    stream_structured_agent_speech,
    AnalystOutput,
    RiskManagerOutput,
    ModeratorOutput,
    ForecastEvaluationOutput,
    GEMINI_API_KEY,
    should_awake_agent
)
from src.database_client import db_client
from src.mock_debate import run_mock_debate
from src.mcp_client import MathToolsMCPClient

def retrieve_analogy_node(state: SwarmState) -> dict:
    """
    Retrieves similar historical events from pgvector or SQLite fallback,
    calculates live technical indicators, and walks the Knowledge Graph within 2-hops.
    """
    ticker = state["ticker"]
    category = state["category"]
    price = state["current_price"]
    print(f"[Node: RetrieveAnalogy] Querying historical events & Knowledge Graph paths for {ticker} ({category})...")
    
    # Query matching keywords
    query_text = "lãi suất" if category == "FOREX" else ("oil" if ticker in ["USO", "CL=F"] else ticker)
    past_events = db_client.get_similar_past_events(
        query_text=query_text, 
        limit=3, 
        ticker=ticker, 
        current_price=price
    )
    
    # Walk the Knowledge Graph
    paths = db_client.get_related_knowledge_paths(ticker)
    
    # Calculate live technical indicators
    indicators = db_client.calculate_technical_indicators(ticker)
    
    return {
        "similar_historical_events": past_events,
        "knowledge_graph_paths": paths,
        "market_indicators": indicators
    }


def specialist_analysis_node(state: SwarmState) -> dict:
    """
    Executes independent rounds of specialist analysis (Round 1) using structured output.
    """
    ticker = state["ticker"]
    category = state["category"]
    price = state["current_price"]
    events_str = json.dumps(state.get("similar_historical_events", []), ensure_ascii=False, indent=2)
    kg_paths = state.get("knowledge_graph_paths", [])
    kg_paths_str = "\n".join(kg_paths) if kg_paths else "- No explicit baseline relations mapped."
    
    # Format computed technical indicators
    indicators = state.get("market_indicators", {})
    if indicators and indicators.get("status") == "SUCCESS":
        indicators_str = (
            f"- Current Price: {indicators['price']}\n"
            f"- 24h Change Percent: {indicators['change_percent']}%\n"
            f"- RSI (14-period): {indicators['rsi']} (Interpretation: {'Oversold' if indicators['rsi'] < 30 else 'Overbought' if indicators['rsi'] > 70 else 'Neutral'})\n"
            f"- MACD: Line={indicators['macd_line']}, Signal={indicators['macd_signal']}, Histogram={indicators['macd_hist']} ({indicators['macd_verdict']})\n"
            f"- 50-day SMA: {indicators['sma_50']} ({indicators['sma_50_verdict']})\n"
            f"- 24h Trading Volume: {indicators['volume_24h']:,} (vs 50-day average: {indicators['volume_avg_50d']:,}, Surge Ratio: {indicators['volume_surge_ratio']}x)"
        )
    else:
        indicators_str = "- No live technical indicators telemetry available (using default fallbacks)."

    opinions = {}
    
    # Select active specialist codes based on asset category
    active_codes = ["TECH_A", "FUND_A", "MACRO_A", "GEOPOL_A", "SENT_A", "RISK_M"]
    if category.upper() == "CRYPTO":
        active_codes.append("CRYPTO_A")
    elif category.upper() == "FOREX":
        active_codes.append("FOREX_A")
    elif category.upper() == "COMMODITY":
        active_codes.append("COMM_A")
        
    for code in active_codes:
        if code == "RISK_M":
            # Risk manager speaks in a later node
            continue
            
        should_awake, skip_reason = should_awake_agent(code, category, state.get("similar_historical_events", []))
        if not should_awake:
            persona = AGENT_PERSONAS[code]
            print(json.dumps({
                "agent_name": persona["name"],
                "avatar_code": persona["avatar_code"],
                "message": f"[{persona['name']} did not join the debate: {skip_reason}]",
                "status": "COMPLETED"
            }))
            sys.stdout.flush()
            continue
            
        persona = AGENT_PERSONAS[code]
        prompt_system = f"System Instruction: {persona['prompt']} Your name is {persona['name']}."
        
        prompt_user = f"""
        Asset: {ticker}
        Category: {category}
        Current Price: {price}
        
        Live Technical Indicators & Market Telemetry:
        {indicators_str}
        
        Knowledge Graph Pathways (Priors & Dependencies):
        {kg_paths_str}
        
        Similar Past Events (Context):
        {events_str}
        
        Based on your specialist persona, computed indicators, and the semantic connections above, evaluate the current price and market environment. Propose your verdict and confidence rating.
        """
        
        # Enforce structured output using stream_structured_agent_speech
        structured_out = stream_structured_agent_speech(code, prompt_system, prompt_user, AnalystOutput)
        
        opinions[code] = AgentOpinion(
            agent_name=persona["name"],
            verdict=structured_out.verdict,
            confidence=structured_out.confidence,
            rationale=structured_out.analysis,
            key_argument=structured_out.key_argument,
            indicators_audited=[category, "News Match", "Structured Technical Indicators"]
        )
        
    return {"opinions": opinions}

def swarm_debate_node(state: SwarmState) -> dict:
    """
    Executes a round of cross-criticism and debate (Round 2) using structured output and state reduction.
    """
    ticker = state["ticker"]
    category = state["category"]
    price = state["current_price"]
    
    # State Reduction: format condensed summaries of Round 1 opinions to save tokens
    opinions_str = ""
    for code, op in state["opinions"].items():
        opinions_str += f"- {op.agent_name}: {op.verdict} ({op.confidence}% confidence) - Key Argument: {op.key_argument}\n"
        
    # Format computed technical indicators to maintain context in Round 2
    indicators = state.get("market_indicators", {})
    if indicators and indicators.get("status") == "SUCCESS":
        indicators_str = (
            f"- Current Price: {indicators['price']}\n"
            f"- 24h Change Percent: {indicators['change_percent']}%\n"
            f"- RSI (14-period): {indicators['rsi']}\n"
            f"- MACD: Line={indicators['macd_line']}, Signal={indicators['macd_signal']}, Histogram={indicators['macd_hist']} ({indicators['macd_verdict']})\n"
            f"- 50-day SMA: {indicators['sma_50']} ({indicators['sma_50_verdict']})\n"
            f"- Volume: {indicators['volume_24h']:,} (vs 50-day average: {indicators['volume_avg_50d']:,})"
        )
    else:
        indicators_str = "- No live indicators telemetry."
        
    debate_history = []
    
    # Let 3 core specialists argue (Technical, Fundamental/Macro, and Sentiment)
    debaters = ["TECH_A", "SENT_A"]
    if category.upper() == "CRYPTO":
        debaters.append("CRYPTO_A")
    else:
        debaters.append("MACRO_A")
        
    # Only allow agents who have entered an opinion in Round 1
    debaters = [d for d in debaters if d in state["opinions"]]
    
    for code in debaters:
        persona = AGENT_PERSONAS[code]
        prompt_system = (
            f"System Instruction: {persona['prompt']} "
            "You are entering Round 2 of the Swarm Debate. You must critique, agree, or disagree with the opinions of the other agents converse-style. "
            "Do NOT simply rephrase or repeat your own analysis or arguments from Round 1. Focus on addressing disagreements, key arguments, or limitations raised by other agents. "
            "Reference other agents by name (e.g. 'Technical Analyst'). Keep it concise and debate-focused."
        )
        
        prompt_user = f"""
        Asset: {ticker}
        Category: {category}
        Current Price: {price}
        
        Live Technical Indicators:
        {indicators_str}
        
        All Specialist Opinions from Round 1 (Summary List):
        {opinions_str}
        
        Write your debate entry responding to these opinions. Direct your comments to specific agents if you disagree or want to reinforce their points.
        """
        
        structured_out = stream_structured_agent_speech(code, prompt_system, prompt_user, AnalystOutput)
        
        debate_history.append(DebateMessage(
            agent_name=persona["name"],
            avatar_code=persona["avatar_code"],
            message=structured_out.counter_arguments or structured_out.analysis
        ))
        
    return {"debate_history": debate_history}

def risk_assessment_node(state: SwarmState) -> dict:
    """
    Invokes the Risk Manager to audit consensus and recommend safe SL / TP levels using structured output.
    """
    ticker = state["ticker"]
    price = state["current_price"]
    
    # State Reduction: format condensed summaries of Round 1 opinions to save tokens
    opinions_str = ""
    for code, op in state["opinions"].items():
        opinions_str += f"- {op.agent_name}: {op.verdict} ({op.confidence}% confidence) - Key Argument: {op.key_argument}\n"
        
    # Format computed technical indicators to maintain context
    indicators = state.get("market_indicators", {})
    if indicators and indicators.get("status") == "SUCCESS":
        indicators_str = (
            f"- Current Price: {indicators['price']}\n"
            f"- 24h Change Percent: {indicators['change_percent']}%\n"
            f"- RSI (14-period): {indicators['rsi']}\n"
            f"- MACD: Line={indicators['macd_line']}, Signal={indicators['macd_signal']}, Histogram={indicators['macd_hist']} ({indicators['macd_verdict']})\n"
            f"- 50-day SMA: {indicators['sma_50']} ({indicators['sma_50_verdict']})\n"
            f"- Volume: {indicators['volume_24h']:,} (vs 50-day average: {indicators['volume_avg_50d']:,})"
        )
    else:
        indicators_str = "- No live indicators telemetry."
        
    code = "RISK_M"
    persona = AGENT_PERSONAS[code]
    
    prompt_system = f"System Instruction: {persona['prompt']}"
    prompt_user = f"""
    Asset: {ticker}
    Current Price: {price}
    
    Live Technical Indicators:
    {indicators_str}
    
    Specialist Opinions (Summary List):
    {opinions_str}
    
    Provide your risk audit, calculating the Entry zone range, Target Profit (TP), and Stop Loss (SL) boundaries. Return the risk profile clearly as structured output.
    """
    
    structured_out = stream_structured_agent_speech(code, prompt_system, prompt_user, RiskManagerOutput)
    
    risk_profile = {
        "entry": structured_out.entry_zone_max,
        "entry_range": f"{structured_out.entry_zone_min:.2f} - {structured_out.entry_zone_max:.2f}",
        "target": structured_out.target_price,
        "stop_loss": structured_out.stop_loss,
        "risk_verdict": structured_out.risk_verdict,
        "rationale": structured_out.risk_analysis
    }
    
    return {"risk_profile": risk_profile}

def consensus_moderator_node(state: SwarmState) -> dict:
    """
    Invokes the Swarm Moderator (Gemini 1.5 Pro) to synthesize the debate
    and output the final Verdict, confidence, momentum and risk multiplier.
    Then triggers the math-tools MCP server to compute exact quantitative predictions.
    """
    ticker = state["ticker"]
    price = state["current_price"]
    
    # State Reduction: format condensed summaries of Round 1 opinions to save tokens
    opinions_str = ""
    for code, op in state["opinions"].items():
        opinions_str += f"- {op.agent_name}: {op.verdict} ({op.confidence}% confidence) - Key Argument: {op.key_argument}\n"
        
    # Format computed technical indicators to maintain context
    indicators = state.get("market_indicators", {})
    if indicators and indicators.get("status") == "SUCCESS":
        indicators_str = (
            f"- Current Price: {indicators['price']}\n"
            f"- 24h Change Percent: {indicators['change_percent']}%\n"
            f"- RSI (14-period): {indicators['rsi']}\n"
            f"- MACD: Line={indicators['macd_line']}, Signal={indicators['macd_signal']}, Histogram={indicators['macd_hist']} ({indicators['macd_verdict']})\n"
            f"- 50-day SMA: {indicators['sma_50']} ({indicators['sma_50_verdict']})\n"
            f"- Volume: {indicators['volume_24h']:,} (vs 50-day average: {indicators['volume_avg_50d']:,})"
        )
    else:
        indicators_str = "- No live indicators telemetry."
        
    debate_str = json.dumps([d.dict() for d in state["debate_history"]], ensure_ascii=False)
    risk_str = json.dumps(state["risk_profile"], ensure_ascii=False)
    kg_paths = state.get("knowledge_graph_paths", [])
    kg_paths_str = "\n".join(kg_paths) if kg_paths else "- No baseline relations."
    
    code = "MOD_O"
    persona = AGENT_PERSONAS[code]
    
    prompt_system = f"System Instruction: {persona['prompt']}"
    
    prompt_user = f"""
    Ticker: {ticker}
    Current Price: {price}
    
    Live Technical Indicators:
    {indicators_str}
    
    Knowledge Graph Paths (Priors & Sector Relationships):
    {kg_paths_str}
    
    Round 1 Opinions (Summary List):
    {opinions_str}
    
    Round 2 Debate:
    {debate_str}
    
    Risk Assessment:
    {risk_str}
    
    Synthesize all arguments and define the qualitative consensus direction. In your structured output, provide:
    1. A final unified recommendation verdict (STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL) and a confidence percentage (0.0 to 100.0).
    2. A momentum direction scalar between -1.0 (strongly bearish) and 1.0 (strongly bullish) representing market momentum.
    3. A risk multiplier sizing factor between 0.5 and 2.0 based on risk and volatility audit.
    4. A general volatility outlook (HIGH, MEDIUM, or LOW).
    """
    
    structured_out = stream_structured_agent_speech(code, prompt_system, prompt_user, ModeratorOutput)
    
    # helper for running async functions from sync contexts safely
    def run_async(coro):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
            
        if loop and loop.is_running():
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return asyncio.run(coro)

    async def get_mcp_forecast():
        client = MathToolsMCPClient()
        try:
            await client.start()
            forecast_args = {
                "ticker": ticker,
                "current_price": float(price),
                "consensus_verdict": structured_out.consensus_verdict,
                "consensus_confidence": float(structured_out.consensus_confidence),
                "momentum_direction": float(structured_out.momentum_direction),
                "risk_multiplier": float(structured_out.risk_multiplier),
                "volatility_outlook": structured_out.volatility_outlook
            }
            res = await client.call_predict_trajectory(forecast_args)
            return res
        finally:
            await client.stop()

    print(f"[Graph Moderator] Dispatching qualitative data to math-tools MCP server...")
    sys.stdout.flush()
    
    forecast_res = run_async(get_mcp_forecast())
    
    # 3. Swarm Evaluation and Review Node
    print(f"[Graph Moderator] Evaluating mathematical results via Swarm Review node...")
    sys.stdout.flush()
    
    eval_prompt_system = (
        "System Instruction: You are the Swarm Moderator. Your task is to perform the final review and evaluation of the mathematical forecasting outputs "
        "calculated by the quantitative models against the qualitative specialists consensus and the Risk Manager boundaries. "
        "Address if the mathematical curves are consistent with the general recommendation or if they are overly aggressive/bearish."
    )
    
    # Format forecasts for the evaluator LLM
    if forecast_res.get("status") == "success":
        predict_price_5d_str = ", ".join([f"{p:.2f}" for p in forecast_res["predict_price_5d"]])
        baseline_trajectory_str = ", ".join([f"{p:.2f}" for p in forecast_res["baseline_trajectory"]])
    else:
        predict_price_5d_str = "N/A"
        baseline_trajectory_str = "N/A"
        
    eval_prompt_user = f"""
    Asset Ticker: {ticker}
    Current price: {price}
    
    Risk Boundaries set by Risk Manager:
    {risk_str}
    
    Qualitative Consensus Verdict: {structured_out.consensus_verdict}
    Consensus Confidence: {structured_out.consensus_confidence}%
    Momentum Direction: {structured_out.momentum_direction}
    Risk Multiplier: {structured_out.risk_multiplier}
    Volatility Outlook: {structured_out.volatility_outlook}
    
    Mathematical Projections (Calculated via Math Models):
    - Baseline 5-day Trajectory: [{baseline_trajectory_str}]
    - Advanced 5-day Trajectory (Swarm-Adjusted): [{predict_price_5d_str}]
    
    Please evaluate the mathematical model results:
    1. Check if the advanced trajectory correctly moves in the direction of our consensus verdict.
    2. Check if the trajectory is risk-realistic, especially if it respects or targets the Risk Manager's target profit/stop loss levels.
    3. Output validation status (VALIDATED, ADJUSTED, or ANOMALY_DETECTED), an evaluation rationale, and any adjustments to the final consensus confidence score.
    """
    
    eval_out = stream_structured_agent_speech(code, eval_prompt_system, eval_prompt_user, ForecastEvaluationOutput)
    
    # Adjust final consensus confidence based on math evaluation
    final_confidence = max(0.0, min(100.0, float(structured_out.consensus_confidence) + float(eval_out.confidence_adjustment)))
    
    # Print consensus forecast structured JSON for backend WebSocket parsing
    try:
        if forecast_res.get("status") == "success":
            forecast_data = {
                "type": "consensus_forecast",
                "ticker": ticker,
                "verdict": structured_out.consensus_verdict,
                "confidence": round(final_confidence, 2),
                "predict_price_5s": [float(p) for p in forecast_res["predict_price_5s"]],
                "predict_price_5m": [float(p) for p in forecast_res["predict_price_5m"]],
                "predict_price_5h": [float(p) for p in forecast_res["predict_price_5h"]],
                "predict_price_5d": [float(p) for p in forecast_res["predict_price_5d"]],
                "baseline_trajectory": [float(p) for p in forecast_res["baseline_trajectory"]],
                "advanced_trajectory": [float(p) for p in forecast_res["advanced_trajectory"]],
                # Add validation report fields
                "validation_status": eval_out.validation_status,
                "evaluation_analysis": eval_out.evaluation_analysis,
                "confidence_adjustment": eval_out.confidence_adjustment
            }
            print(json.dumps(forecast_data))
            sys.stdout.flush()
        else:
            raise ValueError(forecast_res.get("message", "Unknown MCP forecast failure"))
    except Exception as fe:
        print(f"[Graph Error] Failed to compute or parse math forecasts: {fe}", file=sys.stderr)
        # Fallback trajectory calculations if MCP server fails or raises exception
        fallback_data = {
            "type": "consensus_forecast",
            "ticker": ticker,
            "verdict": structured_out.consensus_verdict,
            "confidence": structured_out.consensus_confidence,
            "predict_price_5s": [price] * 5,
            "predict_price_5m": [price] * 5,
            "predict_price_5h": [price] * 5,
            "predict_price_5d": [price] * 5,
            "baseline_trajectory": [price] * 5,
            "advanced_trajectory": [price] * 5,
            "validation_status": "VALIDATION_FAILED",
            "evaluation_analysis": f"Failed to compute math forecasts: {fe}",
            "confidence_adjustment": 0.0
        }
        print(json.dumps(fallback_data))
        sys.stdout.flush()
    
    return {
        "consensus_verdict": structured_out.consensus_verdict,
        "consensus_confidence": final_confidence
    }

def create_swarm_graph() -> StateGraph:
    """
    Configures the LangGraph StateGraph mapping nodes and sequential edges.
    """
    workflow = StateGraph(SwarmState)
    
    # Add nodes
    workflow.add_node("retrieve_analogy", retrieve_analogy_node)
    workflow.add_node("specialist_analysis", specialist_analysis_node)
    workflow.add_node("swarm_debate", swarm_debate_node)
    workflow.add_node("risk_assessment", risk_assessment_node)
    workflow.add_node("consensus_moderator", consensus_moderator_node)
    
    # Configure sequential routing flow
    workflow.set_entry_point("retrieve_analogy")
    workflow.add_edge("retrieve_analogy", "specialist_analysis")
    workflow.add_edge("specialist_analysis", "swarm_debate")
    workflow.add_edge("swarm_debate", "risk_assessment")
    workflow.add_edge("risk_assessment", "consensus_moderator")
    workflow.add_edge("consensus_moderator", END)
    
    return workflow.compile()
