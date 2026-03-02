#!/usr/bin/env python3
"""
Fetch LIVE prices from eToro API for all tracked instruments
Updates tracked-trades.json with real-time market data
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

# Symbol to eToro Instrument ID mapping (discovered via API)
INSTRUMENT_MAP = {
    "UUUU": 3024,      # Energy Fuels
    "XLU": 1130,       # Utilities ETF
    "CVX": 1049,       # Chevron
    "ETH": 100001,     # Ethereum
    "HOOD": 2011684,   # Robinhood
    "SOL": 100016,     # Solana
    "CAT": 1012,       # Caterpillar
    "SPX500": 1001,    # S&P 500
    "BTC": 100000,     # Bitcoin
    "HK-2348": 2348,   # China Hongqiao
    "Space-Investor": None  # Copy trader (no instrument ID)
}

def get_headers():
    """Generate eToro API headers"""
    return {
        "x-api-key": API_KEY,
        "x-user-key": USER_KEY,
        "x-request-id": str(uuid.uuid4()),
        "Content-Type": "application/json"
    }

def get_instrument_rate(instrument_id):
    """Query eToro for current instrument price"""
    try:
        url = f"{BASE_URL}/api/v1/market-data/instruments/rates?instrumentIds={instrument_id}"
        response = requests.get(url, headers=get_headers(), timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if "rates" in data and len(data["rates"]) > 0:
                rate_data = data["rates"][0]
                # Use lastExecution (most recent trade price) or bid
                return rate_data.get("lastExecution") or rate_data.get("bid")
        return None
    except Exception as e:
        print(f"  Error fetching rate for {instrument_id}: {e}")
        return None

def get_order_details(order_id):
    """Query eToro for order details (P&L, current price)"""
    try:
        url = f"{BASE_URL}/api/v1/trading/info/real/orders/{order_id}"
        response = requests.get(url, headers=get_headers(), timeout=5)
        
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"  Error fetching order {order_id}: {e}")
        return None

def update_live_prices():
    """Update all tracked trades with live prices"""
    print("Fetching LIVE prices from eToro API (ofs101clawRW)...\n")
    
    # Load tracked trades
    with open(TRACKED_TRADES_FILE, 'r') as f:
        tracked = json.load(f)
    
    updated_count = 0
    
    for trade in tracked["orders"]:
        symbol = trade["symbol"]
        order_id = trade["order_id"]
        
        print(f"Updating {symbol} (Order: {order_id})...")
        
        # First, try to get real order data if it's a valid eToro order
        if not order_id.endswith("_position"):
            order_data = get_order_details(order_id)
            if order_data:
                # Real order - use actual data
                if "CurrentRate" in order_data:
                    trade["current_price"] = order_data["CurrentRate"]
                    updated_count += 1
                    print(f"  ✓ Live price: ${order_data['CurrentRate']}")
                
                if "NetProfit" in order_data:
                    trade["current_pnl"] = order_data["NetProfit"]
                    print(f"  ✓ Live P&L: ${order_data['NetProfit']}")
                
                if "StatusID" in order_data:
                    status_map = {1: "PENDING", 2: "EXECUTED", 3: "CANCELLED", 4: "REJECTED", 7: "EXECUTED", 11: "PENDING_EXECUTION"}
                    trade["status"] = status_map.get(order_data["StatusID"], "UNKNOWN")
                
                continue
        
        # For manual positions, get live market rate
        instrument_id = INSTRUMENT_MAP.get(symbol)
        if instrument_id:
            live_rate = get_instrument_rate(instrument_id)
            if live_rate:
                old_price = trade.get("current_price", trade["price"])
                trade["current_price"] = live_rate
                
                # Calculate P&L based on live price
                if trade["price"] > 0:
                    pnl_pct = ((live_rate - trade["price"]) / trade["price"]) * 100
                    pnl_amount = trade["amount"] * (pnl_pct / 100)
                    trade["current_pnl"] = pnl_amount
                
                updated_count += 1
                print(f"  ✓ Live price: ${live_rate} (was ${old_price})")
                print(f"  ✓ Calculated P&L: ${trade['current_pnl']:.2f}")
            else:
                print(f"  ✗ Could not fetch live price")
        else:
            print(f"  → No instrument ID (copy trader or unknown)")
        
        trade["last_price_update"] = datetime.now(pytz.timezone('Asia/Jerusalem')).isoformat()
    
    # Save updated data
    with open(TRACKED_TRADES_FILE, 'w') as f:
        json.dump(tracked, f, indent=2)
    
    print(f"\n✓ Updated {updated_count} positions with LIVE eToro data")
    print(f"Saved to: {TRACKED_TRADES_FILE}")
    
    return tracked

if __name__ == "__main__":
    update_live_prices()
    print("\n✓ Live price update complete!")
