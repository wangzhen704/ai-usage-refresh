#!/usr/bin/env bash
set -euo pipefail

API_PROVIDER="${API_PROVIDER:-openai}"
API_KEY="${API_KEY:-}"
API_BASE_URL="${API_BASE_URL:-}"
MODEL="${MODEL:-}"

if [ -z "$API_KEY" ]; then
  echo "ERROR: API_KEY is not set. Please configure it in GitHub Secrets."
  exit 1
fi

build_openai_request() {
  local base="${API_BASE_URL:-https://api.openai.com/v1}"
  local model="${MODEL:-gpt-4o-mini}"
  cat <<EOF
{
  "url": "${base}/chat/completions",
  "model": "${model}",
  "body": {
    "model": "${model}",
    "messages": [{"role": "user", "content": "hi"}],
    "max_tokens": 1,
    "temperature": 0
  }
}
EOF
}

build_anthropic_request() {
  local base="${API_BASE_URL:-https://api.anthropic.com/v1}"
  local model="${MODEL:-claude-sonnet-4-20250514}"
  cat <<EOF
{
  "url": "${base}/messages",
  "model": "${model}",
  "body": {
    "model": "${model}",
    "messages": [{"role": "user", "content": "hi"}],
    "max_tokens": 1,
    "temperature": 0
  }
}
EOF
}

build_custom_request() {
  if [ -z "$API_BASE_URL" ]; then
    echo "ERROR: API_BASE_URL is required for custom provider." >&2
    exit 1
  fi
  local model="${MODEL:-default}"
  cat <<EOF
{
  "url": "${API_BASE_URL}",
  "model": "${model}",
  "body": {
    "model": "${model}",
    "messages": [{"role": "user", "content": "hi"}],
    "max_tokens": 1,
    "temperature": 0
  }
}
EOF
}

echo "=========================================="
echo " AI Usage Refresh"
echo " Provider : ${API_PROVIDER}"
echo " Time     : $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "=========================================="

request=""

case "$API_PROVIDER" in
  openai|openai-compatible)
    request="$(build_openai_request)"
    ;;
  anthropic|claude)
    request="$(build_anthropic_request)"
    ;;
  custom)
    request="$(build_custom_request)"
    ;;
  *)
    echo "ERROR: Unknown provider '${API_PROVIDER}'. Supported: openai, anthropic, custom"
    exit 1
    ;;
esac

url="$(echo "$request" | grep -o '"url": *"[^"]*"' | head -1 | sed 's/"url": *"//;s/"//')"
body="$(echo "$request" | python3 -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d['body']))" 2>/dev/null || echo "$request" | python -c "import sys,json; d=json.load(sys.stdin); print(json.dumps(d['body']))" 2>/dev/null || echo "{}")"

echo ""
echo "Sending refresh request to: ${url}"
echo "Model: $(echo "$request" | grep -o '"model": *"[^"]*"' | head -1 | sed 's/"model": *"//;s/"//')"
echo ""

case "$API_PROVIDER" in
  openai|openai-compatible|custom)
    response=$(curl -s -w "\n%{http_code}" \
      -X POST "$url" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer ${API_KEY}" \
      -d "$body" \
      --connect-timeout 30 \
      --max-time 60 2>&1 || true)
    ;;
  anthropic|claude)
    response=$(curl -s -w "\n%{http_code}" \
      -X POST "$url" \
      -H "Content-Type: application/json" \
      -H "x-api-key: ${API_KEY}" \
      -H "anthropic-version: 2023-06-01" \
      -d "$body" \
      --connect-timeout 30 \
      --max-time 60 2>&1 || true)
    ;;
esac

http_code="$(echo "$response" | tail -1)"
response_body="$(echo "$response" | sed '$d')"

echo "HTTP Status: ${http_code}"
echo ""

if echo "$http_code" | grep -qE '^2[0-9]{2}$'; then
  echo "Refresh successful! Usage timer has been reset."
else
  echo "Response: ${response_body}"
  echo ""
  echo "Refresh may have failed. Check your API key and provider settings."
  exit 1
fi

echo ""
echo "=========================================="
echo " Next reset will be at the configured interval."
echo "=========================================="
