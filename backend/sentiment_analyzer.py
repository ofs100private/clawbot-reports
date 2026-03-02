#!/usr/bin/env python3
"""
X (Twitter) Sentiment Analyzer for Markets
Analyzes sentiment for: US Market, Commodities, ETFs, Crypto
"""

import json
from datetime import datetime
import pytz

def analyze_sentiment(category):
    """Analyze sentiment for a market category"""
    # Placeholder - will be replaced with real X API calls via Grok
    sentiments = {
        "us_market": {"score": 65, "label": "Bullish", "trend": "up"},
        "commodities": {"score": 72, "label": "Bullish", "trend": "up"},
        "etfs": {"score": 58, "label": "Neutral", "trend": "flat"},
        "crypto": {"score": 55, "label": "Neutral", "trend": "up"}
    }
    return sentiments.get(category, {"score": 50, "label": "Neutral", "trend": "flat"})

def get_fear_greed_index():
    """Fetch Fear & Greed Index"""
    try:
        # Alternative API if available, or calculate from VIX
        # Placeholder for now
        return {
            "value": 45,
            "label": "Neutral",
            "updated": datetime.now(pytz.timezone('Asia/Jerusalem')).isoformat()
        }
    except Exception as e:
        return {
            "value": 50,
            "label": "Neutral (Error)",
            "updated": datetime.now(pytz.timezone('Asia/Jerusalem')).isoformat()
        }

def save_sentiment_data(output_file='/home/ofer/clawbot-reports/data/sentiment.json'):
    """Fetch and save all sentiment data"""
    data = {
        "last_update": datetime.now(pytz.timezone('Asia/Jerusalem')).isoformat(),
        "fear_greed": get_fear_greed_index(),
        "sentiment": {
            "us_market": analyze_sentiment("us_market"),
            "commodities": analyze_sentiment("commodities"),
            "etfs": analyze_sentiment("etfs"),
            "crypto": analyze_sentiment("crypto")
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    return data

if __name__ == "__main__":
    result = save_sentiment_data()
    print(f"Updated sentiment data: Fear & Greed = {result['fear_greed']['value']}")
