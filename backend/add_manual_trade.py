#!/usr/bin/env python3
"""
Manual Trade Entry Tool
Use this to record trades executed manually in eToro app/web
"""

import sys
import json
from datetime import datetime
import pytz

sys.path.insert(0, '/home/ofer/clawbot-reports/backend')
from portfolio_tracker import add_trade_to_tracking

def main():
    print("="*60)
    print("Manual Trade Entry Tool")
    print("="*60)
    
    # Collect trade details
    print("\nEnter trade details:")
    order_id = input("Order ID (from eToro): ").strip()
    symbol = input("Symbol (e.g., BTC, ETH, AAPL): ").strip().upper()
    action = input("Action (BUY/SELL): ").strip().upper()
    amount = float(input("Amount ($): ").strip())
    price = float(input("Price: ").strip())
    leverage = int(input("Leverage (1-5): ").strip())
    reason = input("Reason/Notes: ").strip()
    
    # Confirm
    print("\n" + "="*60)
    print("Trade Summary:")
    print(f"  Order ID: {order_id}")
    print(f"  Symbol: {symbol}")
    print(f"  Action: {action}")
    print(f"  Amount: ${amount}")
    print(f"  Price: ${price}")
    print(f"  Leverage: {leverage}x")
    print(f"  Reason: {reason}")
    print("  Source: 👤 Manual (Ofer)")
    print("="*60)
    
    confirm = input("\nAdd this trade? (yes/no): ").strip().lower()
    
    if confirm == "yes":
        add_trade_to_tracking(
            order_id=order_id,
            symbol=symbol,
            action=action,
            amount=amount,
            price=price,
            leverage=leverage,
            is_bot=False,
            reason=reason
        )
        print("\n✓ Trade added successfully!")
        print("Dashboard will update on next sync.")
    else:
        print("\n✗ Trade cancelled")

if __name__ == "__main__":
    main()
