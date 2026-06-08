# API App

Backend-приложение проекта `INFINDA` на `Django + DRF`.

## Подготовка окружения

```bash
cd apps/api
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py check
python manage.py test apps tests.api
python manage.py runserver
```

Для локального запуска:
- `apps/api` автоматически читает корневой файл `/opt/infinda/.env`;
- в нем должны быть только актуальные переменные `INFINDA`, включая `DJANGO_DB_ENGINE`, `POSTGRES_*`, `PLATEGA_*` и `TELEGRAM_*`;
- проверенный локальный сценарий использует интерпретатор `apps/api/.venv/bin/python`.
- для нового foundation-стека базовый сценарий локального окружения теперь идет через `PostgreSQL`, а `sqlite` остается только как fallback для простых локальных и CI-сценариев без отдельной БД.

Быстрый старт foundation-окружения:

```bash
cp apps/api/.env.example .env
docker compose -f infra/docker-compose.local.yml up --build
```

## Команды

- `./.venv/bin/python manage.py check`
- `./.venv/bin/python manage.py migrate`
- `./.venv/bin/python manage.py runserver`
- `./.venv/bin/python manage.py test apps tests.api`
- `./.venv/bin/python manage.py run_telegram_bot`
- `./.venv/bin/python manage.py check_provisioning_servers`
- `./.venv/bin/python manage.py inspect_amonora_restore --database-name infinda_amonora_restore`
- `./.venv/bin/python manage.py inspect_amonora_restore --database-name infinda_amonora_restore --compare-current`
- `./.venv/bin/python manage.py inspect_amonora_restore --database-name infinda_amonora_restore --user-stats`
- `./.venv/bin/python manage.py inspect_amonora_restore --database-name infinda_amonora_restore --subscription-stats`
- `./.venv/bin/python manage.py inspect_amonora_restore --database-name infinda_amonora_restore --support-stats`
- `./.venv/bin/python manage.py inspect_amonora_restore --database-name infinda_amonora_restore --device-stats`
- `./.venv/bin/python manage.py inspect_amonora_restore --database-name infinda_amonora_restore --payment-stats`
- `./.venv/bin/python manage.py import_amonora_users --database-name infinda_amonora_restore`
- `./.venv/bin/python manage.py import_amonora_users --database-name infinda_amonora_restore --dry-run`
- `./.venv/bin/python manage.py import_amonora_users --database-name infinda_amonora_restore --limit 10`
- `./.venv/bin/python manage.py import_amonora_subscriptions --database-name infinda_amonora_restore`
- `./.venv/bin/python manage.py import_amonora_subscriptions --database-name infinda_amonora_restore --dry-run`
- `./.venv/bin/python manage.py import_amonora_subscriptions --database-name infinda_amonora_restore --limit 10`
- `./.venv/bin/python manage.py import_amonora_payments --database-name infinda_amonora_restore`
- `./.venv/bin/python manage.py import_amonora_payments --database-name infinda_amonora_restore --dry-run`
- `./.venv/bin/python manage.py import_amonora_payments --database-name infinda_amonora_restore --limit 10`
- `./.venv/bin/python manage.py import_amonora_support --database-name infinda_amonora_restore`
- `./.venv/bin/python manage.py import_amonora_support --database-name infinda_amonora_restore --dry-run`
- `./.venv/bin/python manage.py import_amonora_support --database-name infinda_amonora_restore --limit 10`

## Текущие API endpoints

- `GET /api/health/`
- `POST /api/auth/login/`
- `POST /api/auth/register/`
- `POST /api/auth/logout/`
- `GET /api/auth/me/`
- `GET /api/profile/me/`
- `PATCH /api/profile/me/`
- `GET /api/devices/`
- `POST /api/devices/<id>/revoke/`
- `POST /api/devices/<id>/repair/`
- `GET /api/access/`
- `POST /api/access/sync/`
- `GET /api/subscription/`
- `GET /api/subscription/plans/`
- `POST /api/subscription/checkout/`
- `POST /api/subscription/webhooks/platega/<secret>/`
- `GET /api/subscription/public/<token>/feed/`
- `GET /api/subscription/public/<token>/summary/`
- `POST /api/subscription/public/<token>/touch/`
- `GET /api/support/conversation/`
- `POST /api/support/messages/`
- `GET /api/telegram/link/`
- `POST /api/telegram/link/`
- `POST /api/telegram/link/confirm/`
- `DELETE /api/telegram/link/`

## Legacy migration tools

- `inspect_amonora_restore` — проверка восстановленной копии Amonora в локальном PostgreSQL перед дальнейшим переносом данных в `INFINDA`.
- `inspect_amonora_restore --compare-current` — сравнение счетчиков Amonora restore и текущего `INFINDA`.
- `inspect_amonora_restore --user-stats` — простая сводка по пользователям старой БД.
- `inspect_amonora_restore --subscription-stats` — простая сводка по subscription state в старой БД.
- `inspect_amonora_restore --support-stats` — простая сводка по support tickets/messages в старой БД.
- `inspect_amonora_restore --device-stats` — простая сводка по vpn_clients и device-related tables в старой БД.
- `inspect_amonora_restore --payment-stats` — простая сводка по payment_records в старой БД.
- `import_amonora_users` — первый реальный перенос из Amonora в INFINDA: технические аккаунты пользователей, их Telegram-привязки и профили; если локальный `telegram_user_id` уже занят, команда переиспользует существующую привязку вместо падения.
- `import_amonora_subscriptions` — второй шаг переноса: текущий статус доступа и подписки для импортированных пользователей.
- `import_amonora_payments` — третий шаг переноса: история подписочных платежей из legacy, без неподдерживаемых топапов и доп.сервисов.
- `import_amonora_support` — четвертый шаг переноса: тикеты, сообщения, вложения и состояние support-диалогов.
- `import_amonora_devices` — пятый шаг переноса: legacy `vpn_clients` в `Device`, где `client_uuid` хранится как внутренний ключ, а в интерфейсе показывается имя устройства из `client_data`.
- `import_amonora_device_slot_entitlements` — шестой шаг переноса: legacy доп.слоты устройств в `UserActivity` и `Subscription.max_devices` для активных entitlements.
- `import_amonora_vpn_repair_events` — седьмой шаг переноса: legacy repair-events в `UserActivity` с сохранением результата и причины.

## Текущее состояние

- Приложение организовано по доменным Django-apps.
- Реализованы модули `auth`, `profile`, `devices`, `subscription`, `support`, `telegram`, `notifications`, `servers`, `routing`, `provisioning`, `access`, `health`, `activity`.
- Runtime foundation теперь умеет работать и с `PostgreSQL`, и с fallback `sqlite`; выбор backend-БД задается через `DJANGO_DB_ENGINE`.
- Для этапа `public access` у подписки теперь есть отдельный безопасный `public_token`, а backend умеет отдавать публичную summary-модель по `GET /api/subscription/public/<token>/summary/`.
- Для Telegram добавлен отдельный runtime через Django management command `run_telegram_bot`: он подтверждает deep-link привязки и создает inbound support-сообщения через уже существующие доменные сервисы.
- `GET /api/devices/` теперь отдает вычисляемые device-state поля `display_name / platform / client / is_current / computed_status / revoked_reason`.
- `GET /api/access/` отдает единый вычисляемый access-state пользователя: `active / expired / pending_payment / device_limit_exceeded / restricted / server_unavailable`.
- В backend теперь есть отдельный foundation-домен `provisioning`: профили серверов и журнал операций `sync/revoke/repair`, чтобы device/subscription lifecycle не был скрытой логикой без трассировки.
- Trial/activation подписки и `POST /api/devices/<id>/revoke/` теперь создают provisioning-операции по связанным маршрутам; `GET /api/access/` дополнительно отдает `provisioning_issue_count` и `last_provisioning_error_codes`.
- Для device/access lifecycle теперь также есть ручные product-level действия: `POST /api/devices/<id>/repair/` запускает repair-операции по маршрутам устройства, а `POST /api/access/sync/` запускает ручную синхронизацию доступа по активной подписке.
- Provisioning adapter layer теперь поддерживает режимы `mock / manual / xui`; для `xui` профиль сервера хранит URL панели, логин, пароль, inbound id, TLS и timeout, а операция уже умеет не только валидировать login/inbound через `httpx`, но и создавать, обновлять и удалять VLESS-клиента.
- В provisioning-домене теперь также есть materialized модель `ProvisionedDeviceAccess`: `sync/repair/revoke` больше не ограничиваются журналом операций, а сохраняют фактическое состояние binding между `Device` и `ConnectionRoute`.
- `GET /api/subscription/`, `GET /api/subscription/public/<token>/summary/` и `GET /api/subscription/public/<token>/feed/` теперь учитывают `ProvisionedDeviceAccess` для устройства, распознанного по `request_ip`: route-level ссылки и feed предпочитают реальные provisioned credentials, а при их отсутствии возвращают fallback-маршруты.
- `POST /api/subscription/public/<token>/touch/` теперь принимает базовый device-context (`device_name / platform / client / icon`), создает или обновляет текущее устройство по IP и запускает repair-операции provisioning по маршрутам активной подписки.
- Public device binding теперь использует не только `request_ip`, но и `X-Device-Key`: это позволяет матчить устройство стабильнее, чем по одному IP, и отдавать правильные provisioned bindings в summary/feed.
- `GET /api/health/` теперь также отдает runtime summary по серверам, а provisioning adapter layer умеет активную health-check проверку ноды через `mock / manual / xui`.
- Команда `check_provisioning_servers` позволяет руками или по cron прогнать active health check по enabled provisioning profiles и обновить `Server.status`, `last_heartbeat` и `ServerStatusSnapshot`.
- `GET /api/subscription/` теперь также отдает историю платежей, историю подписки и состояние `pending_payment`.
- `SubscriptionRoute` теперь привязывается к управляемому `ConnectionRoute`, а серверный и маршрутизирующий слои живут в отдельных доменах.
- Support-диалоги теперь работают как единый тикетный поток: новый тикет можно принять в работу в Django admin, ответы администратора остаются в web-истории, а для Telegram-диалогов автоматически уходят обратно пользователю через бота.
- При новом или переоткрытом тикете backend может отправлять уведомление в операторский Telegram-чат через `TELEGRAM_SUPPORT_NOTIFICATIONS_CHAT_ID`.
- Для основных API уже есть тесты на уровне доменных приложений.
- Frontend `apps/web` ходит в backend не напрямую из браузера, а через собственные Next route handlers.
- Для API настроен единый error-contract: `error.code`, `error.message`, `error.details`.
- В Django admin добавлен audit-слой: у пользователя видны профиль, ФИО и журнал действий; устройства имеют явный статус `Активно/Отозвано`.
- В Django admin доступны ручные административные операции по пользователям, подпискам, устройствам и платежам: выдача подписки, продление, снятие подписки, отзыв устройств, ручная обработка статусов платежа.
- В разделе платежей админки показывается история оплат и помесячная финансовая сводка по успешным платежам.
- Главная страница Django admin оформлена как отдельный dark dashboard под `INFINDA`: сводные карточки, финансовая динамика, последние платежи и журнал последних действий.
- Страница входа в Django admin и список разделов админки также оформлены в едином dark-стиле `INFINDA`: быстрые переходы по ключевым сущностям и более удобная навигация по административным разделам.
- Для админки настроены две рабочие темы `dark/light`; переключатель темы доступен и на login-странице, и в шапке административной панели.
- Dashboard админки теперь дополнен рабочими управленческими блоками: проблемные платежи, скоро истекающие подписки и контроль устройств.
- Login-экран админки теперь имеет собственный loader, switch темы, показ/скрытие пароля и более аккуратную клиентскую проверку перед отправкой формы.
- Левый sidebar админки теперь расширен и переработан в раскрывающийся список приложений; его состояние скрытия сохраняется локально и применяется при следующем открытии панели.
- Регистрация пользователя теперь работает через backend endpoint `POST /api/auth/register/`.
- Backend-платежный контур `subscription/plans + subscription/checkout + platega webhook` реализован и проходит доменные API-тесты.
- Для обновления старой боевой БД на новую схему нужно использовать обычный миграционный путь Django: новые таблицы `servers/routing` создаются миграциями, а текущие подписочные маршруты автоматически backfill-ятся в управляемые route-сущности.

## Структура

- `config` — настройки и корневые urls.
- `apps` — Django-приложения по доменам.

## Ограничения текущего этапа

- `auth`, `profile`, `devices`, `subscription`, `support`, `telegram`, `notifications` уже работают локально.
- Локальный docker-compose стек пока предназначен для foundation-разработки и не заменяет production deployment.
- Telegram bot runtime в текущем этапе работает через long polling; текстовые ответы администратора в Telegram уже поддерживаются, но webhook и пересылка admin-вложений в Telegram пока не добавлены.
- Ответы администратора в Telegram сейчас поддерживают только текст; пересылка admin-вложений в Telegram пока не добавлена.
- Продакшн-настройки и внешние интеграции будут добавляться отдельными этапами.
- Локальные demo-данные могут использоваться для ручной проверки, но конкретные учетные данные не фиксируются в документации проекта.
- Общие TypeScript transport-контракты хранятся в `packages/shared`; backend пока выровнен с ними через serializer-формы и тесты, а не через прямой импорт.
