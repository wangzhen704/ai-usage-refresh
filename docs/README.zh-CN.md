# AI Usage Refresh（AI 编程套餐用量自动刷新）

**让你的 AI Coding Plan 用量配额保持固定周期，不再浪费配额。**

[![GitHub Actions](https://img.shields.io/badge/GitHub-Actions-blue?logo=github)](https://github.com/features/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)

🌍 **语言:** [English](../README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Русский](README.ru.md)

---

## 问题是什么？

大多数 AI 编程套餐服务（ChatGPT Plan、智谱 Coding、阿里云 Coding Plan、Claude 等）的用量配额采用**滚动窗口**重置机制——5 小时计时器从你**首次使用** API 时开始，而非固定时间表。

这会导致**配额浪费**：

```
滚动窗口（浪费配额）：
时间轴: ──使用──5h──重置──────────使用──5h──重置──────
        0h    5h              7h   12h
        ❌ 计时器从首次使用开始，不可预测地偏移
        ❌ 比如一个周期还剩 2h，你用了就是 2h+5h=7h
           但这段区间里你只用了 2 个周期的配额

固定周期（最佳方案）：
时间轴: ──刷新──5h──刷新──5h──刷新──5h──刷新──
        0h            5h           10h          15h
        ✅ 计时器在可预测的时间表上重置
        ✅ 每个周期最大化配额利用率
```

**举个例子：** 你的套餐每 5 小时重置一次。你在某个周期的第 2 小时开始编程。使用服务会启动一个*新的* 5 小时计时器。现在你的重置时间变成了第 7 小时而非第 5 小时——前一个周期的 2 小时配额被白白浪费了。

## 解决方案

本仓库使用 **GitHub Actions** 按固定间隔发送最小化 API 请求（`"hi"`，`max_tokens: 1`），将你的用量计时器锁定在**可预测的时间表**上。

- **零成本** — 使用免费的 GitHub Actions 运行时长
- **零依赖** — 纯 `curl`，无需任何运行时
- **极小 token 消耗** — 每次刷新仅 1 个 token，几乎免费
- **完全可配置** — 间隔、服务商、模型、端点均可通过 GitHub 变量调整

## 工作原理

1. GitHub Actions 按你配置的时间表触发（默认：每 5 小时）
2. 向你的 Coding Plan 端点发送一个最小化 API 请求
3. 触发服务商的用量计时器重置
4. 配额周期保持在固定时间表上
5. 当你实际编程时，计时器已经同步 → 最大化配额

## 快速开始

### 1. Fork 本仓库

点击页面右上角的 **Fork** 按钮。

### 2. 配置密钥和变量

进入你 Fork 的仓库 → **Settings** → **Secrets and variables** → **Actions**

**必填 — 添加密钥：**

| 名称 | 值 |
|---|---|
| `API_KEY` | 你的 Coding Plan API 密钥 |

**可选 — 添加变量：**

| 名称 | 说明 | 默认值 |
|---|---|---|
| `API_PROVIDER` | `openai`、`anthropic` 或 `custom` | `openai` |
| `API_BASE_URL` | 你的 Coding Plan 端点 URL | 服务商默认 |
| `MODEL` | 模型名称 | 服务商默认 |

### 3. 启用 Actions

进入 **Actions** 标签 → 点击 **"I understand my workflows, go ahead and enable them"**

### 4. 完成！

自动运行。也可以通过 **Actions** → **Run workflow** 手动触发。

---

## 各服务商配置示例

### 智谱（ZAI）Coding Plan

在 [open.bigmodel.cn](https://open.bigmodel.cn) → Coding Plan 页面获取 API Key。

| 类型 | 名称 | 值 |
|---|---|---|
| Secret | `API_KEY` | 你的 Coding Plan 密钥 |
| Variable | `API_PROVIDER` | `openai` |
| Variable | `API_BASE_URL` | `https://open.bigmodel.cn/api/coding/paas/v4` |

### 阿里云 Coding Plan — OpenAI 兼容

在 Coding Plan 页面获取**专属** API Key（格式：`sk-sp-xxxxx`）。

> ⚠️ Coding Plan 专属 API Key（`sk-sp-xxxxx`）和 Base URL 与百炼按量计费的 API Key（`sk-xxxxx`）**不互通**，请勿混用。

| 类型 | 名称 | 值 |
|---|---|---|
| Secret | `API_KEY` | `sk-sp-xxxxx`（Coding Plan 专属） |
| Variable | `API_PROVIDER` | `openai` |
| Variable | `API_BASE_URL` | `https://coding.dashscope.aliyuncs.com/v1` |

### 阿里云 Coding Plan — Anthropic 兼容

| 类型 | 名称 | 值 |
|---|---|---|
| Secret | `API_KEY` | `sk-sp-xxxxx`（Coding Plan 专属） |
| Variable | `API_PROVIDER` | `anthropic` |
| Variable | `API_BASE_URL` | `https://coding.dashscope.aliyuncs.com/apps/anthropic` |

### ChatGPT Plan

| 类型 | 名称 | 值 |
|---|---|---|
| Secret | `API_KEY` | 你的 OpenAI API Key |
| Variable | `API_PROVIDER` | `openai` |
| Variable | `API_BASE_URL` | `https://api.openai.com/v1` |

### Claude / Anthropic

| 类型 | 名称 | 值 |
|---|---|---|
| Secret | `API_KEY` | 你的 Anthropic API Key |
| Variable | `API_PROVIDER` | `anthropic` |
| Variable | `API_BASE_URL` | `https://api.anthropic.com/v1` |

### 其他服务商

任何提供 Coding Plan 且有 API 端点和滚动用量窗口的服务商都可以使用。查看你的服务商控制面板获取专属 API Key 和 Base URL，然后：

| 类型 | 名称 | 值 |
|---|---|---|
| Secret | `API_KEY` | 你的服务商 API 密钥 |
| Variable | `API_PROVIDER` | `openai` 或 `anthropic`（取决于兼容性） |
| Variable | `API_BASE_URL` | 你的服务商端点 |
| Variable | `MODEL` | 支持的模型名称 |

---

## 配置

### 修改刷新间隔

编辑 `.github/workflows/refresh.yml` 并修改 `cron` 表达式：

```yaml
on:
  schedule:
    - cron: '0 */5 * * *'  # 修改此处
```

**常用间隔：**

| 间隔 | Cron 表达式 |
|---|---|
| 每 1 小时 | `0 */1 * * *` |
| 每 2 小时 | `0 */2 * * *` |
| 每 3 小时 | `0 */3 * * *` |
| 每 4 小时 | `0 */4 * * *` |
| 每 5 小时 | `0 */5 * * *` |
| 每 6 小时 | `0 */6 * * *` |
| 每 8 小时 | `0 */8 * * *` |
| 每 12 小时 | `0 */12 * * *` |

可在 [crontab.guru](https://crontab.guru) 生成自定义时间表。

## 常见问题

**Q: 这会花钱吗？**
A: 每次请求仅使用 1 个 token（最小值）。任何服务商的价格下都几乎为 $0。

**Q: GitHub 会收我 Actions 的钱吗？**
A: 公开仓库享有无限的免费 Actions 运行时长。私有仓库每月大约使用 ~1 分钟，远在免费额度内。

**Q: 请求失败了怎么办？**
A: 工作流会显示为失败，通过 Actions 标签可以手动重新触发。

**Q: 为什么不直接正常使用服务？**
A: 你当然应该正常使用！这个工具是在正常使用之外*额外*运行的，确保配额计时器保持在固定时间表上，让你每个周期都能最大化利用配额。

## 许可证

[MIT](../LICENSE) © 2026 wsu2059
