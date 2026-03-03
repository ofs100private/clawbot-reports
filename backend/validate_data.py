#!/usr/bin/env python3
"""
Data Quality Validator - Zero tolerance for errors
Runs before every git push, every sync, every update
"""

import json
import sys
import os
from datetime import datetime
import pytz

def load(path):
    """Load JSON file"""
    with open(path, 'r') as f:
        return json.load(f)

def save_error_log(errors, warnings):
    """Save errors to log file"""
    log_file = '/home/ofer/.openclaw/workspace-ofsinvest/memory/data-quality-errors.json'
    
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            log = json.load(f)
    else:
        log = {"validation_runs": []}
    
    log["validation_runs"].append({
        "timestamp": datetime.now(pytz.timezone('Asia/Jerusalem')).isoformat(),
        "errors": errors,
        "warnings": warnings
    })
    
    # Keep last 100 runs
    log["validation_runs"] = log["validation_runs"][-100:]
    
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, 'w') as f:
        json.dump(log, f, indent=2)

def validate_all():
    """Run all validation checks"""
    errors = []
    warnings = []
    
    base_path = '/home/ofer/clawbot-reports'
    
    # 1. Load all data files
    try:
        bot_trades = load(f'{base_path}/data/bot-trades.json')
        tracked = load(f'{base_path}/data/tracked-trades.json')
        trades = load(f'{base_path}/trades.json')
    except Exception as e:
        errors.append(f"Failed to load files: {e}")
        return errors, warnings
    
    # 2. Validate bot trades are marked correctly
    bot_order_ids = {str(o['orderId']) for o in bot_trades.get('orders', [])}
    for trade in tracked.get('orders', []):
        trade_id = str(trade['order_id'])
        if trade_id in bot_order_ids:
            if not trade.get('is_bot_trade'):
                errors.append(f"Bot trade {trade_id} ({trade.get('symbol')}) not marked as is_bot_trade=true")
            if trade.get('trade_source') != '🤖 Bot':
                errors.append(f"Bot trade {trade_id} ({trade.get('symbol')}) has wrong trade_source: {trade.get('trade_source')}")
    
    # 3. Validate status mapping (CRITICAL)
    STATUS_MAP = {
        1: "PENDING",
        2: "PARTIALLY_FILLED",
        3: "EXECUTED",
        4: "CANCELLED",
        5: "REJECTED",
        11: "PENDING_EXECUTION"
    }
    
    for trade in tracked.get('orders', []):
        status = trade.get('status', '')
        # Check for known wrong mappings
        if status == "CANCELLED" and 'statusId' not in trade:
            # If we don't have statusId but it's marked CANCELLED, verify it's not a data error
            if trade.get('is_open') == True:
                errors.append(f"CRITICAL: Order {trade['order_id']} ({trade.get('symbol')}) marked CANCELLED but is_open=True")
    
    # 4. Validate bot budget
    bot_positions = [t for t in tracked.get('orders', [])
                     if t.get('is_bot_trade') and t.get('status') in ['EXECUTED', 'PENDING']]
    bot_total = sum(p.get('amount', 0) for p in bot_positions)
    
    if bot_total > 1700:
        errors.append(f"Bot over budget: ${bot_total:.2f} > $1700")
    elif bot_total > 1700 * 0.92:  # 92% threshold
        warnings.append(f"Bot budget usage high: ${bot_total:.2f} / $1700 ({bot_total/1700*100:.1f}%)")
    
    # 5. Validate all bot trades exist in trades.json
    trades_list = trades.get('trades', [])
    for bot_order_id in bot_order_ids:
        found = any(str(t.get('id')) == bot_order_id for t in trades_list)
        if not found:
            errors.append(f"Bot trade {bot_order_id} missing from trades.json")
    
    # 7. Validate holdings vs active positions
    active_orders = [t for t in tracked.get('orders', [])
                     if t.get('status') in ['EXECUTED', 'PENDING', 'PENDING_EXECUTION']]
    holdings = trades.get('holdings', [])
    
    if len(active_orders) != len(holdings):
        warnings.append(f"Position count mismatch: {len(active_orders)} active orders, {len(holdings)} holdings")
    
    # 7b. Validate bot cash reserve
    bot_holdings = [h for h in holdings if h.get('is_bot_trade') or h.get('trader') == 'OfsInvest']
    bot_invested = sum(h.get('amount', 0) for h in bot_holdings)
    bot_cash = 1700 - bot_invested
    min_bot_cash = 1700 * 0.08  # 8% of bot budget
    
    if bot_cash < min_bot_cash:
        errors.append(f"Bot cash below minimum reserve: ${bot_cash:.2f} < ${min_bot_cash:.2f} (invested ${bot_invested:.2f} / $1700)")
    elif bot_cash < 200:  # Warn if less than $200
        warnings.append(f"Bot cash getting low: ${bot_cash:.2f} remaining (invested ${bot_invested:.2f} / $1700)")
    
    # 8. Validate P&L calculations
    for holding in holdings:
        symbol = holding.get('symbol', 'UNKNOWN')
        current_price = holding.get('current_price', 0)
        entry_price = holding.get('entry_price', 0)
        units = holding.get('units', 0)
        stored_pnl = holding.get('pnl', 0)
        
        if current_price > 0 and entry_price > 0 and units > 0:
            calculated_pnl = (current_price - entry_price) * units
            diff = abs(calculated_pnl - stored_pnl)
            
            if diff > 5.0:  # $5 tolerance for rounding/fees
                warnings.append(f"P&L mismatch {symbol}: calculated=${calculated_pnl:.2f}, stored=${stored_pnl:.2f}, diff=${diff:.2f}")
    
    # 9. Validate JSON integrity
    try:
        json.dumps(bot_trades)
        json.dumps(tracked)
        json.dumps(trades)
    except Exception as e:
        errors.append(f"JSON serialization error: {e}")
    
    # 10. Validate required fields
    for trade in tracked.get('orders', []):
        required = ['order_id', 'symbol', 'action', 'amount', 'status', 'timestamp']
        missing = [f for f in required if f not in trade or trade[f] is None]
        if missing:
            errors.append(f"Trade {trade.get('order_id')} missing fields: {missing}")
    
    return errors, warnings

def main():
    """Main validation routine"""
    print("=" * 60)
    print("Data Quality Validation - Zero Tolerance")
    print("=" * 60)
    
    errors, warnings = validate_all()
    
    # Save to log
    save_error_log(errors, warnings)
    
    # Report results
    if errors:
        print("\n❌ CRITICAL ERRORS FOUND:")
        for e in errors:
            print(f"  - {e}")
        print("\n🚫 VALIDATION FAILED - DO NOT PUSH")
        print("Fix errors or query eToro API for ground truth")
        sys.exit(1)
    
    if warnings:
        print("\n⚠️  WARNINGS (non-blocking):")
        for w in warnings:
            print(f"  - {w}")
        print("\n✅ Validation passed with warnings")
        sys.exit(0)
    
    print("\n✅ ALL VALIDATIONS PASSED - DATA QUALITY PERFECT")
    sys.exit(0)

if __name__ == "__main__":
    main()
