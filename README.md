# 🎯 Real Money Trading Dashboard by OfsInvest

**Live Dashboard:** https://ofs100private.github.io/clawbot-reports/real-money-trading.html

Complete portfolio tracking system with automated bot trading and manual trade logging.

---

## 📊 Features

### Dashboard (real-money-trading.html)
- 🔴 **Live Breaking News** - Top 3 market-moving stories (updates every 5 min)
- 📊 **Sentiment Dashboard** - US Market, Crypto, Commodities, ETFs sentiment
- 😱 **Fear & Greed Index** - Real-time market sentiment gauge
- 📈 **Performance Graph** - Portfolio value over time with buy/sell markers
- 💼 **Current Positions** - All active holdings with P&L
- 📉 **TradingView Charts** - Embedded charts for each asset (MA 50/100/150 + volume)
- 🤖 **Bot vs Manual Indicators** - Clear badges showing trade source

### Historical Trades (historical-trades.html)
- Complete trade log with advanced filters
- Win rate, average trade, total P&L analytics
- Filter by: symbol, action, status, date range, source (bot/manual)
- Sortable table with full trade details

---

## 🤖 Bot vs Manual Tracking

Every trade is marked as either:
- **🤖 Bot** - Executed by OfsInvest autonomous system (purple badge)
- **👤 Manual** - Executed manually by Ofer (green badge)

This allows tracking which trades are automated vs human-initiated.

---

## 📁 Data Files

### `/data/tracked-trades.json`
Complete log of all trades with status tracking:
```json
{
  "orders": [
    {
      "order_id": "1373482995",
      "symbol": "ETH",
      "action": "BUY",
      "amount": 150,
      "price": 1945.76,
      "leverage": 1,
      "is_bot": true,
      "reason": "Expert 11-signal fusion",
      "timestamp": "2026-03-02T11:37:52+02:00",
      "status": "EXECUTED"
    }
  ]
}
```

### `/data/bot-trades.json`
List of bot-executed trade IDs:
```json
{
  "orders": ["1373482995"],
  "positions": []
}
```

### `/data/breaking-news.json`
Latest market news (3 items):
```json
{
  "last_update": "2026-03-02T20:48:21+02:00",
  "news": [
    {
      "title": "Iran conflict escalates...",
      "source": "Reuters",
      "time": "2026-03-02T20:45:00Z",
      "impact": "high",
      "url": "https://..."
    }
  ]
}
```

### `/data/sentiment.json`
Sentiment scores and Fear & Greed Index:
```json
{
  "fear_greed": {"value": 45, "label": "Neutral"},
  "sentiment": {
    "us_market": {"score": 65, "label": "Bullish", "trend": "up"},
    "crypto": {"score": 55, "label": "Neutral", "trend": "up"}
  }
}
```

---

## 🛠️ Backend Scripts

### Portfolio Sync
```bash
python3 /home/ofer/clawbot-reports/backend/portfolio_tracker.py
```
Syncs all tracked trades with eToro API and updates dashboard.

### Add Manual Trade
```bash
python3 /home/ofer/clawbot-reports/backend/add_manual_trade.py
```
Interactive CLI tool to record manually executed trades.

**Shortcut:**
```bash
bash /home/ofer/.openclaw/workspace/scripts/add-trade
```

### Mark Bot Trade
```bash
bash /home/ofer/.openclaw/workspace-ofsinvest/scripts/mark-bot-trade.sh order 1234567
```
Mark a specific trade as bot-executed.

### Full Update
```bash
bash /home/ofer/clawbot-reports/backend/update_all.sh
```
Runs all updates:
1. Portfolio sync
2. Breaking news fetch
3. Sentiment analysis

---

## ⚙️ Automated Updates

**Cron Job:** "Dashboard Data Updater"
- **Frequency:** Every 5 minutes
- **Model:** Grok (free)
- **Tasks:**
  1. Sync portfolio with eToro
  2. Fetch 3 breaking news items
  3. Analyze X/Twitter sentiment
  4. Calculate Fear & Greed Index
  5. Update all JSON data files

**Dashboard Auto-Refresh:**
- Portfolio data: Every 30 seconds
- News feed: Every 5 minutes
- Sentiment data: Every 5 minutes

---

## 📝 How to Add a Manual Trade

When you execute a trade manually in eToro app/web:

1. Run the add-trade command:
```bash
bash /home/ofer/.openclaw/workspace/scripts/add-trade
```

2. Enter the details:
```
Order ID (from eToro): 1234567890
Symbol (e.g., BTC, ETH, AAPL): BTC
Action (BUY/SELL): BUY
Amount ($): 200
Price: 69500
Leverage (1-5): 1
Reason/Notes: Manual buy on dip
```

3. Confirm and the trade will appear on the dashboard within 5 minutes.

---

## 🎯 OfsInvest Bot Trading

When OfsInvest autonomous system executes a trade:
1. Trade is executed via eToro API
2. Order ID is automatically recorded
3. Marked as bot trade in bot-trades.json
4. Added to tracked-trades.json
5. Appears on dashboard with 🤖 Bot badge

**No manual intervention needed for bot trades.**

---

## 📈 Data Flow

```
Bot Trade:
  OfsInvest → eToro API → Auto-record → Dashboard (🤖 Bot)

Manual Trade:
  Ofer → eToro App → Manual entry (CLI) → Dashboard (👤 Manual)

Dashboard Updates:
  Cron (5 min) → portfolio_tracker.py → trades.json → Dashboard refresh
```

---

## 🔧 Configuration

### eToro API Credentials
**Location:** `/home/ofer/.openclaw/workspace-ofsinvest/memory/etoro-credentials.md`

**DO NOT commit to git!**

### Initial Capital
Default: $1,700 (set in portfolio_tracker.py)

To change:
1. Edit `/home/ofer/clawbot-reports/backend/portfolio_tracker.py`
2. Find: `initial_capital = 1700`
3. Update value
4. Restart cron job

---

## 🚨 Troubleshooting

### Dashboard not updating?
```bash
# Check cron job status
bash /home/ofer/.openclaw/workspace/scripts/check-cron.sh

# Manual sync
bash /home/ofer/clawbot-reports/backend/update_all.sh
```

### Missing trades?
```bash
# View tracked trades
cat /home/ofer/clawbot-reports/data/tracked-trades.json

# Add missing trade
bash /home/ofer/.openclaw/workspace/scripts/add-trade
```

### Wrong bot/manual label?
```bash
# Mark order as bot
bash /home/ofer/.openclaw/workspace-ofsinvest/scripts/mark-bot-trade.sh order ORDER_ID

# Edit tracked-trades.json directly and change "is_bot": true/false
```

---

## 📊 Statistics

Current setup tracks:
- ✅ 4 orders (1 bot, 3 manual)
- ✅ Auto-sync every 5 minutes
- ✅ Live sentiment from X/Twitter
- ✅ Breaking news every 5 minutes
- ✅ TradingView charts for each position
- ✅ Complete historical log with filters

---

## 🔗 Links

- **Main Dashboard:** https://ofs100private.github.io/clawbot-reports/real-money-trading.html
- **Historical Trades:** https://ofs100private.github.io/clawbot-reports/historical-trades.html
- **Brain Map:** https://ofs100private.github.io/clawbot-reports/brainmap.html
- **GitHub Repo:** https://github.com/ofs100private/clawbot-reports

---

## 📜 Version History

- **v200** - Complete dashboard redesign (removed competition)
- **v201** - Added bot/manual tracking system (current)

---

**Last Updated:** 2026-03-02  
**Maintained by:** Ben (OfsInvest AI Assistant)
