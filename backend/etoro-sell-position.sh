#!/bin/bash
#
# eToro Sell Position Script
# Closes a position via eToro Public API
#

# eToro API credentials
API_KEY="sdgdskldFPLGfjHn1421dgnlxdGTbngdflg6290bRjslfihsjhSDsdgGHH25hjf"
USER_KEY="eyJjaSI6IjYwY2FiYjBiLTU1OTctNDQ4NS04ZjYzLTdlOWUwNTZlMGJiOCIsImVhbiI6IlVucmVnaXN0ZXJlZEFwcGxpY2F0aW9uIiwiZWsiOiJCRm01a3NkSUFSY29yS0FhTENwcURRLUItb09QdmNNUHFmTDNyem9NemdpTGx6NEItRjh5LWozNmY2dGhZVVpqWXoxeVhrbi52M3NYWFdCUUkwcGdmUExBbi1UNFhnZS03SWVWa0UzaEJiTV8ifQ__"
BASE_URL="https://public-api.etoro.com"

# Parse parameters from query string
POSITION_ID=$(echo "$QUERY_STRING" | grep -oP 'positionId=\K[^&]+')
SYMBOL=$(echo "$QUERY_STRING" | grep -oP 'symbol=\K[^&]+')

if [ -z "$POSITION_ID" ]; then
    echo "Content-Type: text/plain"
    echo ""
    echo "Error: Position ID required"
    exit 1
fi

# Generate unique request ID
REQUEST_ID=$(uuidgen)

# API endpoint
ENDPOINT="${BASE_URL}/api/v1/trading/execution/market-close-orders/positions/${POSITION_ID}"

# Log the sell attempt
echo "$(date '+%Y-%m-%d %H:%M:%S') - SELL ${SYMBOL} (Position: ${POSITION_ID})" >> /home/ofer/.openclaw/workspace-ofsinvest/memory/sell-log.txt

# Execute SELL via eToro API
HTTP_CODE=$(curl -s -w "%{http_code}" -o /tmp/sell_response.json \
    -X POST "${ENDPOINT}" \
    -H "x-api-key: ${API_KEY}" \
    -H "x-user-key: ${USER_KEY}" \
    -H "X-Request-Id: ${REQUEST_ID}" \
    -H "Content-Type: application/json")

# Check response
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
    # Success
    echo "Content-Type: application/json"
    echo ""
    cat /tmp/sell_response.json
    
    # Log success
    echo "$(date '+%Y-%m-%d %H:%M:%S') - SUCCESS: ${SYMBOL} sold (HTTP ${HTTP_CODE})" >> /home/ofer/.openclaw/workspace-ofsinvest/memory/sell-log.txt
    
    exit 0
else
    # Failed
    echo "Content-Type: text/plain"
    echo "Status: ${HTTP_CODE}"
    echo ""
    echo "Failed to sell position (HTTP ${HTTP_CODE})"
    cat /tmp/sell_response.json
    
    # Log failure
    echo "$(date '+%Y-%m-%d %H:%M:%S') - FAILED: ${SYMBOL} (HTTP ${HTTP_CODE}) - $(cat /tmp/sell_response.json)" >> /home/ofer/.openclaw/workspace-ofsinvest/memory/sell-log.txt
    
    exit 1
fi
