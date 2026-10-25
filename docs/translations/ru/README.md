<p align="center">
  <img src="../../assets/readme/hero-banner.png" width="800" alt="Plex AI by pNet с фирменным знаком Triad на тёмном минеральном фоне">
</p>

# Plex AI

[English](../../../README.md) · [Русский](README.md) · [Deutsch](../de/README.md) · [简体中文](../zh-CN/README.md)

**Соберите команду. Координируйте работу.**

Plex — **agent harness для оркестрации и координации нескольких агентов** в
OpenAI Codex, Anthropic Claude Code и Google Antigravity. Установите готовую команду,
выберите профиль моделей и поручите Plex организовать реализацию, ревью и проверку.

[![Latest Release](https://img.shields.io/github/v/release/pnetcloud/plex-ai?display_name=tag&style=flat-square)](https://github.com/pnetcloud/plex-ai/releases/latest) [![CI](https://github.com/pnetcloud/plex-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/pnetcloud/plex-ai/actions/workflows/ci.yml) [![MIT License](https://img.shields.io/github/license/pnetcloud/plex-ai?style=flat-square)](https://github.com/pnetcloud/plex-ai/blob/main/LICENSE)

**[Начать](#quickstart)** · **[Как это работает](../../../README.md#how-it-works)** · **[Документация](index.md)** · **[Релизы](https://github.com/pnetcloud/plex-ai/releases/latest)** · **[Сообщить о проблеме](https://github.com/pnetcloud/plex-ai/issues)**

**Статус: активная разработка; версия доступна для оценки.** Поддержка и объём проверок зависят
от клиента.

<a id="quickstart"></a>

## Быстрый старт

Запустите в папке проекта. Требуются Git, curl, CLI выбранного клиента и uv или Python 3.11+:

```sh
curl -fsSL https://raw.githubusercontent.com/pnetcloud/plex-ai/main/install.sh | bash
```

**Dev-режим · Codex · локальные скиллы проекта**

```sh
curl -fsSL https://raw.githubusercontent.com/pnetcloud/plex-ai/main/install.sh | bash -s -- --dev --client codex
```

Выберите клиентов, область, команду и профиль моделей; подтвердите план. Рекомендуется область **Project**. После установки откройте новую сессию клиента.

Обычный установщик делает обе части настройки:

- **Общий плагин** — переиспользуемые скиллы `plex` и `plex-setup` для клиента.
- **Команда** — нативные роли агентов и управляемый блок инструкций на уровне проекта или пользователя.

Один плагин ещё не настраивает команду. В dev-режиме используются ссылки на локальные скиллы вместо общего плагина Plex в этом проекте.

[Требования, BMad, dev-режим и все параметры](installation.md).

## Как это работает

Текущий чат остаётся координатором и сохраняет свою модель. Каждая новая задача сначала получает короткую оценку `plex-pm`. Координатор следует её маршруту, собирает нужные решения специалистов, затем передаёт реализацию dev и проверяет итог. Для уже охваченных шагов оценка переиспользуется.

```mermaid
flowchart TD
    A[Ваша задача] --> B[Текущий чат координирует]
    B --> P[Короткая оценка PM]
    P --> C[Выбранные роли выполняют поручения]
    C --> D[Координатор объединяет и проверяет]
```

## Примеры в чате

Это **запросы в чате, а не команды терминала**. Замените плейсхолдеры в угловых скобках перед отправкой.

**Скоординировать задачу · плагин Codex**

```text
$plex Скоординируй <задачу>. Требования: <требования>. Проверь <критерии приёмки>.
```

**Провести ревью изменений**

```text
$plex Проведи ревью <изменений> по <требованиям>. Укажи замечания и пробелы в проверках.
```

**Проверить или настроить команду**

```text
$plex-setup Проверь конфигурацию Plex в этом проекте.
$plex-setup Настрой проект: команда <команда>, профиль <профиль>, взаимодействие <режим>.
```

**Координация задачи · плагин Claude Code**

```text
/pnet-plex:plex Выполни <задачу>. Требования: <требования>. Проверь <критерии приёмки>.
/pnet-plex:plex-setup Проверь конфигурацию Plex в этом проекте.
```

В Codex используйте `$plex` и `$plex-setup` при обычной и dev-установке. В других клиентах выберите установленный скилл или явно попросите: `Используй Plex для координации <задачи>.`

Установка не запускает координацию автоматически. `plex-setup` меняет конфигурацию, `plex` координирует работу.

## Команды и модели

| Команда | Назначение |
|---|---|
| **pnet** | Обычная разработка: PM, explorer, researcher, dev, reviewer, QA и DevOps; BMad не требуется |
| **bmad** | Установленные персоны и workflow BMad плюс нативный DevOps; установщик предлагает выбранные зависимости и инициализацию проекта |

Профили **Inherit, Basic, Plus, Pro, Pro+, Ultra, Ultra+** задают модели субагентов. Модель основного чата выбираете вы; установщик показывает рекомендацию выбранного профиля. См. [конфигурацию](configuration.md).

### Режимы оркестрации агентов

Plex — **оркестратор ИИ-агентов (AI agent orchestrator)** внутри вашего клиента.
Текущий чат работает как **координатор**: PM ставит задачу, профильные субагенты
готовят решения, разработчики выполняют работу для ревью. Профили распределяют
Luna, Sol и Astra либо Haiku, Sonnet и Opus между ролями; координатор сохраняет модель вашего чата.

Три независимые настройки: **команда** (`pnet` или workflow BMad),
**профиль моделей** (Inherit / Basic / Plus / Pro / Pro+ / Ultra / Ultra+) и **режим взаимодействия**:

| Режим | Как команда работает с вами |
|---|---|
| **Interactive** | Совместно уточняет требования и значимые решения |
| **Balanced** · по умолчанию | Решает рутинные вопросы; спрашивает о существенных нерешённых вопросах и обязательных согласованиях |
| **Auto** | Выполняет разрешённую работу без ожидания ответов; возвращает результаты и блокеры |

### Модели по профилям

Это **профили конфигурации Plex**, независимые от тарифов провайдеров.
В ячейках — **разработка → ревью кода** для встроенной команды `pnet`.

| Клиент / провайдер моделей | Basic | Plus | Pro | Pro+ | Ultra | Ultra+ |
|---|---|---|---|---|---|---|
| OpenAI Codex | Luna → Luna | Luna → Sol | Luna → Sol | Sol → Sol | Sol → Astra | Sol → Astra |
| Claude Code / Anthropic | Haiku → Haiku | Haiku → Sonnet | Haiku → Sonnet | Sonnet → Sonnet | Sonnet → Opus | Sonnet → Opus |
| Antigravity / Google Gemini | `flash` → `flash` | `flash` → `inherit` | `flash` → `inherit` | `inherit` → `inherit` | `inherit` → `inherit` | `inherit` → `inherit` |
| Antigravity / Anthropic | Sonnet low → Sonnet low | Sonnet low → Sonnet medium | Sonnet low → Sonnet high | Sonnet medium → Sonnet high | Sonnet medium → Opus medium | Sonnet high → Opus high |

- **Basic:** одна базовая модель для ролей `pnet`. **Plus:** разделение моделей реализации и ревью, где это задано профилем.
- **Pro:** больше рассуждений для отдельных ролей; семейства моделей могут оставаться прежними. **Pro+:** разработка и ревью на Sol/Sonnet. **Ultra:** подключаются специалисты Astra/Opus. **Ultra+:** повышается reasoning.
- **BMad:** те же пары разработки и ревью, но уже в Basic ревью выполняет Sol, Sonnet, `inherit` или Sonnet medium соответственно. Планирование, архитектура и остальные роли имеют свои настройки.
- **Inherit:** настройки клиента/сессии. В профилях Gemini значение `inherit` не закрепляет модель Gemini Pro.

Идентификаторы в конфигурации: Luna = `gpt-6-luna`, Sol = `gpt-6.1-sol`, Astra = `gpt-6-astra`.
Claude Code использует алиасы `haiku`, `sonnet`, `opus`; профили Anthropic в Antigravity —
`claude-sonnet-5-5-{low,medium,high}` и `claude-opus-5-5-{low,medium,high}`.
Это поставляемые настройки, без гарантии доступности моделей или экономии. Установщик показывает итоговую конфигурацию с учётом переопределений проекта.

[Все роли pnet](../../../teams/pnet/profiles/) · [Все роли BMad](../../../teams/bmad/profiles/) · [Настройка профилей](configuration.md)

## Команды терминала

| Задача | Команда |
|---|---|
| Настроить или обновить конфигурацию проекта | `plex` |
| Проверить установку | `plex status` |
| Скачать обновление и открыть настройку | `plex update` |
| Посмотреть план удаления команды | `plex uninstall --dry-run` |
| Удалить команду из этого проекта | `plex uninstall` |

Если необязательной команды `plex` нет, используйте `~/.local/share/plex-ai/setup.sh`. В установщике **Update only** сохраняет настройки, **Reconfigure** открывает меню.

## Удаление

Запустите `plex uninstall` из папки проекта. Команда удалит неизменённые управляемые роли, блок Plex и ссылки на скиллы и dev-override; окружающие инструкции сохранятся. Настройки, резервные копии и общий плагин останутся.

Чтобы также удалить общий **плагин Codex**, когда другие проекты больше в нём не нуждаются:

```sh
codex plugin remove pnet-plex@pnet-plex
```

Другие клиенты и удаление команды уровня пользователя описаны в [руководстве](installation.md#удаление).

## Подробнее

- [Сообщить о проблеме](https://github.com/pnetcloud/plex-ai/issues).
- [Документация](index.md) — подробности настройки и использования.
- [Участие в разработке](../../../CONTRIBUTING.md).
- [О Plex](product.md) — назначение и принципы.
- [Совместимость](host-compatibility.md) — живые тесты Codex и отдельных конфигураций Antigravity; нативный Claude Code пока не проверен на живых задачах.
- [Тестирование и эффективность](testing.md) — методика, измерения токенов/стоимости и субъективная оценка качества.
- [Архитектура](architecture.md) — как связаны конфигурация и координация.

## Лицензия

[MIT](../../../LICENSE). Инструкции агентов адаптированы с опорой на [Awesome Codex Subagents](https://github.com/VoltAgent/awesome-codex-subagents);
см. [сторонние материалы](../../../THIRD_PARTY_NOTICES.md).
