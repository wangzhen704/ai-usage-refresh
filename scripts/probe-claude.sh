#!/usr/bin/env bash
set -euo pipefail

# Minimal Claude Pro subscription probe; no API key fallback and no external tools.
if [[ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" ]]; then
  echo "::error::Missing CLAUDE_CODE_OAUTH_TOKEN in the claude-probe environment."
  exit 2
fi
if [[ -n "${ANTHROPIC_API_KEY:-}" || -n "${ANTHROPIC_AUTH_TOKEN:-}" ]]; then
  echo "::error::API billing credentials must be unset for subscription mode."
  exit 2
fi
if ! command -v claude >/dev/null 2>&1; then
  echo "::error::Claude Code CLI is not installed."
  exit 2
fi

workdir="$(mktemp -d)"
chmod 700 "$workdir"
trap 'rm -rf "$workdir"' EXIT
export HOME="$workdir"
export CLAUDE_CONFIG_DIR="$workdir/.claude"
mkdir -p "$CLAUDE_CONFIG_DIR" "$workdir/job"
chmod 700 "$CLAUDE_CONFIG_DIR"
cd "$workdir/job"
umask 077

# Never print or upload model output; avoid repository instructions, tools and MCPs.
# Do NOT use --bare: it intentionally ignores CLAUDE_CODE_OAUTH_TOKEN.
set +e
timeout --signal=TERM --kill-after=10s 120s claude \
  -p 'Reply with exactly OK. No other text.' \
  --max-turns 1 \
  --tools '' \
  --output-format text >"$workdir/out" 2>"$workdir/err"
rc=$?
set -e

if [[ "$rc" -ne 0 ]]; then
  echo "::error::Claude request failed (exit ${rc}); inspect credentials and account usage status locally. Output withheld to prevent leaks."
  exit 1
fi
if [[ "$(tr -d '\r\n[:space:]' < "$workdir/out")" != "OK" ]]; then
  echo "::error::Claude request returned an unexpected response; output withheld."
  exit 1
fi
echo "Claude request succeeded at $(date -u '+%Y-%m-%dT%H:%M:%SZ'). This does NOT prove any quota window reset."
