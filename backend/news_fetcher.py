#!/usr/bin/env python3
"""
Breaking News Fetcher for OfsInvest Dashboard
Fetches top 3 market-moving news items every 5 minutes
"""

import json
import requests
from datetime import datetime
import pytz

def fetch_breaking_news():
    """Fetch top 3 breaking market news using web search"""
    news_items = []
    
    try:
        # Simulate news fetching (in production, use real news API)
        # For now, return placeholder structure
        news_items = [
            {
                "title": "Loading market news...",
                "source": "Market Wire",
                "time": datetime.now(pytz.timezone('Asia/Jerusalem')).isoformat(),
                "impact": "neutral",
                "url": "#"
            }
        ]
        
    except Exception as e:
        print(f"Error fetching news: {e}")
        news_items = [{
            "title": "Error loading news",
            "source": "System",
            "time": datetime.now(pytz.timezone('Asia/Jerusalem')).isoformat(),
            "impact": "neutral",
            "url": "#"
        }]
    
    return news_items[:3]

def save_news_data(output_file='/home/ofer/clawbot-reports/data/breaking-news.json'):
    """Fetch and save news data"""
    news = fetch_breaking_news()
    
    data = {
        "last_update": datetime.now(pytz.timezone('Asia/Jerusalem')).isoformat(),
        "news": news
    }
    
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    return data

if __name__ == "__main__":
    result = save_news_data()
    print(f"Fetched {len(result['news'])} news items")
