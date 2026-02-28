import json
from datetime import datetime

file_path = '/home/ofer/.openclaw/workspace/clawbot-reports/trades.json'

with open(file_path, 'r') as f:
    data = json.load(f)

micha = data['micha']

# Fetched prices
new_prices = {
    "NVDA": 181.76,
    "AAPL": 270.22,
    "MSFT": 394.89,
    "GOOGL": 308.82,
    "AMD": 200.53,
    "AVGO": 317.55,
    "TSM": 374.61,
    "META": 646.28,
    "AMZN": 206.68,
    "QQQ": 605.82,
    "SPY": 684.02,
    "COST": 992.77,
    "NFLX": 91.2,
    "LLY": 1031.62
}

micha['prices'].update(new_prices)

# New trade: sell NVDA
trade = {
    "date": "2026-02-27",
    "action": "sell",
    "ticker": "NVDA",
    "units": 0.1326,
    "price": 181.76,
    "amount": round(0.1326 * 181.76, 2),
    "reason": "Broke below MA-150. Discipline cut.",
    "pnl": round((181.76 - 138.19) * 0.1326, 2)
}

micha['trades'].append(trade)

# Remove NVDA from holdings
micha['holdings'] = [h for h in micha['holdings'] if h['sym'] != "NVDA"]

# Update cash (assume commission 1)
commission = 1.0
micha['cash'] = round(micha['cash'] + trade['amount'] - commission, 2)

# Update totalPnl
micha['totalPnl'] = round(micha['totalPnl'] + trade['pnl'] - commission, 2)

# Update pnlHistory for today
today = "2026-02-27"
found = False
for entry in micha['pnlHistory']:
    if entry['date'] == today:
        entry['pnl'] = round(entry['pnl'] + trade['pnl'] - commission, 2)
        found = True
        break
if not found:
    micha['pnlHistory'].append({"date": today, "pnl": round(trade['pnl'] - commission, 2)})

# Update currentPrice in remaining holdings and recalculate pnl
for h in micha['holdings']:
    sym = h['sym']
    if sym in new_prices:
        h['currentPrice'] = new_prices[sym]
        h['pnl'] = round((new_prices[sym] - h['avgPrice']) * h['units'], 2)

# Update lastUpdate
micha['lastUpdate'] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + "+02:00"

with open(file_path, 'w') as f:
    json.dump(data, f, indent=2)
print("Updated trades.json successfully.")