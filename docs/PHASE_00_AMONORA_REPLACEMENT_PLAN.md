# PHASE 00: AMONORA REPLACEMENT PLAN

Дата: `2026-06-07`

## 1. Контекст

`INFINDA` больше не рассматривается как только web-кабинет поверх нового backend.

Целевая постановка:
- `INFINDA` должна стать полноценной заменой `Amonora`;
- продукт должен работать и как web-платформа, и как Telegram-first контур;
- замена должна покрыть не только UI и API, но и платежи, доступ, support, Telegram runtime, admin/backoffice и эксплуатационный слой.

Что уже есть в `INFINDA`:
- модульный `Next.js` frontend `apps/web`;
- модульный `Django + DRF` backend `apps/api`;
- BFF/proxy слой;
- первые общие transport-контракты в `packages/shared`;
- базовые домены `auth`, `profile`, `devices`, `subscription`, `support`, `telegram`, `notifications`, `servers`, `routing`, `access`, `activity`, `health`;
- ETL-контур переноса legacy-данных из `Amonora`.

Что важно:
- `Amonora` все еще остается production-source-of-truth по поведению продукта;
- переход нельзя делать одним шагом;
- feature parity должна быть зафиксирована до начала следующей волны реализации.

## 2. Цель этапа

Зафиксировать baseline замены `Amonora -> INFINDA`, чтобы следующие этапы реализовывались по согласованной карте продукта и архитектуры.

## 3. План этапа

1. Зафиксировать целевую модель `INFINDA` как web + Telegram продукта.
2. Описать parity между `Amonora` и `INFINDA`.
3. Выделить P0-блокеры полной замены.
4. Разбить доработку на этапы миграции.
5. Зафиксировать, что именно считается критерием готовности к cutover.

## 4. Файлы

### Будут созданы

- `docs/PHASE_00_AMONORA_REPLACEMENT_PLAN.md`

### Будут изменены

- `README.md`
- `docs/MEMORY.md`

### Не должны быть затронуты

- `apps/web/*`
- `apps/api/*`
- `packages/shared/*`
- `tests/*`

## 5. Архитектурные договоренности

### Уже согласовано

- `INFINDA` должна быть полноценной заменой `Amonora`.
- У продукта должны быть два полноценных контура: web и Telegram.
- Целевой стек сохраняется: `Next.js` + `Django + DRF`.
- Замена должна идти по этапам, без хаотичного переноса legacy-логики.

### Требует согласования на следующих этапах

- останется ли продукт Telegram-first, или web и Telegram будут равноправными входами;
- будет ли Telegram main bot жить внутри `apps/api` как management/runtime контур или как отдельный сервис рядом;
- какой минимальный набор legacy-платежей обязателен для первого production cutover;
- какой объем dashboard/RBAC/ops нужен до первого переключения.

### Нельзя решать молча

- смену стека;
- отказ от Telegram-контура;
- отказ от публичной подписочной поверхности;
- урезание платежных сценариев без отдельного решения;
- изменение модели provisioning и server access.

## 6. Feature Parity Matrix

| Область | Amonora | INFINDA сейчас | Статус |
|---|---|---|---|
| Маркетинговый web | Публичный сайт, legal, manual | Есть web-страницы и HTML-эталоны | Частично готово |
| Web-кабинет | Нет единого современного кабинета как ядра продукта | Есть модульный кабинет на `Next.js` | Готово как база |
| Auth | Telegram-first и dashboard auth | Есть web auth `register/login/logout/me` | Частично готово |
| Telegram main bot | Полный клиентский продуктовый контур | Есть только linking + support runtime | Не готово |
| Telegram support | Отдельный bot + ticket flow | Есть unified support domain и Telegram runtime | Частично готово |
| Telegram control/admin | Есть отдельный control bot | Нет | Не готово |
| Subscription core | Есть production flow | Есть subscription domain и Platega checkout | Частично готово |
| Public subscription page | Token page, feed, Happ wrapper | Нет отдельной публичной client-surface | Не готово |
| Provisioning VPN access | Реальный provisioning через `3x-ui` / `Xray` | Есть routes/servers/access, но нет полноценного provisioning-адаптера | Не готово |
| Devices lifecycle | Полный lifecycle устройств | Есть список и revoke, но нет полного provisioning lifecycle | Частично готово |
| Routing / regions | Production routing и node-specific logic | Есть route/server catalog foundation | Частично готово |
| Payments | Platega, Stars, crypto, manual, balance | Есть Platega SBP для подписки | Не готово по parity |
| Balance | Есть внутренний RUB balance | Нет | Не готово |
| Referrals / promo | Есть рефералы, промокоды, gift-flow | Нет доменного слоя | Не готово |
| Notifications | Есть user/admin notifications | Есть backend notification domain foundation | Частично готово |
| Dashboard / backoffice | Полноценная ops/admin surface | Есть кастомизированный Django admin | Частично готово |
| RBAC / 2FA | Есть роли и Telegram-code login | Нет полноценного RBAC и Telegram 2FA admin flow | Не готово |
| Support ops | Есть queue/assign/close/admin reply | Есть ticket domain и admin reply flow | Частично готово |
| Finance ops | Есть payments + finance surfaces | Есть только часть платежной админки | Не готово |
| Infra / deploy / watchdog | Есть `systemd`, `nginx`, backups, watchdog, reminders, `n8n` | `infra` почти пустой | Не готово |
| Data migration | Legacy source DB и production данные | Есть ETL-команды импорта | Частично готово |

## 7. P0-блокеры замены

Без закрытия этих пунктов `INFINDA` нельзя ставить вместо `Amonora`.

1. Public client subscription surface
- нужен отдельный публичный web-контур под tokenized subscription page;
- нужны subscription feed, install-flow, Happ-wrapper и клиентский access-touch сценарий.

2. Production provisioning adapter
- `servers/routing/access` уже есть как foundation;
- нужен реальный adapter для `3x-ui` / `Xray` / будущих node runtimes;
- device create/revoke/repair/sync должен управлять реальным доступом, а не только локальными записями.

3. Telegram main product runtime
- нужен полноценный продуктовый main bot;
- бот должен уметь onboarding, кабинет, подписку, устройства, оплату, support entry;
- linking-only контур недостаточен.

4. Payment parity minimum
- нужно явно решить судьбу `Platega`, `manual`, `Stars`, `crypto`, `balance`;
- хотя бы минимальный production-safe набор должен быть реализован до cutover.

5. Admin and operations minimum
- нужны roles, access boundaries, audit, payment operations, support operations, server visibility;
- текущий `Django admin` хорош как foundation, но еще не замена dashboard-контуру `Amonora`.

6. Production infra
- PostgreSQL-first runtime;
- process management;
- reverse proxy;
- backup/restore;
- secrets/env discipline;
- health and watchdog basics.

## 8. Целевая этапность

### Этап 0. Baseline и целевая карта

Результат:
- зафиксирована целевая модель замены;
- зафиксирована parity matrix;
- выделены P0-блокеры.

### Этап 1. Runtime foundation

Результат:
- production database `PostgreSQL`;
- env/config для dev/stage/prod;
- `infra` с базовыми deployment artifacts;
- единый запуск web/api/telegram runtime.

### Этап 2. Public access and provisioning

Результат:
- публичная подписочная поверхность;
- provisioning adapter;
- реальный device lifecycle;
- server health and route availability.

### Этап 3. Telegram product parity

Результат:
- `INFINDA` main bot;
- Telegram onboarding;
- Telegram cabinet/actions;
- Telegram payment entry;
- unified support entry.

### Этап 4. Billing and support parity

Результат:
- минимально достаточная платежная parity;
- support admin workflow;
- notifications;
- device repair and access recovery flows.

### Этап 5. Backoffice and cutover readiness

Результат:
- admin/RBAC minimum;
- finance/support/server operations;
- migration dry-runs;
- cutover checklist.

## 9. Что считаем минимальной готовностью к cutover

`INFINDA` может считаться кандидатом на замену `Amonora`, только если одновременно выполнены все условия:

1. Пользователь может пройти полный путь и через web, и через Telegram.
2. Подписка выдается не только в БД, но и в реальный VPN/runtime access.
3. Есть production-safe платежный контур с подтвержденным post-payment behavior.
4. Support работает в едином домене для web и Telegram.
5. Есть операторский контур для платежей, устройств, подписок и support.
6. Есть deploy/backup/restore/runbook минимум.
7. Миграция legacy-данных проходит предсказуемо и повторяемо.

## 10. Проверки этапа

### Планируемые проверки

- ручная проверка согласованности документа;
- ручная сверка с `README.md` и `docs/MEMORY.md`;
- проверка diff.

### Если что-то пока невозможно

- runtime и интеграционные тесты не нужны на этом этапе, потому что код приложения не меняется.

## 11. Риски

- если дальше идти без зафиксированной parity matrix, реализация снова распадется на несвязанные куски;
- самый опасный риск сейчас: недооценить объем Telegram/provisioning/ops слоя;
- отдельный риск: начать перенос feature-by-feature без решения, какой именно продуктовый вход считается primary.

## 12. Результат этапа

### Должно быть готово

- единый базовый документ шага 0;
- понятный список того, что уже есть и чего не хватает;
- зафиксированная очередность следующих этапов.

### Точно не входит в этап

- реализация Telegram main bot;
- реализация provisioning adapter;
- перенос новых runtime-функций;
- изменение backend/frontend кода.
