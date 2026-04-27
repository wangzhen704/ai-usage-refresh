# AI Usage Refresh

**Keep your AI Coding Plan usage quota on a fixed cycle. Never waste quota again.**

[![GitHub Actions](https://img.shields.io/badge/GitHub-Actions-blue?logo=github)](https://github.com/features/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

🌍 **Languages:** [English](README.md) | [简体中文](docs/README.zh-CN.md) | [繁體中文](docs/README.zh-TW.md) | [日本語](docs/README.ja.md) | [Русский](docs/README.ru.md)

---

## The Problem

Most AI Coding Plan services (ChatGPT Plan, ZAI Coding, Alibaba Cloud Coding Plan, Claude, etc.) reset your usage quota on a **rolling window** — the 5-hour timer starts when you **first use** the API, not on a fixed schedule.

This leads to **quota waste**:

```
Rolling Window (WASTEFUL):
Timeline: ──use──5h──reset──────────use──5h──reset──────
          0h    5h                7h   12h
          ❌ Timer starts from first use, shifting unpredictably
          ❌ E.g. if 2h remain in a cycle, you get 2h+5h=7h
             but only use 2 cycles' worth of quota in that span

Fixed Cycle (OPTIMAL):
Timeline: ──refresh──5h──refresh──5h──refresh──5h──refresh──
          0h              5h             10h            15h
          ✅ Timer resets on a predictable schedule
          ✅ Maximum quota utilization every cycle
```

**Example:** Your plan resets every 5 hours. You start coding at hour 2 of a cycle. Using the service triggers a *new* 5-hour timer. Now your reset is at hour 7 instead of hour 5 — and the previous 2 hours of quota were wasted.

## The Solution

This repo uses **GitHub Actions** to send a minimal API request (`"hi"`, `max_tokens: 1`) at a fixed interval, locking your usage timer to a **predictable schedule**.

- **Zero cost** — runs on free GitHub Actions minutes
- **Zero dependencies** — pure `curl`, no runtime needed
- **Minimal token usage** — 1 token per refresh, essentially free
- **Fully configurable** — interval, provider, model, endpoint all adjustable via GitHub Variables

## How It Works

1. GitHub Actions triggers on your configured schedule (default: every 5 hours)
2. Sends a minimal `"hi"` request to your Coding Plan endpoint
3. This triggers the provider's usage timer reset
4. Your quota cycle stays locked to a fixed schedule
5. When you actually code, the timer is already in sync → maximum quota

## Quick Start

### 1. Fork this repository

Click **Fork** at the top right.

### 2. Configure Secrets & Variables

Go to your fork → **Settings** → **Secrets and variables** → **Actions**

**Required — Add a Secret:**

| Name | Value |
|---|---|
| `API_KEY` | Your Coding Plan API key |

**Optional — Add Variables:**

| Name | Description | Default |
|---|---|---|
| `API_PROVIDER` | `openai`, `anthropic`, or `custom` | `openai` |
| `API_BASE_URL` | Your Coding Plan endpoint URL | Provider default |
| `MODEL` | Model name | Provider default |

### 3. Enable Actions

Go to **Actions** tab → Click **"I understand my workflows, go ahead and enable them"**

### 4. Done!

Runs automatically. You can also trigger manually via **Actions** → **Run workflow**.

---

## Provider Examples

### ZAI (智谱) Coding Plan

Get your API Key from: [open.bigmodel.cn](https://open.bigmodel.cn) → Coding Plan

| Type | Name | Value |
|---|---|---|
| Secret | `API_KEY` | Your Coding Plan key |
| Variable | `API_PROVIDER` | `openai` |
| Variable | `API_BASE_URL` | `https://open.bigmodel.cn/api/coding/paas/v4` |

### Alibaba Cloud (阿里云) Coding Plan — OpenAI Compatible

Get your **exclusive** API Key (format: `sk-sp-xxxxx`) from the Coding Plan page.

> ⚠️ The Coding Plan API Key (`sk-sp-xxxxx`) and Base URL are **NOT interchangeable** with regular Bailian pay-per-use keys. Do not mix them.

| Type | Name | Value |
|---|---|---|
| Secret | `API_KEY` | `sk-sp-xxxxx` (Coding Plan exclusive) |
| Variable | `API_PROVIDER` | `openai` |
| Variable | `API_BASE_URL` | `https://coding.dashscope.aliyuncs.com/v1` |

### Alibaba Cloud (阿里云) Coding Plan — Anthropic Compatible

| Type | Name | Value |
|---|---|---|
| Secret | `API_KEY` | `sk-sp-xxxxx` (Coding Plan exclusive) |
| Variable | `API_PROVIDER` | `anthropic` |
| Variable | `API_BASE_URL` | `https://coding.dashscope.aliyuncs.com/apps/anthropic` |

### ChatGPT Plan

| Type | Name | Value |
|---|---|---|
| Secret | `API_KEY` | Your OpenAI API key |
| Variable | `API_PROVIDER` | `openai` |
| Variable | `API_BASE_URL` | `https://api.openai.com/v1` |

### Claude / Anthropic

| Type | Name | Value |
|---|---|---|
| Secret | `API_KEY` | Your Anthropic API key |
| Variable | `API_PROVIDER` | `anthropic` |
| Variable | `API_BASE_URL` | `https://api.anthropic.com/v1` |

### Other Providers

Any provider that offers a Coding Plan with an API endpoint and a rolling usage window can be used. Check your provider's dashboard for the exclusive API Key and Base URL, then:

| Type | Name | Value |
|---|---|---|
| Secret | `API_KEY` | Your provider's API key |
| Variable | `API_PROVIDER` | `openai` or `anthropic` (depending on compatibility) |
| Variable | `API_BASE_URL` | Your provider's endpoint |
| Variable | `MODEL` | Supported model name |

---

## Configuration

### Changing the Refresh Interval

Edit `.github/workflows/refresh.yml` and modify the `cron` expression:

```yaml
on:
  schedule:
    - cron: '0 */5 * * *'  # Change this
```

**Common intervals:**

| Interval | Cron Expression |
|---|---|
| Every 1 hour | `0 */1 * * *` |
| Every 2 hours | `0 */2 * * *` |
| Every 3 hours | `0 */3 * * *` |
| Every 4 hours | `0 */4 * * *` |
| Every 5 hours | `0 */5 * * *` |
| Every 6 hours | `0 */6 * * *` |
| Every 8 hours | `0 */8 * * *` |
| Every 12 hours | `0 */12 * * *` |

Generate custom schedules at [crontab.guru](https://crontab.guru).

## FAQ

**Q: Does this cost money?**
A: Each request uses 1 token (minimum possible). At any provider's pricing, this is essentially $0 per refresh.

**Q: Will GitHub charge for Actions?**
A: Public repos get unlimited free Actions minutes. Private repos use ~1 min/month, well within the free tier.

**Q: What if the request fails?**
A: The workflow shows as failed. Re-trigger manually via the Actions tab.

**Q: Why not just use the service normally?**
A: You should! This runs *in addition* to normal usage, keeping the quota timer on a fixed schedule so you get the most out of every cycle.

## License

[MIT](LICENSE) © 2026 wsu2059
