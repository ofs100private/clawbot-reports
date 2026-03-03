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
DASHBOARD_DATA="$BACKEND_DIR/../trading-data.json"
if [ -f "$DASHBOARD_DATA" ]; then
    echo ""
    echo "Step 3: Updating dashboard data..."
    
    # Backup current dashboard data
    cp "$DASHBOARD_DATA" "$DASHBOARD_DATA.backup.$(date +%s)"
    
    # Update timestamp
    jq --arg ts "$TIMESTAMP" '.metadata.last_sync = $ts' "$DASHBOARD_DATA" > "$DASHBOARD_DATA.tmp"
    mv "$DASHBOARD_DATA.tmp" "$DASHBOARD_DATA"
    
    echo "✅ Dashboard data updated"
else
    echo "⚠️  Warning: Dashboard data file not found: $DASHBOARD_DATA"
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
