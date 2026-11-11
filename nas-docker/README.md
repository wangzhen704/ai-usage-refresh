# NAS Docker: Claude Pro + ChatGPT Codex dashboard\n\n**飞牛 NAS 用户请先阅读：[飞牛 NAS（fnOS）Docker 部署与使用指南](飞牛NAS-Docker详细使用指南.md)**\n

Independent NAS deployment of AI subscription usage-window probes. Web UI configures two provider toggles, interval, model and proxy. The actual CLI login happens **inside the NAS container**, never in GitHub Secrets or the browser.

## Security first

- The dashboard does **not** collect OAuth tokens in web forms. ChatGPT device login persists in `./data/home-codex`; Claude Pro bearer credential is read from `./data/claude-oauth-token`. Both files live only on the NAS. Keep `./data` off Git, backups shared with others and public file shares.
- A NAS is not automatically safe: restrict Docker host admin access, change the dashboard password if compromised, avoid exposing port 8787 to the Internet, keep NAS and images updated, review pinned CLI npm package releases.
- The Compose file publishes **localhost only**, runs non-root, drops Linux capabilities, uses read-only root filesystem, limits memory and pids, and makes all automated calls opt-in.
- The web dashboard has session cookies, CSRF, origin checks, modest input validation, and no shell-command field. Output and stderr from CLI calls are never stored or shown. Successful CLI execution **does not prove quota reset**.
- A local admin login password is auto-generated at first boot. Fetch it only with `docker compose exec dashboard cat /data/admin-password.txt`. The password file must remain private.
- Before using Claude, disable any account setting that permits unexpected extra paid usage, if available. Do not use `ANTHROPIC_API_KEY`.

## Deploy

1. Copy `.env.example` to `.env`, set exact **published, reviewed** `CODEX_VERSION` and `CLAUDE_VERSION` (do not use `latest`; builds intentionally fail until versions are supplied).
2. Create a data directory and grant UID 10001 access, with no access for other local users:
   ```sh
   mkdir -p data
   sudo chown 10001:10001 data
   sudo chmod 700 data
   ```
3. Create Docker bridge network once:
   ```sh
   docker network create ai_proxy_net
   ```
4. Run:
   ```sh
   docker compose up -d --build
   docker compose exec dashboard cat /data/admin-password.txt
   ```
5. Open via SSH tunnel rather than NAS port forwarding:
   ```sh
   ssh -L 8787:127.0.0.1:8787 youruser@nas
   ```
   Visit `http://127.0.0.1:8787` on your own computer. On a reverse proxy with HTTPS, also set the container environment variable `COOKIE_SECURE=1` and use VPN or a trusted authentication gateway. The Docker bridge network is separate from the host loopback binding.

## Codex subscription login

In the NAS project directory:

```sh
docker compose exec dashboard sh /opt/app/scripts/codex-login.sh
docker compose exec dashboard sh /opt/app/scripts/codex-status.sh
```

The first command asks Codex for a device authorization. Complete it using a trusted browser signed into your ChatGPT account. The helper picks up the proxy address configured in the dashboard and uses a persistent `HOME=/data/home-codex`. If your CLI/plan does not support device login, use official Codex login instructions; **never** paste browser cookies, export `auth.json` to GitHub, or use unofficial token refresh services. Leave Codex model blank to use the CLI default; do not assume a colloquial model nickname is a valid API model ID.

## Claude Pro subscription login

On a trusted computer where Claude Code is signed into your Claude Pro subscription:

```sh
claude setup-token
```

In a **trusted NAS terminal**, create `data/claude-oauth-token` and paste the resulting token using stdin, not a command-line argument or web form. Ensure owner UID 10001 and permissions `0600`. For example:

```sh
umask 077
cat > data/claude-oauth-token
# paste token, enter, Ctrl-D
sudo chown 10001:10001 data/claude-oauth-token
sudo chmod 600 data/claude-oauth-token
```

This token is a long-lived bearer secret: revoke it if compromised. Claude is fixed to Haiku with `hi`, one turn and no tools.

## Separate Clash/Mihomo Docker container

Use your own **audited** Clash/Mihomo image under a separate Compose project, and attach it to the shared external `ai_proxy_net`. The proxy service should be named `clash`, bind its mixed/HTTP proxy to container interface port 7890, and not publish it to the public network.

Example network stanza for your Clash Compose:

```yaml
services:
  clash:
    image: REPLACE_WITH_TRUSTED_PINNED_IMAGE
    networks: [ai_proxy_net]
networks:
  ai_proxy_net:
    external: true
```

Set the dashboard proxy to `http://clash:7890`. `localhost` inside dashboard points to the dashboard container, **not** the separate Clash container. Never use arbitrary unaudited proxy endpoints with account credentials. The Codex device-login helper and probe requests honor the configured proxy; Claude's token generation on your trusted computer uses that computer's connection.

## Operation and limits

All scheduled tasks start **disabled**. Manual run buttons each send **one real subscription request**. Enable recurring work only after manual validation, and verify usage in the official account dashboard. Defaults are a 300-minute interval; this scheduler is approximate, runs while the container is online and may execute soon after a restart with enabled toggles. **It neither increases plan allowances nor forcibly resets an active five-hour window.**

The source is intentionally small. The CLI packages are retrieved by npm at image build time; inspect their exact versions and lock down your Docker host. Builds and live authentication have **not** been verified on your NAS or with your account. Use a test deploy before exposing the dashboard to any wider network.
