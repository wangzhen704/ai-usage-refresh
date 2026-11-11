# Secure subscription probes

This branch intentionally replaces the original generic API-key refresh workflow. The original workflow calls provider APIs with a shared `API_KEY`, which does not refresh Codex or Claude Pro subscription quotas.

## Rollout / safety

- This is a review branch. **GitHub scheduled workflows execute only from the default branch**; the new cron will not run while it remains on this branch. The job guards also require `refs/heads/main`.
- Default state: **off**. After review and merging to `main`, set `ENABLE_CLAUDE_PROBE=true` as a repository Actions Variable to opt in. No request runs before that.
- Create a GitHub Actions Environment named `claude-probe` and restrict deployment branches to `main`. Add Environment Secret `CLAUDE_CODE_OAUTH_TOKEN`.
- On your trusted local computer, log into the **Claude Pro subscription**, then run `claude setup-token`. Store the returned credential only in the GitHub Environment Secret. Do not paste it into chat, code, commits, or logs. It is a long-lived bearer credential: protect and rotate it.
- Set repository Actions Variable `CLAUDE_CLI_VERSION` to an **exact verified version** of `@anthropic-ai/claude-code`. Inspect the selected release and update manually; there is intentionally no `latest`.
- Do not set `ANTHROPIC_API_KEY`. The workflow unsets API credentials to avoid accidental API pay-as-you-go billing.
- Claude probe uses `claude -p 'hi' --model haiku --max-turns 1 --tools '' --output-format text`; this requests the lowest-cost Claude Code model family rather than the CLI default. Check that your chosen pinned CLI version supports `--model haiku`.
- Disable any extra pay-as-you-go / additional-usage setting in your Claude account before activation if you want a hard subscription-only spending boundary.
- To perform the first manual test after merging, temporarily set `ENABLE_CLAUDE_PROBE=true`, trigger `workflow_dispatch`, inspect the sanitized result and confirm in Claude usage/account settings that the subscription (not Console API billing) was used; then set it back to `false` while evaluating. The same variable gates scheduled and manual requests.
- The workflow does not introspect or manage Claude's five-hour window: it only makes one small real request, which may start a new window **if the previous window has ended**.
- The current cron probes at 00:17, 05:17, 10:17, 15:17, and 20:17 UTC; the last gap is four hours. GitHub cron may be delayed. It is **not** an exact rolling five-hour timer, and a successful request **does not establish that a quota reset occurred**.
- Claude Pro has shared usage caps. Small synthetic requests still consume usage. Disable `ENABLE_CLAUDE_PROBE` if it is not demonstrably useful.

## Security model

- Explicit GitHub minimal permissions, no PR triggers, protected `main` gate, and separate credential environment.
- Known `actions/checkout` release pinned to a complete SHA; persistent checkout credentials disabled.
- Claude CLI exact npm version, no package lifecycle scripts, no automatic updates.
- Commands run in a fresh empty temporary working directory with no project instructions or tools. Model output and stderr are never published.
- GitHub runners are third-party infrastructure: Environment Secrets are protected at rest but available to a running job. Restrict who can change the default branch and workflow; prefer private repo and environment approvals where appropriate.
- Restrict or revoke any compromised token immediately. GitHub redaction is not a substitute for never printing secrets.

## Codex

Read [CODEX-WIF.md](CODEX-WIF.md). The Codex job is only a configuration preflight and makes **no** OpenAI calls. Keep `ENABLE_CODEX_WIF_PREFLIGHT` unset until the workspace is approved for Codex WIF.

## References

- https://code.claude.com/docs/en/authentication
- https://developers.openai.com/api/docs/guides/workload-identity-federation
- https://developers.openai.com/api/docs/guides/workload-identity-federation/github-actions
- https://developers.openai.com/siwc/token-sharing-open-source
