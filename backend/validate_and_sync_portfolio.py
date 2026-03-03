#!/usr/bin/env python3
"""
Real-Time Portfolio Validator & Syncer
Runs every 30 seconds to ensure dashboard shows EXACTLY what's in eToro
"""

import requests
import json
import uuid
import sys
from datetime import datetime
import pytz

API_KEY = "sdgdskldFPLGfjHn1421dgnlxdGTbngdflg6290bRjslfihsjhSDsdgGHH25hjf"
USER_KEY = "eyJjaSI6IjYwY2FiYjBiLTU1OTctNDQ4NS04ZjYzLTdlOWUwNTZlMGJiOCIsImVhbiI6IlVucmVnaXN0ZXJlZEFwcGxpY2F0aW9uIiwiZWsiOiJCRm01a3NkSUFSY29yS0FhTENwcURRLUItb09QdmNNUHFmTDNyem9NemdpTGx6NEItRjh5LWozNmY2dGhZVVpqWXoxeVhrbi52M3NYWFdCUUkwcGdmUExBbi1UNFhnZS03SWVWa0UzaEJiTV8ifQ__"
BASE_URL = "https://public-api.etoro.com"

TRACKED_TRADES_FILE = "/home/ofer/clawbot-reports/data/tracked-trades.json"
TRADES_FILE = "/home/ofer/clawbot-reports/trades.json"

def get_headers():
    return {
        "x-api-key": API_KEY,
        "x-user-key": USER_KEY,
        "X-Request-Id": str(uuid.uuid4())
    }

def validate_etoro_position(order_id):
    """Query eToro API to check if position is still open"""
    url = f"{BASE_URL}/api/v1/trading/info/real/orders/{order_id}"
    
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            positions = data.get('positions', [])
            
            # Check if any position is open
            for pos in positions:
                if pos.get('isOpen'):
                    return {
                        'is_open': True,
                        'position_id': pos.get('positionID'),
                        'units': pos.get('units'),
                        'rate': pos.get('rate')
                    }
            
            return {'is_open': False, 'reason': 'no_open_positions'}
        else:
            return {'is_open': 'UNKNOWN', 'reason': f'api_error_{response.status_code}'}
    
    except Exception as e:
        return {'is_open': 'UNKNOWN', 'reason': str(e)}

def build_real_portfolio():
    """Build list of REAL open positions"""
    
    with open(TRACKED_TRADES_FILE, 'r') as f:
        tracked = json.load(f)
    
    real_positions = []
    closed_positions = []
    
    for trade in tracked['orders']:
        order_id = trade['order_id']
        symbol = trade['symbol']
        
        # Manual positions (snapshot data) - assume open unless marked otherwise
        if not order_id.isdigit():
            if trade.get('status') in ['EXECUTED', 'PENDING']:
                real_positions.append(trade)
            continue
        
        # eToro API positions - validate
        validation = validate_etoro_position(order_id)
        
        if validation['is_open'] == True:
            # Update trade with latest data
            trade['position_id'] = validation.get('position_id')
            trade['units'] = validation.get('units')
            trade['current_price'] = validation.get('rate')
            trade['last_validated'] = datetime.now(pytz.timezone('Asia/Jerusalem')).isoformat()
            real_positions.append(trade)
        elif validation['is_open'] == False:
            trade['status'] = 'CLOSED'
            trade['closed_at'] = datetime.now(pytz.timezone('Asia/Jerusalem')).isoformat()
            closed_positions.append(trade)
        else:
            # API error - keep for now but flag
            trade['validation_warning'] = validation['reason']
            real_positions.append(trade)
    
    return real_positions, closed_positions

def update_dashboard():
    """Update trades.json with real portfolio"""
    
    real_positions, closed = build_real_portfolio()
    
    # Load existing trades.json
    with open(TRADES_FILE, 'r') as f:
        trades_data = json.load(f)
    
    # Build holdings from real positions
    holdings = []
    total_pnl = 0
    total_equity = 0
    
    for pos in real_positions:
        current_price = pos.get('current_price', pos.get('price', 0))
        entry_price = pos.get('price', 0)
        amount = pos.get('amount', 0)
        units = amount / entry_price if entry_price > 0 else 0
        
        pnl = pos.get('current_pnl', 0)
        current_value = amount + pnl
        
        holding = {
            'position_id': pos.get('position_id', pos['order_id']),
            'symbol': pos['symbol'],
            'name': pos['symbol'],
            'type': 'crypto' if pos['symbol'] in ['BTC', 'ETH', 'SOL', 'XRP'] else 'stock',
            'current_price': current_price,
            'entry_price': entry_price,
            'units': units,
            'amount': amount,
            'current_value': current_value,
            'pnl': pnl,
            'pnl_percent': (pnl / amount * 100) if amount > 0 else 0,
            'leverage': pos.get('leverage', 1),
            'status': pos.get('status', 'EXECUTED'),
            'entry_time': pos['timestamp'],
            'is_bot_trade': pos.get('is_bot_trade', False),
            'trade_source': pos.get('trade_source', '🤖 Bot' if pos.get('is_bot_trade') else '👤 Manual'),
            'trader': pos.get('trader', 'OfsInvest' if pos.get('is_bot_trade') else 'Manual')
        }
        
        holdings.append(holding)
        total_pnl += pnl
        total_equity += current_value
    
    # Calculate bot stats
    bot_holdings = [h for h in holdings if h['is_bot_trade']]
    bot_total_amount = sum(h['amount'] for h in bot_holdings)
    bot_total_value = sum(h['current_value'] for h in bot_holdings)
    bot_total_pnl = sum(h['pnl'] for h in bot_holdings)
    bot_budget = 1700
    
    # Update trades.json
    trades_data['holdings'] = holdings
    trades_data['last_update'] = datetime.now(pytz.timezone('Asia/Jerusalem')).isoformat()
    trades_data['stats'] = {
        'total_positions': len(holdings),
        'bot_positions': sum(1 for h in holdings if h['is_bot_trade']),
        'manual_positions': sum(1 for h in holdings if not h['is_bot_trade']),
        'total_orders': len(real_positions),
        'bot_orders': sum(1 for p in real_positions if p.get('is_bot_trade')),
        'manual_orders': sum(1 for p in real_positions if not p.get('is_bot_trade'))
    }
    
    # Add bot key (CRITICAL for dashboard)
    trades_data['bot'] = {
        'budget': bot_budget,
        'current_value': bot_total_value,
        'invested': bot_total_amount,
        'cash': bot_budget - bot_total_amount,
        'pnl': bot_total_pnl,
        'pnl_percent': (bot_total_pnl / bot_total_amount * 100) if bot_total_amount > 0 else 0,
        'positions': len(bot_holdings)
    }
    
    # Save
    with open(TRADES_FILE, 'w') as f:
        json.dump(trades_data, f, indent=2)
    
    return {
        'real_positions': len(real_positions),
        'closed_positions': len(closed),
        'bot_positions': trades_data['stats']['bot_positions'],
        'manual_positions': trades_data['stats']['manual_positions']
    }

if __name__ == "__main__":
    try:
        result = update_dashboard()
        print(f"✅ Portfolio validated & synced")
        print(f"   Real positions: {result['real_positions']}")
        print(f"   Bot: {result['bot_positions']}, Manual: {result['manual_positions']}")
        print(f"   Closed: {result['closed_positions']}")
        sys.exit(0)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)
