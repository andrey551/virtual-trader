import re
from typing import Dict

# Lexicon of financial and macro keywords with sentiment weights
SENTIMENT_LEXICON: Dict[str, float] = {
    # Positive
    "growth": 0.4,
    "profit": 0.5,
    "surge": 0.6,
    "bullish": 0.7,
    "breakout": 0.6,
    "recovery": 0.4,
    "upgrade": 0.5,
    "rebound": 0.4,
    "easing": 0.3,
    "support": 0.2,
    "cut": 0.2,          # Usually positive for stocks when referring to interest rates
    "expansion": 0.4,
    "dividend": 0.3,
    "outperform": 0.5,
    "optimistic": 0.5,
    "gain": 0.3,
    "rally": 0.5,
    
    # Negative
    "inflation": -0.3,
    "rate hike": -0.4,
    "bearish": -0.7,
    "crash": -0.9,
    "drop": -0.4,
    "fall": -0.3,
    "slump": -0.6,
    "losses": -0.5,
    "deficit": -0.4,
    "recession": -0.8,
    "spill": -0.6,
    "leak": -0.4,
    "disaster": -0.7,
    "lawsuit": -0.5,
    "fine": -0.3,
    "tariff": -0.4,
    "sanction": -0.5,
    "bankruptcy": -0.9,
    "collapse": -0.8,
    "war": -0.9,
    "tension": -0.4,
    "uncertainty": -0.3,
    "weakness": -0.4,
    "crisis": -0.7,
    "slowdown": -0.4,
    "underperform": -0.5
}

def analyze_sentiment(text: str) -> float:
    """
    Calculate text sentiment score between -1.0 (extremely negative) and +1.0 (extremely positive).
    Uses keyword matching and normalizes by matching count.
    """
    if not text:
        return 0.0
    
    text_lower = text.lower()
    
    total_score = 0.0
    match_count = 0
    
    # Check multi-word phrases first to avoid splitting
    phrases = ["rate hike", "rate cut", "oil spill", "core inflation", "trade war"]
    for phrase in phrases:
        if phrase in text_lower:
            phrase_key = phrase
            if phrase_key in SENTIMENT_LEXICON:
                total_score += SENTIMENT_LEXICON[phrase_key]
                match_count += 1
                # Remove phrase to avoid matching individual words
                text_lower = text_lower.replace(phrase, "")

    # Clean text and split into words
    words = re.findall(r'\b\w+\b', text_lower)
    for word in words:
        if word in SENTIMENT_LEXICON:
            total_score += SENTIMENT_LEXICON[word]
            match_count += 1
            
    if match_count == 0:
        return 0.0
        
    avg_score = total_score / match_count
    # Bound the output between -1.0 and 1.0
    return max(-1.0, min(1.0, avg_score))
