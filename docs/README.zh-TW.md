# AI Usage Refresh（AI 編程套餐用量自動刷新）

**讓你的 AI Coding Plan 用量配額保持固定週期，不再浪費配額。**

[![GitHub Actions](https://img.shields.io/badge/GitHub-Actions-blue?logo=github)](https://github.com/features/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)

🌍 **語言:** [English](../README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Русский](README.ru.md)

---

## 問題是什麼？

大多數 AI 程式設計套餐服務（ChatGPT Plan、智譜 Coding、阿里雲 Coding Plan、Claude 等）的用量配額採用**滾動視窗**重置機制——5 小時計時器從你**首次使用** API 時開始，而非固定時間表。

這會導致**配額浪費**：

```
滾動視窗（浪費配額）：
時間軸: ──使用──5h──重置──────────使用──5h──重置──────
        0h    5h              7h   12h
        ❌ 計時器從首次使用開始，不可預測地偏移
        ❌ 比如一個週期還剩 2h，你用了就是 2h+5h=7h
           但這段區間裡你只用了 2 個週期的配額

固定週期（最佳方案）：
時間軸: ──刷新──5h──刷新──5h──刷新──5h──刷新──
        0h            5h           10h          15h
        ✅ 計時器在可預測的時間表上重置
        ✅ 每個週期最大化配額利用率
```

**舉個例子：** 你的套餐每 5 小時重置一次。你在某個週期的第 2 小時開始寫程式。使用服務會啟動一個*新的* 5 小時計時器。現在你的重置時間變成了第 7 小時而非第 5 小時——前一個週期的 2 小時配額被白白浪費了。

## 解決方案

本倉庫使用 **GitHub Actions** 按固定間隔發送最小化 API 請求（`"hi"`，`max_tokens: 1`），將你的用量計時器鎖定在**可預測的時間表**上。

- **零成本** — 使用免費的 GitHub Actions 運行時間
- **零依賴** — 純 `curl`，無需任何執行環境
- **極小 token 消耗** — 每次刷新僅 1 個 token，幾乎免費
- **完全可配置** — 間隔、服務商、模型、端點均可透過 GitHub 變數調整

## 工作原理

1. GitHub Actions 按你配置的時間表觸發（預設：每 5 小時）
2. 向你的 Coding Plan 端點發送一個最小化 API 請求
3. 觸發服務商的用量計時器重置
4. 配額週期保持在固定時間表上
5. 當你實際寫程式時，計時器已經同步 → 最大化配額

## 快速開始

### 1. Fork 本倉庫

點擊頁面右上角的 **Fork** 按鈕。

### 2. 配置密鑰和變數

進入你 Fork 的倉庫 → **Settings** → **Secrets and variables** → **Actions**

**必填 — 新增密鑰：**

| 名稱 | 值 |
|---|---|
| `API_KEY` | 你的 Coding Plan API 密鑰 |

**可選 — 新增變數：**

| 名稱 | 說明 | 預設值 |
|---|---|---|
| `API_PROVIDER` | `openai`、`anthropic` 或 `custom` | `openai` |
| `API_BASE_URL` | 你的 Coding Plan 端點 URL | 服務商預設 |
| `MODEL` | 模型名稱 | 服務商預設 |

### 3. 啟用 Actions

進入 **Actions** 標籤 → 點擊 **"I understand my workflows, go ahead and enable them"**

### 4. 完成！

自動運行。也可以透過 **Actions** → **Run workflow** 手動觸發。

---

## 各服務商配置範例

### 智譜（ZAI）Coding Plan

在 [open.bigmodel.cn](https://open.bigmodel.cn) → Coding Plan 頁面取得 API Key。

| 類型 | 名稱 | 值 |
|---|---|---|
| Secret | `API_KEY` | 你的 Coding Plan 密鑰 |
| Variable | `API_PROVIDER` | `openai` |
| Variable | `API_BASE_URL` | `https://open.bigmodel.cn/api/coding/paas/v4` |

### 阿里雲 Coding Plan — OpenAI 相容

在 Coding Plan 頁面取得**專屬** API Key（格式：`sk-sp-xxxxx`）。

> ⚠️ Coding Plan 專屬 API Key（`sk-sp-xxxxx`）和 Base URL 與百鍊按量計費的 API Key（`sk-xxxxx`）**不互通**，請勿混用。

| 類型 | 名稱 | 值 |
|---|---|---|
| Secret | `API_KEY` | `sk-sp-xxxxx`（Coding Plan 專屬） |
| Variable | `API_PROVIDER` | `openai` |
| Variable | `API_BASE_URL` | `https://coding.dashscope.aliyuncs.com/v1` |

### 阿里雲 Coding Plan — Anthropic 相容

| 類型 | 名稱 | 值 |
|---|---|---|
| Secret | `API_KEY` | `sk-sp-xxxxx`（Coding Plan 專屬） |
| Variable | `API_PROVIDER` | `anthropic` |
| Variable | `API_BASE_URL` | `https://coding.dashscope.aliyuncs.com/apps/anthropic` |

### ChatGPT Plan

| 類型 | 名稱 | 值 |
|---|---|---|
| Secret | `API_KEY` | 你的 OpenAI API Key |
| Variable | `API_PROVIDER` | `openai` |
| Variable | `API_BASE_URL` | `https://api.openai.com/v1` |

### Claude / Anthropic

| 類型 | 名稱 | 值 |
|---|---|---|
| Secret | `API_KEY` | 你的 Anthropic API Key |
| Variable | `API_PROVIDER` | `anthropic` |
| Variable | `API_BASE_URL` | `https://api.anthropic.com/v1` |

### 其他服務商

任何提供 Coding Plan 且有 API 端點和滾動用量視窗的服務商都可以使用。查看你的服務商控制台取得專屬 API Key 和 Base URL，然後：

| 類型 | 名稱 | 值 |
|---|---|---|
| Secret | `API_KEY` | 你的服務商 API 密鑰 |
| Variable | `API_PROVIDER` | `openai` 或 `anthropic`（取決於相容性） |
| Variable | `API_BASE_URL` | 你的服務商端點 |
| Variable | `MODEL` | 支援的模型名稱 |

---

## 配置

### 修改刷新間隔

編輯 `.github/workflows/refresh.yml` 並修改 `cron` 表達式：

```yaml
on:
  schedule:
    - cron: '0 */5 * * *'  # 修改此處
```

**常用間隔：**

| 間隔 | Cron 表達式 |
|---|---|
| 每 1 小時 | `0 */1 * * *` |
| 每 2 小時 | `0 */2 * * *` |
| 每 3 小時 | `0 */3 * * *` |
| 每 4 小時 | `0 */4 * * *` |
| 每 5 小時 | `0 */5 * * *` |
| 每 6 小時 | `0 */6 * * *` |
| 每 8 小時 | `0 */8 * * *` |
| 每 12 小時 | `0 */12 * * *` |

可在 [crontab.guru](https://crontab.guru) 生成自訂時間表。

## 常見問題

**Q: 這會花錢嗎？**
A: 每次請求僅使用 1 個 token（最小值）。任何服務商的價格下都幾乎為 $0。

**Q: GitHub 會收我 Actions 的費用嗎？**
A: 公開倉庫享有無限的免費 Actions 運行時間。私有倉庫每月大約使用 ~1 分鐘，遠在免費額度內。

**Q: 請求失敗了怎麼辦？**
A: 工作流會顯示為失敗，透過 Actions 標籤可以手動重新觸發。

**Q: 為什麼不直接正常使用服務？**
A: 你當然應該正常使用！這個工具是在正常使用之外*額外*運行的，確保配額計時器保持在固定時間表上，讓你每個週期都能最大化利用配額。

## 授權條款

[MIT](../LICENSE) © 2026 wsu2059
