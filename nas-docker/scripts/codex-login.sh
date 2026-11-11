#!/bin/sh
set -eu
export HOME=/data/home-codex
mkdir -p "$HOME"
chmod 700 "$HOME"
proxy="$(python3 -c 'import json; from pathlib import Path; p=Path("/data/config.json"); print(json.loads(p.read_text()).get("proxy_url", "") if p.exists() else "")')"
if [ -n "$proxy" ]; then
  export HTTP_PROXY="$proxy" HTTPS_PROXY="$proxy" http_proxy="$proxy" https_proxy="$proxy"
  case "$proxy" in socks5*) export ALL_PROXY="$proxy" all_proxy="$proxy";; esac
fi
exec codex login --device-auth
