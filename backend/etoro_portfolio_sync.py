#!/usr/bin/env python3
"""
eToro Portfolio Sync - Complete Account Synchronization
Fetches ALL positions, orders, and account data from eToro
Distinguishes between bot trades (OfsInvest) and manual trades
"""

import json
import requests
from datetime import datetime
import pytz
import os
import uuid

# eToro API Configuration
BASE_URL = "https://public-api.etoro.com"
API_KEY = "sdgdskldFPLGfjHn1421dgnlxdGTbngdflg6290bRjslfihsjhSDsdgGHH25hjf"
USER_KEY = "eyJjaSI6IjYwY2FiYjBiLTU1OTctNDQ4NS04ZjYzLTdlOWUwNTZlMGJiOCIsImVhbiI6IlVucmVnaXN0ZXJlZEFwcGxpY2F0aW9uIiwiZWsiOiJCRm01a3NkSUFSY29yS0FhTENwcURRLUItb09QdmNNUHFmTDNyem9NemdpTGx6NEItRjh5LWozNmY2dGhZVVpqWXoxeVhrbi52M3NYWFdCUUkwcGdmUExBbi1UNFhnZS03SWVWa0UzaEJiTV8ifQ__"
CID = "28376799"  # Real account CID

def get_headers():
    """Generate headers with unique request ID"""
    return {
        "x-api-key": API_KEY,
        "x-user-key": USER_KEY,
        "x-request-id": str(uuid.uuid4()),
        "Content-Type": "application/json"
    }

# Track which trades are bot-executed
BOT_TRADES_FILE = "/home/ofer/clawbot-reports/data/bot-trades.json"

def load_bot_trades():
    """Load list of bot-executed trade/order IDs"""
    if os.path.exists(BOT_TRADES_FILE):
        with open(BOT_TRADES_FILE, 'r') as f:
            return json.load(f)
    return {"orders": [], "positions": []}

def save_bot_trades(bot_trades):
    """Save bot trade tracking"""
    with open(BOT_TRADES_FILE, 'w') as f:
        json.dump(bot_trades, f, indent=2)

def mark_as_bot_trade(order_id=None, position_id=None):
    """Mark a trade as bot-executed"""
    bot_trades = load_bot_trades()
    if order_id:
        if order_id not in bot_trades["orders"]:
            bot_trades["orders"].append(order_id)
    if position_id:
        if position_id not in bot_trades["positions"]:
            bot_trades["positions"].append(position_id)
    save_bot_trades(bot_trades)

def get_account_info():
    """Fetch account balance and equity"""
    try:
        # Note: This endpoint might not exist in Public API
        # Will need to calculate from positions
        return {
            "balance": 0,
            "equity": 0,
            "available": 0
        }
    except Exception as e:
        print(f"Error fetching account info: {e}")
        return None

def get_all_positions():
    """Fetch all open positions"""
    try:
        url = f"{BASE_URL}/api/v1/trading/info/real/positions"
        response = requests.get(url, headers=get_headers())
        
        if response.status_code == 200:
            data = response.json()
            return data.get("positions", [])
        else:
            print(f"Error fetching positions: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Error fetching positions: {e}")
        return []

def get_all_orders():
    """Fetch all orders (pending, executed, cancelled)"""
    try:
        url = f"{BASE_URL}/api/v1/trading/info/real/orders"
        response = requests.get(url, headers=get_headers())
        
        if response.status_code == 200:
            data = response.json()
            return data.get("orders", [])
        else:
            print(f"Error fetching orders: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Error fetching orders: {e}")
        return []

def get_instrument_details(instrument_ids):
    """Fetch details for multiple instruments"""
    if not instrument_ids:
        return {}
    
    try:
        ids_str = ",".join(str(id) for id in instrument_ids)
        url = f"{BASE_URL}/api/v1/market-data/instruments/rates?instrumentIds={ids_str}"
        response = requests.get(url, headers=get_headers())
        
        if response.status_code == 200:
            data = response.json()
            # Convert to dict keyed by instrument ID
            return {item["InstrumentID"]: item for item in data.get("rates", [])}
        else:
            print(f"Error fetching instrument details: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Error fetching instrument details: {e}")
        return {}

def map_order_status(status_id):
    """Map eToro order status ID to readable status"""
    status_map = {
        1: "PENDING",
        2: "EXECUTED",
        3: "CANCELLED",
        4: "REJECTED",
        11: "PENDING_EXECUTION"
    }
    return status_map.get(status_id, f"UNKNOWN_{status_id}")

def sync_portfolio():
    """Main sync function - fetch everything from eToro"""
    print("Syncing portfolio with eToro...")
    
    # Load bot trades tracking
    bot_trades = load_bot_trades()
    
    # Fetch all data
    positions = get_all_positions()
    orders = get_all_orders()
    
    # Get unique instrument IDs
    instrument_ids = set()
    for pos in positions:
        instrument_ids.add(pos.get("InstrumentID"))
    for order in orders:
        instrument_ids.add(order.get("InstrumentID"))
    
    # Fetch instrument details (current prices, names, etc.)
    instruments = get_instrument_details(list(instrument_ids))
    
    # Calculate total portfolio value
    total_equity = 0
    total_pnl = 0
    
    # Process positions
    holdings = []
    for pos in positions:
        inst_id = pos.get("InstrumentID")
        inst_info = instruments.get(inst_id, {})
        
        amount = pos.get("Amount", 0)
        invested = pos.get("Invested", 0)
        current_value = pos.get("NetProfit", 0) + invested
        pnl = pos.get("NetProfit", 0)
        
        total_equity += current_value
        total_pnl += pnl
        
        # Check if this is a bot trade
        position_id = pos.get("PositionID")
        is_bot = position_id in bot_trades["positions"]
        
        holding = {
            "position_id": position_id,
            "symbol": inst_info.get("SymbolFull", f"ID_{inst_id}"),
            "name": inst_info.get("InstrumentDisplayName", "Unknown"),
            "type": determine_asset_type(inst_id),
            "current_price": inst_info.get("Bid", 0),
            "entry_price": invested / amount if amount != 0 else 0,
            "units": amount,
            "amount": invested,
            "current_value": current_value,
            "pnl": pnl,
            "pnl_percent": (pnl / invested * 100) if invested != 0 else 0,
            "leverage": pos.get("Leverage", 1),
            "status": "ACTIVE",
            "entry_time": pos.get("OpenDateTime", ""),
            "is_bot_trade": is_bot,
            "trade_source": "🤖 Bot" if is_bot else "👤 Manual"
        }
        holdings.append(holding)
    
    # Process orders (including cancelled)
    all_trades = []
    for order in orders:
        inst_id = order.get("InstrumentID")
        inst_info = instruments.get(inst_id, {})
        order_id = order.get("OrderID")
        
        # Check if this is a bot trade
        is_bot = order_id in bot_trades["orders"]
        
        status = map_order_status(order.get("StatusID"))
        
        trade = {
            "id": str(order_id),
            "timestamp": order.get("OpenDateTime", ""),
            "symbol": inst_info.get("SymbolFull", f"ID_{inst_id}"),
            "action": "BUY" if order.get("IsBuy") else "SELL",
            "type": "OPEN",
            "amount": order.get("Amount", 0),
            "price": order.get("OpenRate", 0),
            "units": order.get("Amount", 0) / order.get("OpenRate", 1) if order.get("OpenRate", 0) != 0 else 0,
            "leverage": order.get("Leverage", 1),
            "reason": "Manual trade" if not is_bot else "OfsInvest automated trade",
            "status": status,
            "is_bot_trade": is_bot,
            "trade_source": "🤖 Bot" if is_bot else "👤 Manual"
        }
        all_trades.append(trade)
    
    # Sort trades by timestamp
    all_trades.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Calculate account info
    # Note: We don't have direct balance endpoint, so we estimate
    # Assuming starting capital was $1700 (from trades.json)
    initial_capital = 1700
    current_value = initial_capital + total_pnl
    cash = current_value - total_equity  # Rough estimate
    
    # Build performance history (we'll merge with existing)
    performance_point = {
        "timestamp": datetime.now(pytz.timezone('Asia/Jerusalem')).isoformat(),
        "value": current_value,
        "pnl": total_pnl
    }
    
    # Prepare output data
    portfolio_data = {
        "last_sync": datetime.now(pytz.timezone('Asia/Jerusalem')).isoformat(),
        "sync_source": "eToro API",
        "account": {
            "start_date": "2026-03-02",
            "initial_capital": initial_capital,
            "current_value": current_value,
            "cash": cash,
            "equity": total_equity,
            "total_pnl": total_pnl,
            "pnl_percent": (total_pnl / initial_capital * 100) if initial_capital != 0 else 0
        },
        "holdings": holdings,
        "trades": all_trades,
        "performance_point": performance_point,
        "stats": {
            "total_positions": len(holdings),
            "bot_positions": sum(1 for h in holdings if h["is_bot_trade"]),
            "manual_positions": sum(1 for h in holdings if not h["is_bot_trade"]),
            "total_orders": len(all_trades),
            "bot_orders": sum(1 for t in all_trades if t["is_bot_trade"]),
            "manual_orders": sum(1 for t in all_trades if not t["is_bot_trade"])
        }
    }
    
    print(f"Synced: {len(holdings)} positions, {len(all_trades)} orders")
    print(f"Bot: {portfolio_data['stats']['bot_positions']} positions, {portfolio_data['stats']['bot_orders']} orders")
    print(f"Manual: {portfolio_data['stats']['manual_positions']} positions, {portfolio_data['stats']['manual_orders']} orders")
    
    return portfolio_data

def determine_asset_type(instrument_id):
    """Determine asset type from instrument ID"""
    # Crypto: 100000+
    if instrument_id >= 100000:
        return "crypto"
    # Stocks: typically lower IDs
    return "stock"

def merge_with_existing_data(new_data, existing_file='/home/ofer/clawbot-reports/trades.json'):
    """Merge new sync data with existing performance history"""
    # Load existing data
    if os.path.exists(existing_file):
        with open(existing_file, 'r') as f:
            existing = json.load(f)
    else:
        existing = {"performance_history": []}
    
    # Merge performance history (avoid duplicates)
    existing_history = existing.get("performance_history", [])
    new_point = new_data["performance_point"]
    
    # Check if we already have a point within the last minute
    last_timestamp = existing_history[-1]["timestamp"] if existing_history else None
    if last_timestamp:
        from dateutil import parser
        last_dt = parser.parse(last_timestamp)
        new_dt = parser.parse(new_point["timestamp"])
        time_diff = (new_dt - last_dt).total_seconds()
        
        # Only add if more than 60 seconds since last point
        if time_diff > 60:
            existing_history.append(new_point)
    else:
        existing_history.append(new_point)
    
    # Limit history to last 1000 points
    if len(existing_history) > 1000:
        existing_history = existing_history[-1000:]
    
    # Build final output
    output = {
        "last_update": new_data["last_sync"],
        "account": new_data["account"],
        "performance_history": existing_history,
        "holdings": new_data["holdings"],
        "trades": new_data["trades"],
        "stats": new_data["stats"]
    }
    
    return output

def save_portfolio_data(data, output_file='/home/ofer/clawbot-reports/trades.json'):
    """Save portfolio data to JSON"""
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    # Sync portfolio
    new_data = sync_portfolio()
    
    # Merge with existing
    merged_data = merge_with_existing_data(new_data)
    
    # Save
    save_portfolio_data(merged_data)
    
    print(f"\n✓ Portfolio sync complete")
    print(f"Total Value: ${merged_data['account']['current_value']:.2f}")
    print(f"Total P&L: ${merged_data['account']['total_pnl']:.2f} ({merged_data['account']['pnl_percent']:.2f}%)")
