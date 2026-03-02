#!/usr/bin/env python3
"""
Realistic Portfolio Updater for eToro
- Gets LIVE data for real eToro orders (via order API)
- Marks manual positions as SNAPSHOT (no live data available)
- Updates tracked-trades.json with best available data
"""

import json
import requests
import uuid
from datetime import datetime
import pytz

# eToro API Configuration (ofs101clawRW client)
BASE_URL = "https://public-api.etoro.com"
API_KEY = "sdgdskldFPLGfjHn1421dgnlxdGTbngdflg6290bRjslfihsjhSDsdgGHH25hjf"
USER_KEY = "eyJjaSI6IjYwY2FiYjBiLTU1OTctNDQ4NS04ZjYzLTdlOWUwNTZlMGJiOCIsImVhbiI6IlVucmVnaXN0ZXJlZEFwcGxpY2F0aW9uIiwiZWsiOiJCRm01a3NkSUFSY29yS0FhTENwcURRLUItb09QdmNNUHFmTDNyem9NemdpTGx6NEItRjh5LWozNmY2dGhZVVpqWXoxeVhrbi52M3NYWFdCUUkwcGdmUExBbi1UNFhnZS03SWVWa0UzaEJiTV8ifQ__"

TRACKED_TRADES_FILE = "/home/ofer/clawbot-reports/data/tracked-trades.json"

def get_headers():
    """Generate eToro API headers"""
    return {
        "x-api-key": API_KEY,
        "x-user-key": USER_KEY,
        "x-request-id": str(uuid.uuid4()),
        "Content-Type": "application/json"
    }

def get_order_details(order_id):
    """Query eToro for order details"""
    try:
        url = f"{BASE_URL}/api/v1/trading/info/real/orders/{order_id}"
        response = requests.get(url, headers=get_headers(), timeout=10)
        
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return None

def update_portfolio():
    """Update portfolio with REAL data where available"""
    print("="*80)
    print("REALISTIC PORTFOLIO UPDATE - eToro ofs101clawRW Client")
    print("="*80)
    print()
    
    # Load tracked trades
    with open(TRACKED_TRADES_FILE, 'r') as f:
        tracked = json.load(f)
    
    live_count = 0
    snapshot_count = 0
    
    for trade in tracked["orders"]:
        symbol = trade["symbol"]
        order_id = trade["order_id"]
        
        # Check if this is a real eToro order (numeric ID)
        if order_id.isdigit():
            print(f"📡 {symbol} (Order {order_id}) - Querying eToro API...")
            
            order_data = get_order_details(order_id)
            if order_data and "StatusID" in order_data:
                # LIVE DATA AVAILABLE
                trade["data_source"] = "LIVE_ETORO_API"
                
                # Update status
                status_map = {
                    1: "PENDING",
                    2: "EXECUTED",
                    3: "CANCELLED",
                    4: "REJECTED",
                    7: "EXECUTED",
                    11: "PENDING_EXECUTION"
                }
                old_status = trade.get("status", "UNKNOWN")
                new_status = status_map.get(order_data["StatusID"], f"UNKNOWN_{order_data['StatusID']}")
                trade["status"] = new_status
                
                # Update prices if available
                if "CurrentRate" in order_data:
                    trade["current_price"] = order_data["CurrentRate"]
                    print(f"  ✓ Live price: ${order_data['CurrentRate']}")
                
                if "NetProfit" in order_data:
                    trade["current_pnl"] = order_data["NetProfit"]
                    print(f"  ✓ Live P&L: ${order_data['NetProfit']}")
                
                if new_status != old_status:
                    print(f"  ✓ Status: {old_status} → {new_status}")
                
                trade["last_api_update"] = datetime.now(pytz.timezone('Asia/Jerusalem')).isoformat()
                live_count += 1
                print(f"  ✅ LIVE DATA UPDATED\n")
            else:
                print(f"  ✗ API call failed - keeping existing data\n")
                trade["data_source"] = "SNAPSHOT"
                snapshot_count += 1
        else:
            # Manual position - no real order ID
            print(f"📸 {symbol} (ID: {order_id}) - SNAPSHOT DATA (manual position)")
            trade["data_source"] = "SNAPSHOT"
            trade["note"] = "Manual position - no live eToro order ID available"
            snapshot_count += 1
            print(f"  → Using static data from initial entry\n")
    
    # Save updated data
    with open(TRACKED_TRADES_FILE, 'w') as f:
        json.dump(tracked, f, indent=2)
    
    print("="*80)
    print(f"✓ PORTFOLIO UPDATE COMPLETE")
    print(f"  • {live_count} positions with LIVE eToro data")
    print(f"  • {snapshot_count} positions with SNAPSHOT data")
    print(f"  • Saved to: {TRACKED_TRADES_FILE}")
    print("="*80)
    
    return tracked

if __name__ == "__main__":
    update_portfolio()
