# API App

Backend-приложение проекта `INFINDA` на `Django + DRF`.

## Подготовка окружения

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Команды

- `python manage.py check`
- `python manage.py migrate`
- `python manage.py runserver`
- `python manage.py test`

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
- `GET /api/subscription/`

## Текущее состояние

- Приложение организовано по доменным Django-apps.
- Реализованы модули `auth`, `profile`, `devices`, `subscription`, `health`, `activity`.
- Для основных API уже есть тесты на уровне доменных приложений.
- Frontend `apps/web` ходит в backend не напрямую из браузера, а через собственные Next route handlers.
- Для API настроен единый error-contract: `error.code`, `error.message`, `error.details`.
- В Django admin добавлен audit-слой: у пользователя видны профиль, ФИО и журнал действий; устройства имеют явный статус `Активно/Отозвано`.
- Регистрация пользователя теперь работает через backend endpoint `POST /api/auth/register/`.

## Структура

- `config` — настройки и корневые urls.
- `apps` — Django-приложения по доменам.

## Ограничения текущего этапа

- `auth`, `profile`, `devices`, `subscription` уже работают локально.
- `support` и реальное `продление / оплата` пока не подключены к backend.
- Продакшн-настройки и внешние интеграции будут добавляться отдельными этапами.
- Локальные demo-данные могут использоваться для ручной проверки, но конкретные учетные данные не фиксируются в документации проекта.
- Общие TypeScript transport-контракты хранятся в `packages/shared`; backend пока выровнен с ними через serializer-формы и тесты, а не через прямой импорт.
