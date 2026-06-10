import os
import sys
import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from src.config import GEMINI_API_KEY, GEMINI_FLASH_MODEL, GEMINI_PRO_MODEL
from src.personas import AGENT_PERSONAS
from src.state import SwarmState, AgentOpinion, DebateMessage

# Define structured Pydantic output models for Gemini
class AnalystOutput(BaseModel):
    verdict: str = Field(description="Final verdict for the asset. Must be exactly one of: STRONG_BUY, BUY, HOLD, SELL, or STRONG_SELL.")
    confidence: float = Field(description="Confidence rating for this verdict as a percentage from 0.0 to 100.0.")
    analysis: str = Field(description="Detailed analysis of technical charts, fundamentals, sentiment, or indicators depending on your persona.")
    key_argument: str = Field(description="A concise 1-sentence summary of your main reason for the verdict, used for state reduction.")
    counter_arguments: str = Field(description="Critique, rebuttal, or feedback addressing other specialists, if in Round 2, else empty string.")

class RiskManagerOutput(BaseModel):
    entry_zone_min: float = Field(description="Recommended lower limit of the entry range price.")
    entry_zone_max: float = Field(description="Recommended upper limit of the entry range price.")
    target_price: float = Field(description="Recommended take-profit target price.")
    stop_loss: float = Field(description="Recommended protective stop-loss price.")
    risk_verdict: str = Field(description="Defensive risk management recommendation (e.g. DEFENSIVE_HOLD, RISK_APPROVED).")
    risk_analysis: str = Field(description="Detailed risk management reasoning, volatility analysis, and sizing logic.")

class ModeratorOutput(BaseModel):
    consensus_verdict: str = Field(description="Final synthesized consensus verdict. Must be exactly one of: STRONG_BUY, BUY, HOLD, SELL, or STRONG_SELL.")
    consensus_confidence: float = Field(description="Synthesized consensus confidence level from 0.0 to 100.0.")
    synthesis_rationale: str = Field(description="Detailed consensus reasoning synthesizing Round 1 and Round 2 viewpoints.")
    momentum_direction: float = Field(description="Trend momentum direction scalar between -1.0 (strongly bearish) and 1.0 (strongly bullish).")
    risk_multiplier: float = Field(description="Volatility and risk sizing multiplier, typically 0.5 to 2.0.")
    volatility_outlook: str = Field(description="Expected volatility of the asset: HIGH, MEDIUM, or LOW.")

class ForecastEvaluationOutput(BaseModel):
    validation_status: str = Field(description="Review verdict for the mathematical price trajectories. Must be exactly one of: VALIDATED (aligns perfectly with consensus and risk targets), ADJUSTED (valid but needs caution or adjustments), or ANOMALY_DETECTED (mathematical outputs diverge significantly from qualitative reality).")
    evaluation_analysis: str = Field(description="Detailed qualitative analysis and validation of the baseline and advanced price curves relative to the specialists debate and risk boundaries.")
    confidence_adjustment: float = Field(description="Adjustment to final consensus confidence (from -20.0 to +20.0) based on mathematical trajectory validation.")

# Initialize Gemini Chat LLMs safely if key is available
llm_flash = None
llm_pro = None

if GEMINI_API_KEY:
    # 9 Specialists run on Flash Lite for speed & cost optimization
    llm_flash = ChatGoogleGenerativeAI(
        model=GEMINI_FLASH_MODEL,
        google_api_key=GEMINI_API_KEY,
        temperature=0.5
    )
    # Swarm Moderator runs on Flash for deep logical synthesis
    llm_pro = ChatGoogleGenerativeAI(
        model=GEMINI_PRO_MODEL,
        google_api_key=GEMINI_API_KEY,
        temperature=0.2
    )

def stream_agent_speech(agent_code: str, prompt_system: str, prompt_user: str) -> str:
    """
    Invokes the Gemini API and streams the output directly to stdout in real-time,
    simulating a typewriter effect chunk-by-chunk for the WebSocket connection.
    """
    persona = AGENT_PERSONAS[agent_code]
    agent_name = persona["name"]
    avatar = persona["avatar_code"]
    
    # 1. Print TYPING
    print(json.dumps({
        "agent_name": agent_name,
        "avatar_code": avatar,
        "message": "",
        "status": "TYPING"
    }))
    sys.stdout.flush()
    
    # Choose appropriate model: Pro for Swarm Moderator, Flash for specialists
    llm = llm_pro if agent_code == "MOD_O" else llm_flash
    if not llm:
        raise ValueError("Gemini API Client is not initialized. Please configure GEMINI_API_KEY.")
        
    messages = [
        ("system", prompt_system),
        ("user", prompt_user)
    ]
    
    full_text = ""
    try:
        # Stream response chunk-by-chunk
        for chunk in llm.stream(messages):
            content = chunk.content
            if content:
                full_text += content
                print(json.dumps({
                    "agent_name": agent_name,
                    "avatar_code": avatar,
                    "message_chunk": content,
                    "status": "SPEAKING"
                }))
                sys.stdout.flush()
    except Exception as e:
        # Gracefully handle API failures by falling back to errors printed as chat
        error_msg = f"[Error calling Gemini API: {str(e)}]"
        full_text += error_msg
        print(json.dumps({
            "agent_name": agent_name,
            "avatar_code": avatar,
            "message_chunk": error_msg,
            "status": "SPEAKING"
        }))
        sys.stdout.flush()

    # 2. Print COMPLETED
    print(json.dumps({
        "agent_name": agent_name,
        "avatar_code": avatar,
        "message": full_text,
        "status": "COMPLETED"
    }))
    sys.stdout.flush()

    # 3. Print METRICS for tracking
    prompt_tokens = max(1, len(prompt_system + prompt_user) // 4)
    completion_tokens = max(1, len(full_text) // 4)
    total_tokens = prompt_tokens + completion_tokens
    
    model_name = GEMINI_PRO_MODEL if agent_code == "MOD_O" else GEMINI_FLASH_MODEL
    
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

    return full_text


def stream_structured_agent_speech(agent_code: str, prompt_system: str, prompt_user: str, output_schema):
    """
    Invokes the Gemini API using structured output with a Pydantic schema.
    Returns the parsed Pydantic object, while simulating typewriter streaming to stdout for UX compatibility.
    """
    import time
    persona = AGENT_PERSONAS[agent_code]
    agent_name = persona["name"]
    avatar = persona["avatar_code"]
    
    # 1. Print TYPING
    print(json.dumps({
        "agent_name": agent_name,
        "avatar_code": avatar,
        "message": "",
        "status": "TYPING"
    }))
    sys.stdout.flush()
    
    llm = llm_pro if agent_code == "MOD_O" else llm_flash
    if not llm:
        raise ValueError("Gemini API Client is not initialized. Please configure GEMINI_API_KEY.")
        
    messages = [
        ("system", prompt_system),
        ("user", prompt_user)
    ]
    
    try:
        # Wrap the LLM with structured output schema
        structured_llm = llm.with_structured_output(output_schema)
        result = structured_llm.invoke(messages)
        
        # Extract the appropriate text field to stream chunk-by-chunk for the frontend
        text_to_stream = ""
        if hasattr(result, "analysis"):
            text_to_stream = result.analysis
            if getattr(result, "counter_arguments", ""):
                text_to_stream += "\n\n**Counter Arguments & Critiques:**\n" + result.counter_arguments
        elif hasattr(result, "risk_analysis"):
            text_to_stream = result.risk_analysis
        elif hasattr(result, "synthesis_rationale"):
            text_to_stream = result.synthesis_rationale
            
        # Simulate chunk streaming to stdout for the WebSocket consumer
        chunk_size = 8
        for i in range(0, len(text_to_stream), chunk_size):
            chunk = text_to_stream[i:i+chunk_size]
            print(json.dumps({
                "agent_name": agent_name,
                "avatar_code": avatar,
                "message_chunk": chunk,
                "status": "SPEAKING"
            }))
            sys.stdout.flush()
            time.sleep(0.015) # 15ms typewriter delay
            
        # 2. Print COMPLETED
        print(json.dumps({
            "agent_name": agent_name,
            "avatar_code": avatar,
            "message": text_to_stream,
            "status": "COMPLETED"
        }))
        sys.stdout.flush()
        
        # 3. Print METRICS
        prompt_tokens = max(1, len(prompt_system + prompt_user) // 4)
        completion_tokens = max(1, len(text_to_stream) // 4)
        total_tokens = prompt_tokens + completion_tokens
        model_name = GEMINI_PRO_MODEL if agent_code == "MOD_O" else GEMINI_FLASH_MODEL
        
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
        
        return result
        
    except Exception as e:
        # Handle failures gracefully by falling back to text error blocks
        error_msg = f"[Error in structured Gemini call: {str(e)}]"
        print(json.dumps({
            "agent_name": agent_name,
            "avatar_code": avatar,
            "message_chunk": error_msg,
            "status": "SPEAKING"
        }))
        sys.stdout.flush()
        print(json.dumps({
            "agent_name": agent_name,
            "avatar_code": avatar,
            "message": error_msg,
            "status": "COMPLETED"
        }))
        sys.stdout.flush()
        
        # Return fallback Pydantic objects depending on schema
        if output_schema == AnalystOutput:
            return AnalystOutput(verdict="HOLD", confidence=50.0, analysis=error_msg, key_argument="API error fallback", counter_arguments="")
        elif output_schema == RiskManagerOutput:
            return RiskManagerOutput(entry_zone_min=0.0, entry_zone_max=0.0, target_price=0.0, stop_loss=0.0, risk_verdict="HOLD", risk_analysis=error_msg)
        elif output_schema == ForecastEvaluationOutput:
            return ForecastEvaluationOutput(
                validation_status="VALIDATED",
                evaluation_analysis=f"Fallback evaluation due to structured call error: {error_msg}",
                confidence_adjustment=0.0
            )
        else:
            return ModeratorOutput(
                consensus_verdict="HOLD",
                consensus_confidence=50.0,
                synthesis_rationale=error_msg,
                momentum_direction=0.0,
                risk_multiplier=1.0,
                volatility_outlook="MEDIUM"
            )


def should_awake_agent(agent_code: str, category: str, similar_events: list) -> tuple[bool, str]:
    """
    Determines if an agent has reasoning/data to participate in the debate.
    Returns (should_awake, reason).
    """
    # Category checks
    cat_upper = category.upper()
    if agent_code == "CRYPTO_A" and cat_upper != "CRYPTO":
        return False, f"Agent is specialized in CRYPTO, but asset category is {category}."
    if agent_code == "FOREX_A" and cat_upper != "FOREX":
        return False, f"Agent is specialized in FOREX, but asset category is {category}."
    if agent_code == "COMM_A" and cat_upper != "COMMODITY":
        return False, f"Agent is specialized in COMMODITY, but asset category is {category}."
    if agent_code == "FUND_A" and cat_upper not in ["STOCKS", "INDEX"]:
        return False, f"Agent is specialized in STOCKS/INDEX fundamentals, but asset category is {category}."

    # Specific data-driven reasoning for social/sentiment agent
    if agent_code == "SENT_A":
        # Check if there are news/events related to the asset ticker
        if not similar_events:
            return False, "No recent news or sentiment events found in database or internet search."
        
        # Check if any event has been updated/published within the last 7 days
        import datetime
        now = datetime.datetime.utcnow()
        has_recent = False
        for ev in similar_events:
            pub_at = ev.get("published_at")
            if isinstance(pub_at, str):
                try:
                    # Handle ISO string formatting
                    pub_at = datetime.datetime.fromisoformat(pub_at)
                except Exception:
                    pass
            if isinstance(pub_at, datetime.datetime):
                if pub_at.tzinfo is not None:
                    pub_at = pub_at.replace(tzinfo=None)
                if (now - pub_at).days <= 7:
                    has_recent = True
                    break
        if not has_recent:
            return False, "No new social or news updates in the last 7 days."

    return True, "Agent has active reasoning and data to participate in the debate."

