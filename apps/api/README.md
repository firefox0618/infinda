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
- `apps/api` автоматически читает корневой файл `/home/dextrmed/Project/infinda/.env`;
- в нем должны быть только актуальные переменные `INFINDA`, включая `PLATEGA_*` и `TELEGRAM_*`.
- проверенный локальный сценарий использует интерпретатор `apps/api/.venv/bin/python`.

## Команды

- `./.venv/bin/python manage.py check`
- `./.venv/bin/python manage.py migrate`
- `./.venv/bin/python manage.py runserver`
- `./.venv/bin/python manage.py test apps tests.api`
- `./.venv/bin/python manage.py run_telegram_bot`

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
- `GET /api/access/`
- `GET /api/subscription/`
- `GET /api/subscription/plans/`
- `POST /api/subscription/checkout/`
- `POST /api/subscription/webhooks/platega/<secret>/`
- `GET /api/support/conversation/`
- `POST /api/support/messages/`
- `GET /api/telegram/link/`
- `POST /api/telegram/link/`
- `POST /api/telegram/link/confirm/`
- `DELETE /api/telegram/link/`

## Текущее состояние

- Приложение организовано по доменным Django-apps.
- Реализованы модули `auth`, `profile`, `devices`, `subscription`, `support`, `telegram`, `notifications`, `servers`, `routing`, `access`, `health`, `activity`.
- Для Telegram добавлен отдельный runtime через Django management command `run_telegram_bot`: он подтверждает deep-link привязки и создает inbound support-сообщения через уже существующие доменные сервисы.
- `GET /api/devices/` теперь отдает вычисляемые device-state поля `display_name / platform / client / is_current / computed_status / revoked_reason`.
- `GET /api/access/` отдает единый вычисляемый access-state пользователя: `active / expired / pending_payment / device_limit_exceeded / restricted / server_unavailable`.
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
- Telegram bot runtime в текущем этапе работает через long polling; текстовые ответы администратора в Telegram уже поддерживаются, но webhook и пересылка admin-вложений в Telegram пока не добавлены.
- Ответы администратора в Telegram сейчас поддерживают только текст; пересылка admin-вложений в Telegram пока не добавлена.
- Продакшн-настройки и внешние интеграции будут добавляться отдельными этапами.
- Локальные demo-данные могут использоваться для ручной проверки, но конкретные учетные данные не фиксируются в документации проекта.
- Общие TypeScript transport-контракты хранятся в `packages/shared`; backend пока выровнен с ними через serializer-формы и тесты, а не через прямой импорт.
