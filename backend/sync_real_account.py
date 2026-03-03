#!/usr/bin/env python3
"""
Sync Real eToro Account - Simple Total Tracking
Only tracks account-level totals, not individual positions
"""

import json
import requests
import uuid
from datetime import datetime
import pytz

# eToro API - ofs101clawRW
API_KEY = "sdgdskldFPLGfjHn1421dgnlxdGTbngdflg6290bRjslfihsjhSDsdgGHH25hjf"
USER_KEY = "eyJjaSI6IjYwY2FiYjBiLTU1OTctNDQ4NS04ZjYzLTdlOWUwNTZlMGJiOCIsImVhbiI6IlVucmVnaXN0ZXJlZEFwcGxpY2F0aW9uIiwiZWsiOiJCRm01a3NkSUFSY29yS0FhTENwcURRLUItb09QdmNNUHFmTDNyem9NemdpTGx6NEItRjh5LWozNmY2dGhZVVpqWXoxeVhrbi52M3NYWFdCUUkwcGdmUExBbi1UNFhnZS03SWVWa0UzaEJiTV8ifQ__"
BASE_URL = "https://public-api.etoro.com"

TRADES_FILE = "/home/ofer/clawbot-reports/trades.json"
BOT_BUDGET = 1700.00

def get_headers():
    return {
        "x-api-key": API_KEY,
        "x-user-key": USER_KEY,
        "x-request-id": str(uuid.uuid4())
    }

def get_account_info():
    """Get account-level totals from eToro API"""
    try:
        # Try to get portfolio summary
        # Note: This endpoint may not exist, so we'll use manual input for now
        # But keeping the structure for future API improvements
        
        # For now, return None and use manual updates
        return None
    except:
        return None

def update_portfolio():
    """Update portfolio with latest account totals"""
    
    # Load existing data
    with open(TRADES_FILE, 'r') as f:
        data = json.load(f)
    
    # Try to get real-time data from eToro
    account_data = get_account_info()
    
    if not account_data:
        # API not available - keep existing totals
        # Manual updates will be done via separate script
        print("Using existing account totals (manual update mode)")
    
    # Update timestamp
    data['last_update'] = datetime.now(pytz.timezone('Asia/Jerusalem')).isoformat()
    
    # Save
    with open(TRADES_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    account = data['account']
    print(f"Portfolio Status:")
    print(f"  Total: ${account['current_value']:,.2f}")
    print(f"  P&L: +${account['total_pnl']:,.2f} ({account['pnl_percent']:.2f}%)")
    print(f"  Bot Budget: ${BOT_BUDGET:,.2f}")
    print(f"  Manual: ${account['current_value'] - BOT_BUDGET:,.2f}")

if __name__ == "__main__":
    update_portfolio()
