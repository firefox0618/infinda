# INFINDA

Проект находится на этапе перехода от HTML-макетов к модульному web/API-приложению.

Текущее состояние:
- Визуальные HTML-макеты находятся в каталоге `шаблоны и работа/` и являются эталоном внешнего вида.
- Инициализированы `apps/web` на `Next.js` и `apps/api` на `Django + DRF`.
- В `apps/web` уже перенесены основные страницы лендинга и служебные экраны: `главная`, `возможности`, `цены`, `ресурсы`, `о нас`, `авторизация`, `личный кабинет`, а также отдельные страницы ошибок.
- Frontend использует `App Router`, feature-слой и общий `shared`-слой.
- Между frontend и backend уже работает BFF/proxy-слой на Next route handlers.
- В `apps/api` уже реализованы базовые доменные модули: `auth`, `profile`, `devices`, `subscription`, `health`.
- В backend уже добавлен административный audit-слой `activity` для журналирования ключевых действий пользователя.
- В `packages/shared` уже вынесен первый реальный слой общих transport-контрактов frontend/backend: DTO, endpoint-paths и единый error-format.

Базовая структура:
- `apps/web` — frontend на `Next.js`.
- `apps/api` — backend API на `Django + DRF`.
- `packages/shared` — общие типы, контракты, утилиты.
- `tests` — интеграционные, e2e и служебные тесты.
- `infra` — инфраструктурные файлы.
- `docs` — документация проекта и рабочие правила.

Документация:
- [AGENTS.md](AGENTS.md) — единый источник постоянных правил работы
- [docs/MEMORY.md](docs/MEMORY.md)
- [docs/RULES.md](docs/RULES.md)
- [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)
- [docs/PHASE_01_FOUNDATION.md](docs/PHASE_01_FOUNDATION.md)
- [docs/TASK_PLAN_TEMPLATE.md](docs/TASK_PLAN_TEMPLATE.md) — шаблон плана перед реализацией

Что уже реализовано:
- В `apps/web` перенесены страницы `главная`, `возможности`, `цены`, `ресурсы`, `о нас`, `авторизация`, `личный кабинет`.
- Общие `header` и `footer` вынесены в layout-слой.
- Для мобильной версии добавлен общий burger-menu паттерн.
- Для frontend выделены общие слои `shared/layout`, `shared/ui`, `shared/styles`, `shared/auth`, `shared/config`.
- Страницы маршрутов в `src/app` работают как тонкие entry-point'ы, а основная UI-логика вынесена в `src/features`.
- Frontend `/api/*` route handlers проксируют auth/profile/devices/subscription запросы в локальный Django backend.
- Backend уже отдает рабочие API для входа, профиля, устройств, подписки и health-check.
- Backend уже отдает рабочие API для регистрации, входа, профиля, устройств, подписки и health-check.
- При регистрации новый пользователь автоматически получает trial-подписку на 3 дня с базовыми маршрутами, чтобы кабинет открывался сразу в рабочем состоянии.
- API подписки теперь отдает явные состояния `none / trial / active / expired`, чтобы кабинет корректно показывал empty-state и сценарий истекшего доступа без `404`.
- Для подписок уже есть первый purchase-flow без реальных платежей: `GET /api/subscription/plans/` отдает каталог тарифов, а `POST /api/subscription/purchase/` сразу активирует или продлевает подписку.
- Для `Platega SBP` уже подключен реальный checkout-flow: `POST /api/subscription/checkout/` создает платежную сессию, webhook `POST /api/subscription/webhooks/platega/<secret>/` подтверждает оплату и активирует подписку.
- Для backend уже есть доменные API-тесты.
- Для API введен единый error-contract вида `error.code / error.message / error.details`.
- Django admin показывает ФИО пользователя, связанный профиль, историю действий и жизненный статус устройств.

Переменные окружения для платежного контура backend:
- `PLATEGA_MERCHANT_ID`
- `PLATEGA_SECRET_KEY`
- `PLATEGA_BASE_URL`
- `PLATEGA_WEBHOOK_SECRET`
- `PLATEGA_RETURN_URL`
- `PLATEGA_FAILED_URL`

Принцип работы:
- Сначала планирование и уточнение.
- Затем согласование ключевых решений.
- После этого реализация небольшими понятными этапами.
- Постоянные правила процесса хранятся в `AGENTS.md`.
