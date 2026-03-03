#!/bin/bash

# eToro Trade Execution Script
# Usage: ./etoro-execute-trade.sh <instrumentId> <amount> <leverage> [stopLoss] [takeProfit]

set -e

INSTRUMENT_ID=$1
AMOUNT=$2
LEVERAGE=${3:-1}
STOP_LOSS=${4:-0}
TAKE_PROFIT=${5:-0}

if [ -z "$INSTRUMENT_ID" ] || [ -z "$AMOUNT" ]; then
    echo "Error: Missing required parameters"
    echo "Usage: $0 <instrumentId> <amount> <leverage> [stopLoss] [takeProfit]"
    exit 1
fi

# Read credentials
SECRETS_FILE="/home/ofer/.openclaw/workspace-ofsinvest/memory/etoro-credentials.md"

if [ ! -f "$SECRETS_FILE" ]; then
    echo "Error: Credentials file not found: $SECRETS_FILE"
    exit 1
fi

# Extract API keys (remove all whitespace and newlines)
API_KEY=$(grep "x-api-key" "$SECRETS_FILE" | awk -F': ' '{print $2}' | tr -d ' \r\n')
USER_KEY=$(grep "x-user-key" "$SECRETS_FILE" | awk -F': ' '{print $2}' | tr -d ' \r\n')

if [ -z "$API_KEY" ] || [ -z "$USER_KEY" ]; then
    echo "Error: Could not extract API keys from credentials file"
    exit 1
fi

# eToro API base URL
BASE_URL="https://public-api.etoro.com"

# Build JSON payload
JSON_PAYLOAD=$(cat <<EOF
{
  "instrumentId": $INSTRUMENT_ID,
  "amount": $AMOUNT,
  "leverage": $LEVERAGE,
  "isBuy": true
EOF
)

# Add optional stop loss
if [ "$STOP_LOSS" != "0" ]; then
    JSON_PAYLOAD="$JSON_PAYLOAD,
  \"stopLoss\": $STOP_LOSS"
fi

# Add optional take profit
if [ "$TAKE_PROFIT" != "0" ]; then
    JSON_PAYLOAD="$JSON_PAYLOAD,
  \"takeProfit\": $TAKE_PROFIT"
fi

# Close JSON
JSON_PAYLOAD="$JSON_PAYLOAD
}"

echo "========================================="
echo "eToro Trade Execution"
echo "========================================="
echo "Instrument ID: $INSTRUMENT_ID"
echo "Amount: \$$AMOUNT"
echo "Leverage: ${LEVERAGE}x"
echo "Stop Loss: $STOP_LOSS"
echo "Take Profit: $TAKE_PROFIT"
echo "========================================="
echo ""
echo "Sending order to eToro API..."
echo ""

# Generate unique request ID
REQUEST_ID=$(uuidgen 2>/dev/null || cat /proc/sys/kernel/random/uuid 2>/dev/null || echo "req-$(date +%s)-$$")

# Execute trade
RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/trading/execution/market-open-orders/by-amount" \
  -H "Content-Type: application/json" \
  -H "x-api-key: ${API_KEY}" \
  -H "x-user-key: ${USER_KEY}" \
  -H "X-Request-Id: ${REQUEST_ID}" \
  -d "$JSON_PAYLOAD" \
  -w "\nHTTP_STATUS:%{http_code}")

# Extract HTTP status code
HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS:/d')

echo "========================================="
echo "API Response"
echo "========================================="
echo "HTTP Status: $HTTP_STATUS"
echo "Response Body:"
echo "$BODY" | jq . 2>/dev/null || echo "$BODY"
echo "========================================="

# Check for success
if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "201" ]; then
    echo ""
    echo "✅ Trade executed successfully!"
    
    # Extract order ID if available
    ORDER_ID=$(echo "$BODY" | jq -r '.orderId // .id // empty' 2>/dev/null)
    if [ -n "$ORDER_ID" ]; then
        echo "Order ID: $ORDER_ID"
    fi
    
    exit 0
else
    echo ""
    echo "❌ Trade execution failed!"
    echo "HTTP Status: $HTTP_STATUS"
    exit 1
fi
