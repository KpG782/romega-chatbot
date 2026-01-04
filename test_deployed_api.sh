#!/bin/bash

# Test script for deployed Romega Chatbot API
BASE_URL="https://automation-romega-chatbot.kygozf.easypanel.host"

echo "=========================================="
echo "Testing Romega Chatbot API"
echo "=========================================="
echo ""

echo "1. Testing Health Endpoint..."
echo "GET $BASE_URL/health"
curl -s "$BASE_URL/health" | jq .
echo ""
echo ""

echo "2. Testing Root Endpoint..."
echo "GET $BASE_URL/"
curl -s "$BASE_URL/" | jq .
echo ""
echo ""

echo "3. Testing Chat Endpoint..."
echo "POST $BASE_URL/chat"
curl -s -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What services does Romega Solutions offer?"}' | jq .
echo ""
echo ""

echo "4. Testing Chat Endpoint (cached response)..."
echo "POST $BASE_URL/chat (should return cached=true)"
curl -s -X POST "$BASE_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What services does Romega Solutions offer?"}' | jq .
echo ""
echo ""

echo "5. Testing Rate Limiting..."
echo "Making 25 requests rapidly to test rate limit (20/minute)..."
for i in {1..25}; do
  echo -n "Request $i: "
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/chat" \
    -H "Content-Type: application/json" \
    -d "{\"message\": \"Test request $i\"}")
  echo "HTTP $STATUS"
  if [ "$STATUS" == "429" ]; then
    echo "✅ Rate limit working! (HTTP 429)"
    break
  fi
done

echo ""
echo "=========================================="
echo "Testing Complete!"
echo "=========================================="
