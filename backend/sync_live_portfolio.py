#!/usr/bin/env python3
"""
COMPREHENSIVE Portfolio Sync - eToro ofs101clawRW Client
- Queries real orders via eToro API
- Fetches live instrument rates
- Calculates current P&L
- Updates tracked-trades.json with LIVE data where possible
"""

import json
import requests
import uuid
from datetime import datetime
import pytz

# eToro API Configuration
BASE_URL = "https://public-api.etoro.com"
API_KEY = "sdgdskldFPLGfjHn1421dgnlxdGTbngdflg6290bRjslfihsjhSDsdgGHH25hjf"
USER_KEY = "eyJjaSI6IjYwY2FiYjBiLTU1OTctNDQ4NS04ZjYzLTdlOWUwNTZlMGJiOCIsImVhbiI6IlVucmVnaXN0ZXJlZEFwcGxpY2F0aW9uIiwiZWsiOiJCRm01a3NkSUFSY29yS0FhTENwcURRLUItb09QdmNNUHFmTDNyem9NemdpTGx6NEItRjh5LWozNmY2dGhZVVpqWXoxeVhrbi52M3NYWFdCUUkwcGdmUExBbi1UNFhnZS03SWVWa0UzaEJiTV8ifQ__"

TRACKED_TRADES_FILE = "/home/ofer/clawbot-reports/data/tracked-trades.json"

def get_headers():
    return {
        "x-api-key": API_KEY,
        "x-user-key": USER_KEY,
        "x-request-id": str(uuid.uuid4())
    }

def get_order_details(order_id):
    """Get order details from eToro"""
    try:
        url = f"{BASE_URL}/api/v1/trading/info/real/orders/{order_id}"
        r = requests.get(url, headers=get_headers(), timeout=15)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def get_instrument_rate(instrument_id):
    """Get current market rate for instrument"""
    try:
        url = f"{BASE_URL}/api/v1/market-data/instruments/rates?instrumentIds={instrument_id}"
        r = requests.get(url, headers=get_headers(), timeout=15)
        if r.status_code == 200:
            data = r.json()
            if "rates" in data and len(data["rates"]) > 0:
                return data["rates"][0].get("lastExecution") or data["rates"][0].get("bid")
        return None
    except:
        return None

def sync_portfolio():
    """Sync portfolio with live eToro data"""
    print("="*80)
    print("LIVE PORTFOLIO SYNC - eToro ofs101clawRW Client")
    print("="*80)
    print()
    
    with open(TRACKED_TRADES_FILE, 'r') as f:
        tracked = json.load(f)
    
    live_count = 0
    snapshot_count = 0
    
    for trade in tracked["orders"]:
        symbol = trade["symbol"]
        order_id = trade["order_id"]
        
        # Real eToro order?
        if order_id.isdigit():
            print(f"📡 {symbol} (Order {order_id})")
            
            # Step 1: Get order details
            order_data = get_order_details(order_id)
            if not order_data or "orderID" not in order_data:
                print(f"  ✗ Order API failed\n")
                trade["data_source"] = "SNAPSHOT"
                snapshot_count += 1
                continue
            
            # Step 2: Parse order data
            instrument_id = order_data.get("instrumentID")
            status_id = order_data.get("statusID")
            amount = order_data.get("amount", trade["amount"])
            units = order_data.get("units")
            
            status_map = {1: "PENDING", 2: "EXECUTED", 3: "CANCELLED", 4: "REJECTED", 7: "EXECUTED", 11: "PENDING_EXECUTION"}
            trade["status"] = status_map.get(status_id, f"UNKNOWN_{status_id}")
            print(f"  • Status: {trade['status']}")
            
            # Step 3: Get current market rate
            if instrument_id:
                current_rate = get_instrument_rate(instrument_id)
                if current_rate:
                    trade["current_price"] = current_rate
                    print(f"  • Live price: ${current_rate}")
                    
                    # Calculate P&L
                    if trade["price"] > 0 and units:
                        # entry_value = amount (what was invested)
                        # current_value = units × current_rate
                        # P&L = current_value - entry_value
                        current_value = units * current_rate
                        entry_value = amount
                        pnl = current_value - entry_value
                        pnl_pct = (pnl / entry_value) * 100 if entry_value > 0 else 0
                        
                        trade["current_pnl"] = pnl
                        print(f"  • Calculated P&L: ${pnl:.2f} ({pnl_pct:+.2f}%)")
                    
                    trade["data_source"] = "LIVE_ETORO_API"
                    trade["last_api_update"] = datetime.now(pytz.timezone('Asia/Jerusalem')).isoformat()
                    live_count += 1
                    print(f"  ✅ LIVE DATA\n")
                else:
                    print(f"  ✗ Rate API failed\n")
                    trade["data_source"] = "SNAPSHOT"
                    snapshot_count += 1
            else:
                print(f"  ✗ No instrument ID\n")
                trade["data_source"] = "SNAPSHOT"
                snapshot_count += 1
        else:
            # Manual position
            print(f"📸 {symbol} - SNAPSHOT (manual position)\n")
            trade["data_source"] = "SNAPSHOT"
            snapshot_count += 1
    
    # Save
    with open(TRACKED_TRADES_FILE, 'w') as f:
        json.dump(tracked, f, indent=2)
    
    print("="*80)
    print(f"✅ SYNC COMPLETE")
    print(f"  • {live_count} positions with LIVE data")
    print(f"  • {snapshot_count} positions with SNAPSHOT data")
    print("="*80)

if __name__ == "__main__":
    sync_portfolio()
