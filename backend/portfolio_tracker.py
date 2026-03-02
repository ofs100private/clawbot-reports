#!/usr/bin/env python3
"""
Portfolio Tracker - Track all trades locally and sync status with eToro
Since eToro Public API doesn't provide "list all positions" endpoint,
we track trades locally and query individual status
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

TRACKED_TRADES_FILE = "/home/ofer/clawbot-reports/data/tracked-trades.json"
BOT_TRADES_FILE = "/home/ofer/clawbot-reports/data/bot-trades.json"

def get_headers():
    """Generate headers with unique request ID"""
    return {
        "x-api-key": API_KEY,
        "x-user-key": USER_KEY,
        "x-request-id": str(uuid.uuid4()),
        "Content-Type": "application/json"
    }

def load_tracked_trades():
    """Load all trades we're tracking"""
    if os.path.exists(TRACKED_TRADES_FILE):
        with open(TRACKED_TRADES_FILE, 'r') as f:
            return json.load(f)
    return {"orders": []}

def save_tracked_trades(data):
    """Save tracked trades"""
    os.makedirs(os.path.dirname(TRACKED_TRADES_FILE), exist_ok=True)
    with open(TRACKED_TRADES_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_bot_trades():
    """Load bot trade markers"""
    if os.path.exists(BOT_TRADES_FILE):
        with open(BOT_TRADES_FILE, 'r') as f:
            return json.load(f)
    return {"orders": [], "positions": []}

def add_trade_to_tracking(order_id, symbol, action, amount, price, leverage, is_bot=False, reason=""):
    """Add a new trade to tracking"""
    tracked = load_tracked_trades()
    
    trade = {
        "order_id": str(order_id),
        "symbol": symbol,
        "action": action,
        "amount": amount,
        "price": price,
        "leverage": leverage,
        "is_bot": is_bot,
        "reason": reason,
        "timestamp": datetime.now(pytz.timezone('Asia/Jerusalem')).isoformat(),
        "status": "UNKNOWN"
    }
    
    # Check if already exists
    existing = next((t for t in tracked["orders"] if t["order_id"] == str(order_id)), None)
    if existing:
        # Update existing
        existing.update(trade)
    else:
        # Add new
        tracked["orders"].append(trade)
    
    save_tracked_trades(tracked)
    print(f"Added/updated trade: {order_id}")

def get_order_status(order_id):
    """Query eToro for order status"""
    try:
        url = f"{BASE_URL}/api/v1/trading/info/real/orders/{order_id}"
        response = requests.get(url, headers=get_headers())
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"Error querying order {order_id}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error querying order {order_id}: {e}")
        return None

def map_status_id(status_id):
    """Map eToro status ID to readable status"""
    status_map = {
        1: "PENDING",
        2: "EXECUTED",
        3: "CANCELLED",
        4: "REJECTED",
        11: "PENDING_EXECUTION"
    }
    return status_map.get(status_id, f"UNKNOWN_{status_id}")

def sync_all_tracked_trades():
    """Sync all tracked trades with eToro"""
    print("Syncing tracked trades with eToro...")
    tracked = load_tracked_trades()
    bot_trades = load_bot_trades()
    
    updated_count = 0
    api_failed_count = 0
    
    for trade in tracked["orders"]:
        order_id = trade["order_id"]
        old_status = trade.get("status", "UNKNOWN")
        
        # Query eToro
        order_data = get_order_status(order_id)
        
        if order_data and order_data.get("StatusID") is not None:
            status_id = order_data.get("StatusID")
            new_status = map_status_id(status_id)
            
            if new_status != old_status:
                trade["status"] = new_status
                trade["last_sync"] = datetime.now(pytz.timezone('Asia/Jerusalem')).isoformat()
                updated_count += 1
                print(f"  Order {order_id}: {old_status} → {new_status}")
                
                # Update additional details if available
                if "NetProfit" in order_data:
                    trade["current_pnl"] = order_data["NetProfit"]
                if "CurrentRate" in order_data:
                    trade["current_price"] = order_data["CurrentRate"]
        else:
            # API failed - keep existing status from tracked-trades.json
            api_failed_count += 1
            if old_status in ["UNKNOWN", "UNKNOWN_None", ""]:
                # If we never had a status, default to PENDING for new orders
                # Check if order is very old (>24h) - might be cancelled
                from dateutil import parser
                order_time = parser.parse(trade["timestamp"])
                now = datetime.now(pytz.timezone('Asia/Jerusalem'))
                hours_old = (now - order_time).total_seconds() / 3600
                
                if hours_old > 24:
                    print(f"  Order {order_id}: Assuming CANCELLED (>24h old, API unavailable)")
                    trade["status"] = "CANCELLED"
                else:
                    print(f"  Order {order_id}: Keeping local status or defaulting to PENDING")
                    # Keep existing status or set to PENDING if truly unknown
                    if old_status in ["UNKNOWN", "UNKNOWN_None", ""]:
                        trade["status"] = "PENDING"
    
    save_tracked_trades(tracked)
    print(f"Updated {updated_count} trades, {api_failed_count} API calls failed (using local status)")
    
    return tracked

def build_portfolio_from_tracked():
    """Build portfolio data from tracked trades"""
    tracked = sync_all_tracked_trades()
    bot_trades = load_bot_trades()
    
    # Separate active positions from all orders
    holdings = []
    all_trades = []
    
    total_pnl = 0
    total_equity = 0
    
    for trade in tracked["orders"]:
        order_id = trade["order_id"]
        is_bot = order_id in bot_trades["orders"]
        
        # Add to trades list
        trade_entry = {
            "id": order_id,
            "timestamp": trade["timestamp"],
            "symbol": trade["symbol"],
            "action": trade["action"],
            "type": "OPEN",
            "amount": trade["amount"],
            "price": trade["price"],
            "units": trade["amount"] / trade["price"] if trade["price"] > 0 else 0,
            "leverage": trade["leverage"],
            "reason": trade["reason"],
            "status": trade["status"],
            "is_bot_trade": is_bot,
            "trade_source": "🤖 Bot" if is_bot else "👤 Manual"
        }
        all_trades.append(trade_entry)
        
        # If not CANCELLED or REJECTED, consider it a holding
        # (includes EXECUTED, PENDING, PENDING_EXECUTION, or UNKNOWN if API unavailable)
        if trade["status"] not in ["CANCELLED", "REJECTED", "CLOSED"]:
            current_pnl = trade.get("current_pnl", 0)
            current_value = trade["amount"] + current_pnl
            
            holding = {
                "position_id": order_id,
                "symbol": trade["symbol"],
                "name": trade["symbol"],
                "type": "crypto" if trade["symbol"] in ["ETH", "BTC"] else "stock",
                "current_price": trade.get("current_price", trade["price"]),
                "entry_price": trade["price"],
                "units": trade["amount"] / trade["price"] if trade["price"] > 0 else 0,
                "amount": trade["amount"],
                "current_value": current_value,
                "pnl": current_pnl,
                "pnl_percent": (current_pnl / trade["amount"] * 100) if trade["amount"] > 0 else 0,
                "leverage": trade["leverage"],
                "status": trade["status"],
                "entry_time": trade["timestamp"],
                "is_bot_trade": is_bot,
                "trade_source": "🤖 Bot" if is_bot else "👤 Manual"
            }
            holdings.append(holding)
            
            total_pnl += current_pnl
            total_equity += current_value
    
    # Sort trades by timestamp
    all_trades.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Calculate account totals
    # Initial capital should be the sum of all invested amounts
    initial_capital = sum(t["amount"] for t in tracked["orders"] if t["status"] not in ["CANCELLED", "REJECTED"])
    current_value = initial_capital + total_pnl
    cash = current_value - total_equity
    
    # Build output
    portfolio_data = {
        "last_update": datetime.now(pytz.timezone('Asia/Jerusalem')).isoformat(),
        "account": {
            "start_date": "2026-03-02",
            "initial_capital": initial_capital,
            "current_value": current_value,
            "cash": cash,
            "equity": total_equity,
            "total_pnl": total_pnl,
            "pnl_percent": (total_pnl / initial_capital * 100) if initial_capital > 0 else 0
        },
        "holdings": holdings,
        "trades": all_trades,
        "stats": {
            "total_positions": len(holdings),
            "bot_positions": sum(1 for h in holdings if h["is_bot_trade"]),
            "manual_positions": sum(1 for h in holdings if not h["is_bot_trade"]),
            "total_orders": len(all_trades),
            "bot_orders": sum(1 for t in all_trades if t["is_bot_trade"]),
            "manual_orders": sum(1 for t in all_trades if not t["is_bot_trade"])
        }
    }
    
    print(f"\nPortfolio Summary:")
    print(f"  Holdings: {len(holdings)} ({portfolio_data['stats']['bot_positions']} bot, {portfolio_data['stats']['manual_positions']} manual)")
    print(f"  Orders: {len(all_trades)} ({portfolio_data['stats']['bot_orders']} bot, {portfolio_data['stats']['manual_orders']} manual)")
    print(f"  Value: ${current_value:.2f}, P&L: ${total_pnl:.2f} ({portfolio_data['account']['pnl_percent']:.2f}%)")
    
    return portfolio_data

def merge_with_performance_history(new_data, existing_file='/home/ofer/clawbot-reports/trades.json'):
    """Merge with existing performance history"""
    if os.path.exists(existing_file):
        with open(existing_file, 'r') as f:
            existing = json.load(f)
    else:
        existing = {"performance_history": []}
    
    # Add new performance point
    existing_history = existing.get("performance_history", [])
    new_point = {
        "timestamp": new_data["last_update"],
        "value": new_data["account"]["current_value"],
        "pnl": new_data["account"]["total_pnl"]
    }
    
    # Only add if >60 seconds since last point
    if existing_history:
        from dateutil import parser
        last_dt = parser.parse(existing_history[-1]["timestamp"])
        new_dt = parser.parse(new_point["timestamp"])
        if (new_dt - last_dt).total_seconds() > 60:
            existing_history.append(new_point)
    else:
        existing_history.append(new_point)
    
    # Limit to 1000 points
    if len(existing_history) > 1000:
        existing_history = existing_history[-1000:]
    
    # Build output
    output = {
        "last_update": new_data["last_update"],
        "account": new_data["account"],
        "performance_history": existing_history,
        "holdings": new_data["holdings"],
        "trades": new_data["trades"],
        "stats": new_data["stats"]
    }
    
    return output

def save_portfolio(data, output_file='/home/ofer/clawbot-reports/trades.json'):
    """Save portfolio data"""
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    # Build portfolio from tracked trades
    portfolio = build_portfolio_from_tracked()
    
    # Merge with history
    merged = merge_with_performance_history(portfolio)
    
    # Save
    save_portfolio(merged)
    
    print("\n✓ Portfolio sync complete")
