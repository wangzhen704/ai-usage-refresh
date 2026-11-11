# Codex subscription: WIF and SIWC integration plan (NOT ACTIVE)

## Why this is separate

**Do not configure `OPENAI_API_KEY` or put `~/.codex/auth.json` in GitHub Secrets.** API Platform WIF is also not the same as *Codex managed ChatGPT workspace* WIF. Ordinary OpenAI API usage does not use the user's Codex subscription allowance.

### Preferred: Codex WIF beta, subject to workspace enablement

OpenAI currently requires explicit enablement of Codex WIF for a managed ChatGPT workspace. Request this through OpenAI Support or your representative. Only the workspace administrator can verify eligibility; the repository cannot test feature entitlement.

After approval:

1. In the ChatGPT Admin Portal, configure a **Custom OIDC** provider for GitHub: issuer `https://token.actions.githubusercontent.com`. Use a dedicated audience.
2. Create a **Codex federation rule**, not an API Platform service-account mapping, targeting a dedicated managed ChatGPT principal. Restrict exact OIDC claims:
   - `repository = wangzhen704/ai-usage-refresh`
   - `ref = refs/heads/main`
   - `workflow_ref = wangzhen704/ai-usage-refresh/.github/workflows/refresh.yml@refs/heads/main`
   - optional protected GitHub Environment claim if used
3. Set a short access lifetime and Codex-local-access scopes as documented. Never use a broad organization wildcard.
4. Review the official Codex CLI WIF documentation for **both** required runtime environment variables and `OPENAI_IDENTITY_TOKEN_FILE`. The file must be an absolute, short-lived GitHub OIDC JWT path with `0600` permission.
5. Only once tested, introduce a separate restricted job with `permissions: {contents: read, id-token: write}`, exact CLI version, and no persisted credentials. Confirm `codex login status` indicates WIF before any request.

Current preflight is deliberately nonfunctional with respect to token exchange or Codex inference. Repository variables `CODEX_WIF_AUDIENCE`, `CODEX_WIF_PROVIDER_ID`, and `CODEX_WIF_RULE_ID` are placeholders only; they are NOT assumed to be the final CLI environment variable names.

### Alternative: Sign in with ChatGPT (SIWC)

This is a **distinct OAuth client integration**, not a generic replacement credential for `codex exec`. ChatGPT plan usage requires approval/scopes, stable host identifier, browser-based initial registration, PKCE, access-token validation and secure storage/refresh. Remotely hosted applications may need explicit eligibility/approval. Do not put SIWC refresh tokens in a public repo or unreviewed workflow.

Until the required plan-usage permission and remote-host eligibility are confirmed, no SIWC execution path is enabled.

### If neither option is approved

Use a trusted self-hosted GitHub Actions runner or run Codex interactively. A self-hosted runner keeps the CLI's login in its own secured OS credential store, but it is still a sensitive long-lived credential and must not execute untrusted PRs. It does not provide WIF-equivalent risk reduction.

### Documentation

- https://developers.openai.com/api/docs/guides/workload-identity-federation
- https://developers.openai.com/api/docs/guides/workload-identity-federation/federation-rules
- https://developers.openai.com/api/docs/guides/workload-identity-federation/github-actions
- https://developers.openai.com/siwc/token-sharing-open-source
