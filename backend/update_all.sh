#!/bin/bash
# Update all dashboard data feeds

cd /home/ofer/clawbot-reports/backend

# Ensure data directory exists
mkdir -p /home/ofer/clawbot-reports/data

# Fetch breaking news
python3 news_fetcher.py

# Update sentiment data
python3 sentiment_analyzer.py

echo "Dashboard data updated: $(date)"
