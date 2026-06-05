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
- `POST /api/auth/logout/`
- `GET /api/auth/me/`
- `GET /api/profile/me/`
- `PATCH /api/profile/me/`
- `GET /api/devices/`
- `POST /api/devices/<id>/revoke/`
- `GET /api/subscription/`

### Локальный demo-пользователь

Для локальной ручной проверки уже подготовлен пользователь:

- `email / username`: `rudolfnaumow@gmail.com`
- `password`: `13bozotA)`

Для `Django admin` используются те же данные:

- `http://127.0.0.1:8000/admin`

Также локально уже подготовлены demo-данные:

- профиль `Rudolf Naumow`
- `Telegram`: `@rudolfnaumow`
- 3 устройства
- активная demo-подписка на `12 месяцев`
- 4 demo-маршрута по странам

## Структура

- `config` — настройки и корневые urls.
- `apps` — Django-приложения по доменам.

## Ограничения текущего этапа

- `auth`, `profile`, `devices`, `subscription` уже работают локально.
- `support` и реальное `продление / оплата` пока не подключены к backend.
- Продакшн-настройки и внешние интеграции будут добавляться отдельными этапами.
