import os
import sys
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from src.config import GEMINI_API_KEY, GEMINI_FLASH_MODEL, GEMINI_PRO_MODEL
from src.personas import AGENT_PERSONAS
from src.state import SwarmState, AgentOpinion, DebateMessage

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

