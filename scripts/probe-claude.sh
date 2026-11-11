#!/usr/bin/env bash
set -euo pipefail

# One minimal Claude Pro subscription request. This does not reset an active window.
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

# Run in an empty directory without project instructions or enabled tools.
# Do not add --bare: it may ignore CLAUDE_CODE_OAUTH_TOKEN.
# Output and stderr are deliberately withheld to avoid leaking account data.
set +e
timeout --signal=TERM --kill-after=10s 120s claude \
  -p 'hi' \
  --model haiku \
  --max-turns 1 \
  --tools '' \
  --output-format text >"$workdir/out" 2>"$workdir/err"
rc=$?
set -e

if [[ "$rc" -ne 0 ]]; then
  echo "::error::Claude Haiku request failed (exit ${rc}); response withheld. Verify subscription authentication and usage status."
  exit 1
fi
if [[ ! -s "$workdir/out" ]]; then
  echo "::error::Claude Haiku request returned empty output."
  exit 1
fi
echo "Claude Haiku request succeeded at $(date -u '+%Y-%m-%dT%H:%M:%SZ'). This does NOT prove the quota window reset."
