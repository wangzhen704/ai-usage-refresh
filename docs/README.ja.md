# AI Usage Refresh（AI コーディングプラン使用量自動リフレッシュ）

**AI Coding Plan の使用量クォータを固定サイクルに保ち、クォータを無駄にしません。**

[![GitHub Actions](https://img.shields.io/badge/GitHub-Actions-blue?logo=github)](https://github.com/features/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)

🌍 **言語:** [English](../README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Русский](README.ru.md)

---

## 問題点

ほとんどの AI コーディングプランサービス（ChatGPT Plan、ZAI Coding、Alibaba Cloud Coding Plan、Claude など）は、**ローリングウィンドウ**方式で使用量クォータをリセットします。5時間のタイマーは固定スケジュールではなく、**初回使用時**から開始されます。

これにより**クォータの無駄**が生じます：

```
ローリングウィンドウ（無駄あり）:
タイムライン: ──使用──5h──リセット──────使用──5h──リセット──
              0h    5h                7h   12h
              ❌ タイマーが初回使用から開始、予測不能にずれる
              ❌ 例：サイクル残り2時間で使用すると、2h+5h=7hになるが
                 その期間で得られるのはわずか2サイクル分のクォータのみ

固定サイクル（最適）:
タイムライン: ──リフレッシュ──5h──リフレッシュ──5h──リフレッシュ──
              0h                      5h                       10h
              ✅ 予測可能なスケジュールでタイマーがリセット
              ✅ 各サイクルでクォータを最大化
```

## 解決策

このリポジトリは **GitHub Actions** を使用して、固定間隔で最小限の API リクエスト（`"hi"`, `max_tokens: 1`）を送信し、使用量タイマーを**予測可能なスケジュール**に固定します。

- **ゼロコスト** — GitHub Actions の無料枠で実行
- **ゼロ依存** — 純粋な `curl`、ランタイム不要
- **最小トークン使用量** — 1回のリフレッシュで1トークンのみ
- **完全設定可能** — 間隔、プロバイダー、モデル、エンドポイントを GitHub Variables で調整

## クイックスタート

### 1. このリポジトリをフォーク

ページ右上の **Fork** ボタンをクリック。

### 2. Secrets & Variables の設定

フォークしたリポジトリ → **Settings** → **Secrets and variables** → **Actions**

**必須 — Secret の追加:**

| 名前 | 値 |
|---|---|
| `API_KEY` | Coding Plan の API キー |

**オプション — Variable の追加:**

| 名前 | 説明 | デフォルト |
|---|---|---|
| `API_PROVIDER` | `openai`, `anthropic`, `custom` | `openai` |
| `API_BASE_URL` | Coding Plan エンドポイント URL | プロバイダーデフォルト |
| `MODEL` | モデル名 | プロバイダーデフォルト |

### 3. Actions を有効化

**Actions** タブ → **"I understand my workflows, go ahead and enable them"** をクリック

### 4. 完了！

自動実行されます。**Actions** → **Run workflow** で手動実行も可能です。

---

## プロバイダー設定例

### 智譜（ZAI）Coding Plan

[open.bigmodel.cn](https://open.bigmodel.cn) → Coding Plan ページで API Key を取得。

| タイプ | 名前 | 値 |
|---|---|---|
| Secret | `API_KEY` | Coding Plan キー |
| Variable | `API_PROVIDER` | `openai` |
| Variable | `API_BASE_URL` | `https://open.bigmodel.cn/api/coding/paas/v4` |

### Alibaba Cloud Coding Plan — OpenAI 互換

Coding Plan ページで**専用** API Key（形式：`sk-sp-xxxxx`）を取得。

> ⚠️ Coding Plan 専用 API Key（`sk-sp-xxxxx`）と Base URL は、通常の従量課金 API Key（`sk-xxxxx`）と**互換性がありません**。混用しないでください。

| タイプ | 名前 | 値 |
|---|---|---|
| Secret | `API_KEY` | `sk-sp-xxxxx`（Coding Plan 専用） |
| Variable | `API_PROVIDER` | `openai` |
| Variable | `API_BASE_URL` | `https://coding.dashscope.aliyuncs.com/v1` |

### Alibaba Cloud Coding Plan — Anthropic 互換

| タイプ | 名前 | 値 |
|---|---|---|
| Secret | `API_KEY` | `sk-sp-xxxxx`（Coding Plan 専用） |
| Variable | `API_PROVIDER` | `anthropic` |
| Variable | `API_BASE_URL` | `https://coding.dashscope.aliyuncs.com/apps/anthropic` |

### ChatGPT Plan

| タイプ | 名前 | 値 |
|---|---|---|
| Secret | `API_KEY` | OpenAI API キー |
| Variable | `API_PROVIDER` | `openai` |
| Variable | `API_BASE_URL` | `https://api.openai.com/v1` |

### Claude / Anthropic

| タイプ | 名前 | 値 |
|---|---|---|
| Secret | `API_KEY` | Anthropic API キー |
| Variable | `API_PROVIDER` | `anthropic` |
| Variable | `API_BASE_URL` | `https://api.anthropic.com/v1` |

### その他のプロバイダー

API エンドポイントとローリング使用量ウィンドウを提供する Coding Plan なら、どのプロバイダーでも使用できます。プロバイダーのダッシュボードで専用 API Key と Base URL を確認してください。

---

## 設定

### リフレッシュ間隔の変更

`.github/workflows/refresh.yml` の `cron` を編集：

| 間隔 | Cron 式 |
|---|---|
| 1時間ごと | `0 */1 * * *` |
| 2時間ごと | `0 */2 * * *` |
| 3時間ごと | `0 */3 * * *` |
| 4時間ごと | `0 */4 * * *` |
| 5時間ごと | `0 */5 * * *` |
| 6時間ごと | `0 */6 * * *` |
| 8時間ごと | `0 */8 * * *` |
| 12時間ごと | `0 */12 * * *` |

## ライセンス

[MIT](../LICENSE) © 2026 wsu2059
