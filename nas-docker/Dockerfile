FROM node:22-bookworm-slim
ARG CODEX_VERSION
ARG CLAUDE_VERSION
RUN apt-get update && apt-get install -y --no-install-recommends python3 ca-certificates && rm -rf /var/lib/apt/lists/* \
 && test -n "$CODEX_VERSION" && test -n "$CLAUDE_VERSION" \
 && npm install -g --no-audit --no-fund "@openai/codex@${CODEX_VERSION}" "@anthropic-ai/claude-code@${CLAUDE_VERSION}" \
 && useradd -m -u 10001 -s /bin/sh app && mkdir -p /data /opt/app && chown app:app /data
COPY app.py /opt/app/app.py
COPY scripts/ /opt/app/scripts/
USER app
ENV APP_DATA=/data BIND_HOST=127.0.0.1 PORT=8787
EXPOSE 8787
CMD ["python3", "/opt/app/app.py"]
