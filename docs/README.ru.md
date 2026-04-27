# AI Usage Refresh (Автообновление использования AI)

**Держите квоту использования AI Coding Plan на фиксированном цикле. Больше никакого расхода квоты.**

[![GitHub Actions](https://img.shields.io/badge/GitHub-Actions-blue?logo=github)](https://github.com/features/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)

🌍 **Языки:** [English](../README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [Русский](README.ru.md)

---

## Проблема

Большинство сервисов AI-кодинга (ChatGPT Plan, ZAI Coding, Alibaba Cloud Coding Plan, Claude и др.) сбрасывают квоту использования по **скользящему окну** — 5-часовой таймер запускается при **первом использовании** API, а не по фиксированному расписанию.

Это приводит к **потере квоты**:

```
Скользящее окно (ПОТЕРИ):
Таймлайн: ──использование──5h──сброс──────использование──5h──сброс──
          0h               5h              7h              12h
          ❌ Таймер запускается с первого использования, непредсказуемо сдвигается
          ❌ Например: осталось 2ч в цикле, использование даёт 2h+5h=7h
             но вы получаете только 2 цикла квоты за этот период

Фиксированный цикл (ОПТИМАЛЬНО):
Таймлайн: ──обновление──5h──обновление──5h──обновление──5h──обновление──
          0h                     5h                      10h                     15h
          ✅ Таймер сбрасывается по предсказуемому расписанию
          ✅ Максимальное использование квоты каждый цикл
```

## Решение

Этот репозиторий использует **GitHub Actions** для отправки минимального API-запроса (`"hi"`, `max_tokens: 1`) с фиксированным интервалом, привязывая ваш таймер использования к **предсказуемому расписанию**.

- **Нулевая стоимость** — работает на бесплатных минутах GitHub Actions
- **Нулевые зависимости** — чистый `curl`, без runtime
- **Минимальное потребление токенов** — 1 токен за обновление
- **Полная настройка** — интервал, провайдер, модель, endpoint настраиваются через GitHub Variables

## Быстрый старт

### 1. Форкните этот репозиторий

Нажмите **Fork** в правом верхнем углу.

### 2. Настройте Secrets и Variables

Перейдите в ваш форк → **Settings** → **Secrets and variables** → **Actions**

**Обязательно — добавьте Secret:**

| Имя | Значение |
|---|---|
| `API_KEY` | Ваш API-ключ Coding Plan |

**Опционально — добавьте Variables:**

| Имя | Описание | По умолчанию |
|---|---|---|
| `API_PROVIDER` | `openai`, `anthropic` или `custom` | `openai` |
| `API_BASE_URL` | URL эндпоинта вашего Coding Plan | По умолчанию провайдера |
| `MODEL` | Имя модели | По умолчанию провайдера |

### 3. Включите Actions

Перейдите на вкладку **Actions** → Нажмите **"I understand my workflows, go ahead and enable them"**

### 4. Готово!

Запускается автоматически. Также можно запустить вручную через **Actions** → **Run workflow**.

---

## Примеры настройки провайдеров

### 智譜 (ZAI) Coding Plan

Получите API Key на [open.bigmodel.cn](https://open.bigmodel.cn) → Coding Plan.

| Тип | Имя | Значение |
|---|---|---|
| Secret | `API_KEY` | Ключ Coding Plan |
| Variable | `API_PROVIDER` | `openai` |
| Variable | `API_BASE_URL` | `https://open.bigmodel.cn/api/coding/paas/v4` |

### Alibaba Cloud Coding Plan — совместимость с OpenAI

Получите **эксклюзивный** API Key (формат: `sk-sp-xxxxx`) на странице Coding Plan.

> ⚠️ Эксклюзивный API Key Coding Plan (`sk-sp-xxxxx`) и Base URL **несовместимы** с обычными ключами оплаты по факту использования (`sk-xxxxx`). Не смешивайте их.

| Тип | Имя | Значение |
|---|---|---|
| Secret | `API_KEY` | `sk-sp-xxxxx` (эксклюзивный Coding Plan) |
| Variable | `API_PROVIDER` | `openai` |
| Variable | `API_BASE_URL` | `https://coding.dashscope.aliyuncs.com/v1` |

### Alibaba Cloud Coding Plan — совместимость с Anthropic

| Тип | Имя | Значение |
|---|---|---|
| Secret | `API_KEY` | `sk-sp-xxxxx` (эксклюзивный Coding Plan) |
| Variable | `API_PROVIDER` | `anthropic` |
| Variable | `API_BASE_URL` | `https://coding.dashscope.aliyuncs.com/apps/anthropic` |

### ChatGPT Plan

| Тип | Имя | Значение |
|---|---|---|
| Secret | `API_KEY` | Ваш OpenAI API-ключ |
| Variable | `API_PROVIDER` | `openai` |
| Variable | `API_BASE_URL` | `https://api.openai.com/v1` |

### Claude / Anthropic

| Тип | Имя | Значение |
|---|---|---|
| Secret | `API_KEY` | Ваш Anthropic API-ключ |
| Variable | `API_PROVIDER` | `anthropic` |
| Variable | `API_BASE_URL` | `https://api.anthropic.com/v1` |

### Другие провайдеры

Любой провайдер с Coding Plan, API-эндпоинтом и скользящим окном использования поддерживается. Проверьте панель управления провайдера для получения эксклюзивного API Key и Base URL.

---

## Настройка

### Изменение интервала обновления

Отредактируйте выражение `cron` в `.github/workflows/refresh.yml`:

| Интервал | Выражение Cron |
|---|---|
| Каждый 1 час | `0 */1 * * *` |
| Каждые 2 часа | `0 */2 * * *` |
| Каждые 3 часа | `0 */3 * * *` |
| Каждые 4 часа | `0 */4 * * *` |
| Каждые 5 часов | `0 */5 * * *` |
| Каждые 6 часов | `0 */6 * * *` |
| Каждые 8 часов | `0 */8 * * *` |
| Каждые 12 часов | `0 */12 * * *` |

Создайте своё расписание на [crontab.guru](https://crontab.guru).

## Лицензия

[MIT](../LICENSE) © 2026 wsu2059
