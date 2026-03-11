#!/usr/bin/env bash
# Hyper-Sentinel v2 — Test Publisher
# ===================================
# Publishes a test market data request to NATS to validate the MarketAgent pipeline.
# Usage: bash scripts/test-publish.sh [NATS_URL]

set -euo pipefail

NATS_URL="${1:-nats://localhost:4222}"
SUBJECT="sentinel.market.data"

echo "╔══════════════════════════════════════════════════════╗"
echo "║  Hyper-Sentinel v2 — MarketAgent Test Publisher      ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "→ NATS URL:  ${NATS_URL}"
echo "→ Subject:   ${SUBJECT}"
echo ""

# Check if nats CLI is available
if ! command -v nats &> /dev/null; then
    echo "✗ NATS CLI not found. Install it:"
    echo "  brew install nats-io/nats-tools/nats   (macOS)"
    echo "  go install github.com/nats-io/natscli/nats@latest   (Go)"
    exit 1
fi

# Test 1: Basic market scan request
echo "─── Test 1: Market Scan Request ─────────────────────"
nats pub "${SUBJECT}" \
    --server="${NATS_URL}" \
    '{
        "request_id": "test-001",
        "request_type": "market_scan",
        "symbols": ["SPY", "QQQ", "BTC-USD"],
        "timeframe": "1d",
        "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
    }'
echo "✓ Published market scan request"
echo ""

# Test 2: Anomaly detection request
echo "─── Test 2: Anomaly Detection Request ───────────────"
nats pub "${SUBJECT}" \
    --server="${NATS_URL}" \
    '{
        "request_id": "test-002",
        "request_type": "anomaly_detection",
        "symbols": ["SPY", "QQQ"],
        "timeframe": "5d",
        "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
    }'
echo "✓ Published anomaly detection request"
echo ""

# Test 3: Single stock deep dive
echo "─── Test 3: Single Stock Analysis ───────────────────"
nats pub "${SUBJECT}" \
    --server="${NATS_URL}" \
    '{
        "request_id": "test-003",
        "request_type": "deep_analysis",
        "symbols": ["BTC-USD"],
        "timeframe": "30d",
        "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
    }'
echo "✓ Published deep analysis request"
echo ""

echo "══════════════════════════════════════════════════════"
echo "  All test messages published."
echo "  Check MarketAgent logs:  docker compose logs -f market-agent"
echo "  Query SQLite:  sqlite3 data/agent_decisions.db 'SELECT * FROM agent_decisions;'"
echo "══════════════════════════════════════════════════════"
