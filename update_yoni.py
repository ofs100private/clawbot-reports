import json
import datetime

with open('trades.json', 'r') as f:
    data = json.load(f)

# Update lastUpdate
data['lastUpdate'] = '2026-02-28T05:16:00+02:00'

# Update prices
new_prices = {'NVDA':177.19,'AAPL':264.18,'MSFT':392.74,'GOOGL':311.76,'AMD':200.21,'AVGO':319.55,'TSM':374.58,'META':648.18,'AMZN':210,'PLTR':137.19,'SOFI':17.76,'COIN':175.85,'MARA':8.94,'RIOT':16.29}
data['prices'] = new_prices

# Update yoni
yoni = data['yoni']
yoni['cash'] = 195.24
yoni['totalPnl'] = -4.37

# Update pnlHistory, replace the last one if same date, else add
new_pnl_entry = {'date': '2026-02-28', 'pnl': -4.37}
if yoni['pnlHistory'][-1]['date'] == '2026-02-28':
    yoni['pnlHistory'][-1] = new_pnl_entry
else:
    yoni['pnlHistory'] += [new_pnl_entry]

# Update holdings
new_holdings = [
    {'sym':'AAPL','units':0.7574,'avgPrice':264.18,'currentPrice':264.18,'pnl':0},
    {'sym':'MSFT','units':0.5092,'avgPrice':392.74,'currentPrice':392.74,'pnl':0},
    {'sym':'TSM','units':0.5341,'avgPrice':374.58,'currentPrice':374.58,'pnl':0},
    {'sym':'GOOGL','units':0.6414,'avgPrice':311.76,'currentPrice':311.76,'pnl':0}
]
yoni['holdings'] = new_holdings

# Update trades
new_trades = [
    {'date':'2026-02-28','action':'sell','ticker':'META','units':0.3091,'price':648.18,'amount':200.36,'reason':'SM:36.88|distributing GEX:negative|-0.08, SM less than 40 indicating distribution','pnl':0.36},
    {'date':'2026-02-28','action':'sell','ticker':'SOFI','units':11.2613,'price':17.76,'amount':200,'reason':'SM:0|distributing GEX:positive|0.15, SM less than 40 indicating distribution','pnl':0},
    {'date':'2026-02-28','action':'sell','ticker':'AVGO','units':0.6258,'price':319.55,'amount':200,'reason':'SM:0|distributing GEX:negative|-0.22, SM less than 40 indicating distribution','pnl':0},
    {'date':'2026-02-28','action':'buy','ticker':'MSFT','units':0.5092,'price':392.74,'amount':200,'reason':'SM:100|accumulating GEX:positive|0.28, SM greater than 60 indicating accumulation, positive GEX for support','pnl':0},
    {'date':'2026-02-28','action':'buy','ticker':'TSM','units':0.5341,'price':374.58,'amount':200,'reason':'SM:100|accumulating GEX:positive|0.07, SM greater than 60 indicating accumulation, positive GEX for support','pnl':0},
    {'date':'2026-02-28','action':'buy','ticker':'GOOGL','units':0.6414,'price':311.76,'amount':200,'reason':'SM:100|accumulating GEX:negative|-0.26, SM greater than 60 indicating accumulation','pnl':0}
]
yoni['trades'] += new_trades

# Update audit
new_audit = [
    {'time':'2026-02-28T05:16:00+02:00','agent':'yoni','msg':'SELL 0.3091 META @ 648.18 → P&L: 0.36. SM:36.88|distributing GEX:negative|-0.08'},
    {'time':'2026-02-28T05:16:00+02:00','agent':'yoni','msg':'SELL 11.2613 SOFI @ 17.76 → P&L: 0. SM:0|distributing GEX:positive|0.15'},
    {'time':'2026-02-28T05:16:00+02:00','agent':'yoni','msg':'SELL 0.6258 AVGO @ 319.55 → P&L: 0. SM:0|distributing GEX:negative|-0.22'},
    {'time':'2026-02-28T05:16:00+02:00','agent':'yoni','msg':'BUY 0.5092 MSFT @ 392.74 1x ($200). SM:100|accumulating GEX:positive|0.28'},
    {'time':'2026-02-28T05:16:00+02:00','agent':'yoni','msg':'BUY 0.5341 TSM @ 374.58 1x ($200). SM:100|accumulating GEX:positive|0.07'},
    {'time':'2026-02-28T05:16:00+02:00','agent':'yoni','msg':'BUY 0.6414 GOOGL @ 311.76 1x ($200). SM:100|accumulating GEX:negative|-0.26'}
]
data['audit'] += new_audit

with open('trades.json', 'w') as f:
    json.dump(data, f, indent=2)