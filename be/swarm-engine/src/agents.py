import os
import sys
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from src.config import GEMINI_API_KEY
from src.personas import AGENT_PERSONAS
from src.state import SwarmState, AgentOpinion, DebateMessage

# Initialize Gemini Chat LLMs safely if key is available
llm_flash = None
llm_pro = None

if GEMINI_API_KEY:
    # 9 Specialists run on Gemini 1.5 Flash for speed & cost optimization
    llm_flash = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=GEMINI_API_KEY,
        temperature=0.5
    )
    # Swarm Moderator runs on Gemini 1.5 Pro for deep logical synthesis
    llm_pro = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
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
    return full_text
