# INFINDA

Проект находится на этапе перехода от HTML-макетов к модульному web/API-приложению.

Текущее состояние:
- Визуальные HTML-макеты находятся в каталоге `шаблоны и работа/` и являются эталоном внешнего вида.
- Инициализированы `apps/web` на `Next.js` и `apps/api` на `Django + DRF`.
- Целевая постановка проекта зафиксирована как полная замена `Amonora`: `INFINDA` должна стать полноценной и как web-платформа, и как Telegram-продукт.
- В `apps/web` уже перенесены основные страницы лендинга и служебные экраны: `главная`, `возможности`, `цены`, `ресурсы`, `о нас`, `авторизация`, `личный кабинет`, а также отдельные страницы ошибок.
- Frontend использует `App Router`, feature-слой и общий `shared`-слой.
- Между frontend и backend уже работает BFF/proxy-слой на Next route handlers.
- В `apps/api` уже реализованы базовые доменные модули: `auth`, `profile`, `devices`, `subscription`, `support`, `telegram`, `notifications`, `servers`, `routing`, `access`, `health`.
- В backend теперь также начат отдельный provisioning-домен: профили серверов и журнал операций синхронизации/отзыва доступа больше не должны жить скрытой логикой внутри `devices` или `subscription`.
- В provisioning-домене теперь появился реальный adapter layer `mock/manual/xui`: операции уже могут валидировать живую XUI-панель и inbound, а также materialize-ить отдельные device bindings с внешним `client_uuid/email/inbound`.
- В backend уже добавлен административный audit-слой `activity` для журналирования ключевых действий пользователя.
- В `packages/shared` уже вынесен первый реальный слой общих transport-контрактов frontend/backend: DTO, endpoint-paths и единый error-format.
- В `Phase 1` уже начат `runtime foundation`: backend теперь умеет работать с `PostgreSQL`, а в `infra/` появился первый локальный стек `postgres + api + web + telegram-bot`.
- В `infra/` теперь также появились первые server-run шаблоны: env, `systemd` и `nginx`.
- В `Phase 2` начат `public access`: у подписок появился безопасный публичный токен, backend summary endpoint и первая страница `/sub/[token]`.
- Генерация подписочных ссылок теперь разделена по типам: page/feed, Happ wrapper, Happ routing settings и отдельные ссылки по серверам, чтобы frontend не собирал их вручную.
- Публичная подписочная страница теперь также несет install-flow для Happ: backend отдает платформенные install-guides, а frontend показывает быстрые действия и route-level импорт по странам.

Базовая структура:
- `apps/web` — frontend на `Next.js`.
- `apps/api` — backend API на `Django + DRF`.
- `packages/shared` — общие типы, контракты, утилиты.
- `tests` — заготовка под интеграционные, e2e и служебные тесты уровня репозитория.
- `infra` — заготовка под инфраструктурные файлы.
- `docs` — документация проекта и рабочие правила.

Документация:
- [AGENTS.md](AGENTS.md) — единый источник постоянных правил работы
- [docs/MEMORY.md](docs/MEMORY.md)
- [docs/RULES.md](docs/RULES.md)
- [docs/PHASE_00_AMONORA_REPLACEMENT_PLAN.md](docs/PHASE_00_AMONORA_REPLACEMENT_PLAN.md)
- [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)
- [docs/PROJECT_REVIEW_REPORT.md](docs/PROJECT_REVIEW_REPORT.md)
- [docs/PHASE_01_FOUNDATION.md](docs/PHASE_01_FOUNDATION.md)
- [docs/TASK_PLAN_TEMPLATE.md](docs/TASK_PLAN_TEMPLATE.md) — шаблон плана перед реализацией
- [infra/RUNTIME_RUNBOOK.md](infra/RUNTIME_RUNBOOK.md) — простой runtime-сценарий установки, обновления и проверки

Что уже реализовано:
- В `apps/web` перенесены страницы `главная`, `возможности`, `цены`, `ресурсы`, `о нас`, `авторизация`, `личный кабинет`.
- Общие `header` и `footer` вынесены в layout-слой.
- Для мобильной версии добавлен общий burger-menu паттерн.
- Для frontend выделены общие слои `shared/layout`, `shared/ui`, `shared/styles`, `shared/auth`, `shared/config`.
- Страницы маршрутов в `src/app` работают как тонкие entry-point'ы, а основная UI-логика вынесена в `src/features`.
- Frontend `/api/*` route handlers проксируют auth/profile/devices/subscription/support запросы в локальный Django backend.
- Backend уже отдает рабочие API для регистрации, входа, профиля, устройств, подписки и health-check.
- Backend кабинета теперь отдает историю платежей, историю продлений, состояние `pending_payment` и нормализованные статусы устройств.
- В backend также появился `Batch 2` foundation-слой: отдельные домены `servers`, `routing` и `access`, а кабинет теперь получает единый вычисляемый `access-state`.
- При регистрации новый пользователь автоматически получает trial-подписку на 3 дня с базовыми маршрутами, чтобы кабинет открывался сразу в рабочем состоянии.
- API подписки теперь отдает явные состояния `none / trial / active / expired / pending_payment`, чтобы кабинет корректно показывал empty-state, ожидающую оплату и сценарий истекшего доступа без `404`.
- Для подписок используется единый платежный сценарий через `Platega SBP`: `GET /api/subscription/plans/` отдает каталог тарифов, `POST /api/subscription/checkout/` создает платежную сессию, а webhook `POST /api/subscription/webhooks/platega/<secret>/` подтверждает оплату и активирует подписку.
- Platega webhook теперь проходит через единый post-payment path: confirmed-платеж создает те же subscription-history и notifications, что и ручной paid-flow, а canceled callback предсказуемо переводит pending-платеж в `canceled`.
- Для finance-оператора теперь также есть staff-only payment API: список последних платежей и явная ручная смена статуса `paid / canceled / failed`, чтобы операторский сценарий не зависел только от Django admin actions.
- Public subscription surface теперь не ограничивается raw feed: `GET /api/subscription/public/<token>/summary/` отдает также install-guides по платформам и route-level client links, а `/sub/[token]` показывает quick-start, установку Happ и отдельные действия по маршрутам.
- Для поддержки теперь используется единый backend-диалог: `GET /api/support/conversation/` отдает историю текущего обращения, а `POST /api/support/messages/` добавляет новое сообщение с вложениями.
- Для операторов теперь есть и отдельный support API workflow поверх того же домена: staff может получить очередь диалогов, явно назначить тикет, ответить и закрыть его без обходных действий через сырой admin state.
- Для Telegram linking теперь используется отдельный backend-контур: `GET/POST/DELETE /api/telegram/link/` управляет статусом привязки, deep-link токеном и отвязкой Telegram.
- Telegram runtime теперь уже не ограничен одним linking/support-addon: для привязанного пользователя bot понимает `/menu`, `/subscription`, `/devices`, `/plans`, `/buy <code>`, `/sync`, `/repair <device_id>`, `/support` и использует реальные backend-данные.
- В backend добавлен отдельный домен `notifications` с Telegram-first dispatch для событий оплаты, revoke устройств, ответов поддержки и привязки Telegram.
- Управляемые пользовательские маршруты больше не живут только как URL внутри подписки: они привязаны к отдельным сущностям `ConnectionRoute` и `Server`.
- Trial/activation подписки и revoke устройства теперь уже запускают отдельные provisioning operations, а `access-state` умеет отдавать короткую сводку по provisioning-проблемам.
- В кабинете теперь видны provisioning-проблемы, доступен ручной sync access, а для устройств появился явный repair-flow без смешивания этой логики с обычным revoke.
- `XUI`-adapter уже читает конфиг provisioning-профиля сервера, умеет создавать/обновлять/удалять VLESS-клиента и может падать с явными кодами ошибок `XUI_CONFIG_INCOMPLETE / XUI_LOGIN_FAILED / XUI_INBOUND_NOT_FOUND`, если интеграция настроена неверно.
- Provisioning больше не ограничен только operation log: для каждого `device + route` теперь хранится отдельный `ProvisionedDeviceAccess` со статусом, внешним client identity, inbound и connection metadata.
- Cabinet subscription API, public summary `/sub/[token]` и raw feed теперь уже умеют предпочитать реальные provisioned route credentials для распознанного устройства по IP; если binding еще не найден, surface мягко деградирует к старым fallback URL.
- `POST /api/subscription/public/<token>/touch/` больше не формальный `ok`: public flow теперь создает или обновляет текущее устройство, логирует это событие и запускает device-level provisioning repair по маршрутам подписки.
- Public page `/sub/[token]` теперь после загрузки делает browser-side `touch` и повторно запрашивает summary через Next BFF, чтобы backend видел реальный IP пользователя, а не только адрес server-side рендера.
- Runtime heartbeat для provisioning-ноды теперь тоже замкнут: adapters умеют active health check, backend сохраняет `ServerStatusSnapshot`, `/api/health/` отдает runtime summary, а ops может вручную прогнать `check_provisioning_servers`.
- После review-fix public device identity больше не держится только на IP: public flow использует persistent `device_key`, который идет через BFF/headers и помогает точнее матчить текущее устройство и его bindings.
- `POST /api/subscription/public/<token>/touch/` теперь отдает единый API error-contract и больше не смешивает произвольные DRF validation payload с доменными `error.code`.
- Для backend уже есть доменные API-тесты.
- Корневой каталог `tests` пока остается в состоянии заготовки: системный и e2e-слой еще не развернут, а рабочие backend-тесты пока живут внутри `apps/api/apps/*/test_*.py`.
- Для API введен единый error-contract вида `error.code / error.message / error.details`.
- Для замены `Amonora` уже оформлен отдельный `Phase 00` baseline: parity matrix, P0-блокеры и этапность миграции зафиксированы в `docs/PHASE_00_AMONORA_REPLACEMENT_PLAN.md`.
- Django admin показывает ФИО пользователя, связанный профиль, историю действий и жизненный статус устройств.
- В Django admin для подписок и платежей теперь доступны административные действия: выдать подписку, продлить срок, убрать подписку, отозвать устройства, вручную отметить платеж как оплаченный/отмененный/ошибочный.
- В Django admin для платежей теперь есть история оплат по пользователям и помесячная финансовая сводка по успешным платежам.
- В Django admin теперь есть собственная dark-dashboard главная страница `INFINDA`, но в текущем этапе она перестроена в операционный `Обзор`: KPI, очередь внимания, быстрые действия, последние ответы поддержки, последние платежи и контроль устройств.
- В Django admin теперь также есть собственная branded login-страница и workspace-навигация из 6 верхних зон: `Обзор`, `Support`, `Пользователи`, `Платежи`, `Подписки`, `Устройства`.
- В Django admin теперь настроены обе темы `dark/light` с единым brand-стилем, а переключатель темы доступен и на login-экране, и внутри самой админки.
- Dashboard админки теперь работает как внутренняя система управления: верхний уровень больше не занят `Telegram/Аудитом/Профилями`, а быстрые переходы и sidebar собраны вокруг реальных рабочих сценариев продукта `INFINDA`.
- Login-экран админки теперь включает loader, switch темы, показ/скрытие пароля и более аккуратный UX проверки данных перед входом.
- Левое меню админки переработано в более широкий collapsible sidebar: список приложений раскрывается по секциям, а сама боковая панель умеет плавно скрываться и запоминает состояние.

Переменные окружения для платежного контура backend:
- `PLATEGA_MERCHANT_ID`
- `PLATEGA_SECRET_KEY`
- `PLATEGA_BASE_URL`
- `PLATEGA_WEBHOOK_SECRET`
- `PLATEGA_RETURN_URL`
- `PLATEGA_FAILED_URL`

Переменные окружения для Telegram bot runtime backend:
- `TELEGRAM_MAIN_BOT_USERNAME`
- `TELEGRAM_MAIN_BOT_TOKEN`
- `TELEGRAM_BOT_API_BASE_URL`
- `TELEGRAM_BOT_POLL_TIMEOUT_SECONDS`
- `TELEGRAM_BOT_REQUEST_TIMEOUT_SECONDS`
- `TELEGRAM_BOT_RETRY_DELAY_SECONDS`
- `TELEGRAM_SUPPORT_NOTIFICATIONS_CHAT_ID`

Локальный env:
- backend `apps/api` автоматически читает корневой `.env`;
- в корневом `.env` должны лежать только переменные, нужные `INFINDA`;
- старые или сторонние env-файлы нужно хранить отдельно как reference, а не использовать их напрямую в корне проекта.
- проверенный локальный backend-сценарий: `cd apps/api && ./.venv/bin/python manage.py check && ./.venv/bin/python manage.py test apps tests.api`.
- runtime support bot запускается отдельно: `cd apps/api && ./.venv/bin/python manage.py run_telegram_bot`.
- если нужен alert в Telegram для команды поддержки, нужно указать `TELEGRAM_SUPPORT_NOTIFICATIONS_CHAT_ID` группы или служебного чата.
- при обновлении уже существующей серверной БД нужно идти только через миграции текущего репозитория: новые `routing/servers` сущности заполняются через migration backfill из текущих подписочных маршрутов.

CI:
- в репозитории уже есть базовый GitHub Actions workflow `.github/workflows/ci.yml`;
- он запускает backend `check` + `app-level` и `repo-level` тесты, а также frontend `lint/typecheck/build`.
- отдельный job `frontend-e2e` теперь также запускает Playwright-сценарии `cd apps/web && npm run test:e2e`.
- для frontend теперь также есть первый реальный Playwright e2e-сценарий `cd apps/web && npm run test:e2e`; он сам поднимает backend/frontend стек, применяет backend-миграции и гоняет сценарий на `next build + next start`.
- в `tests/api` теперь есть и repo-level сценарий для public subscription flow: `register -> /sub/[token] touch -> provisioned summary/feed -> cabinet/access sync`.

Принцип работы:
- Сначала планирование и уточнение.
- Затем согласование ключевых решений.
- После этого реализация небольшими понятными этапами.
- Постоянные правила процесса хранятся в `AGENTS.md`.
