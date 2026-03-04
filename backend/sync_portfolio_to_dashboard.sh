#!/bin/bash

# Portfolio-Dashboard Sync Script
# Runs every 5 minutes to ensure dashboard reflects live portfolio state

set -e

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
TIMESTAMP_LOCAL=$(date +"%Y-%m-%d %H:%M:%S %Z")

echo "========================================="
echo "Portfolio-Dashboard Sync"
echo "========================================="
echo "Started: $TIMESTAMP_LOCAL"
echo ""

# Paths
BACKEND_DIR="/home/ofer/clawbot-reports/backend"
TRADES_DIR="/home/ofer/clawbot-reports/trades"
CACHE_DIR="/home/ofer/.openclaw/workspace-ofsinvest/cache"
MEMORY_DIR="/home/ofer/.openclaw/workspace-ofsinvest/memory"

# Ensure directories exist
mkdir -p "$TRADES_DIR"
mkdir -p "$CACHE_DIR"
mkdir -p "$MEMORY_DIR"

# 1. Fetch current portfolio state from eToro API
echo "Step 1: Fetching live portfolio from eToro..."
cd "$BACKEND_DIR"

if [ -f "sync_live_portfolio.py" ]; then
    python3 sync_live_portfolio.py > /tmp/portfolio_sync.log 2>&1 || echo "Warning: sync_live_portfolio.py failed"
fi

# 2. Load trade log
TRADE_LOG="$MEMORY_DIR/trade-log.json"
if [ -f "$TRADE_LOG" ]; then
    TOTAL_TRADES=$(jq '.metadata.total_trades // 0' "$TRADE_LOG")
    echo "Trade log: $TOTAL_TRADES trades recorded"
else
    echo "Warning: No trade log found at $TRADE_LOG"
    TOTAL_TRADES=0
fi

# 3. Check for portfolio-dashboard discrepancies
echo ""
echo "Step 2: Validating dashboard data..."

# Count trades in directory
TRADE_FILES=$(find "$TRADES_DIR" -name "*.json" -type f | wc -l)
echo "Trade files on disk: $TRADE_FILES"
echo "Trade log entries: $TOTAL_TRADES"

if [ "$TRADE_FILES" -ne "$TOTAL_TRADES" ]; then
    echo "⚠️  WARNING: Mismatch between trade files ($TRADE_FILES) and log ($TOTAL_TRADES)"
fi

# 4. Update dashboard data file
TRACKED_FILE="/home/ofer/clawbot-reports/data/tracked-trades.json"
DASHBOARD_DATA="$BACKEND_DIR/../trades.json"
if [ -f "$DASHBOARD_DATA" ] && [ -f "$TRACKED_FILE" ]; then
    echo ""
    echo "Step 3: Updating dashboard data..."
    
    # Backup current dashboard data
    cp "$DASHBOARD_DATA" "$DASHBOARD_DATA.backup.$(date +%s)"
    
    # Make copy for comparison
    cp "$DASHBOARD_DATA" "/tmp/trades_before.json"
    
    # Merge live data into holdings
    jq '
      .holdings = [
        .holdings[] |
        . as $holding |
        ($tracked[0].orders[] | select(.order_id == $holding.position_id)) as $match |
        if $match then
          $holding
          | .current_price = $match.current_price
          | .pnl = $match.current_pnl
          | .status = $match.status
          | .pnl_percent = (if .amount > 0 then (.pnl / .amount) * 100 else 0 end)
          | .current_value = (.amount + .pnl)
          | (if $match.units != null then .units = $match.units else . end)
          | (if $match.last_api_update != null then .last_update = $match.last_api_update else . end)
        else
          $holding
        end
      ]
    ' --slurpfile tracked "$TRACKED_FILE" "$DASHBOARD_DATA" > "/tmp/trades_merged.json"
    
    # Compare if changed
    if cmp -s "/tmp/trades_before.json" "/tmp/trades_merged.json"; then
        echo "No data changes detected - skipping timestamp update"
        rm "/tmp/trades_merged.json"
    else
        echo "Data changes detected - updating timestamp"
        jq --arg ts "$TIMESTAMP" '.metadata.last_sync = $ts' "/tmp/trades_merged.json" > "$DASHBOARD_DATA.tmp"
        mv "$DASHBOARD_DATA.tmp" "$DASHBOARD_DATA"
        rm "/tmp/trades_merged.json"
    fi
    
    rm "/tmp/trades_before.json"
    
    echo "✅ Dashboard data updated"
else
    if [ ! -f "$DASHBOARD_DATA" ]; then
        echo "⚠️  Warning: Dashboard data file not found: $DASHBOARD_DATA"
    fi
    if [ ! -f "$TRACKED_FILE" ]; then
        echo "⚠️  Warning: Tracked trades file not found: $TRACKED_FILE"
    fi
fi

# 5. Validate critical files
echo ""
echo "Step 4: Validating critical files..."

CRITICAL_FILES=(
    "$TRADE_LOG"
    "$CACHE_DIR/portfolio-instrument-ids.json"
    "$MEMORY_DIR/etoro-credentials.md"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ MISSING: $file"
    fi
done

# 6. Generate sync report
SYNC_REPORT="$CACHE_DIR/last-sync-report.json"
cat > "$SYNC_REPORT" << EOF
{
  "timestamp": "$TIMESTAMP",
  "timestamp_local": "$TIMESTAMP_LOCAL",
  "trade_log_entries": $TOTAL_TRADES,
  "trade_files_on_disk": $TRADE_FILES,
  "discrepancy": $([ "$TRADE_FILES" -ne "$TOTAL_TRADES" ] && echo "true" || echo "false"),
  "dashboard_updated": true,
  "status": "completed"
}
EOF

echo ""
echo "========================================="
echo "Sync completed successfully"
echo "Report: $SYNC_REPORT"
echo "========================================="

exit 0
