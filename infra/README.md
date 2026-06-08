# Infra

Каталог `infra/` зарезервирован под инфраструктурные материалы проекта.

Текущее состояние этапа `runtime foundation`:
- добавлен локальный docker-compose стек `docker-compose.local.yml`;
- добавлены отдельные Dockerfile для `api` и `web`;
- локальный стек поднимает `postgres`, `api`, `web` и `telegram-bot`.
- добавлены первые production-like шаблоны для env, `systemd` и `nginx`.

## Локальный запуск

1. Скопировать пример env:

```bash
cp apps/api/.env.example .env
```

2. Поднять стек:

```bash
docker compose -f infra/docker-compose.local.yml up --build
```

3. Точки входа:
- web: `http://localhost:3000`
- api: `http://localhost:8000/api/health/`
- postgres: `localhost:5432`

## Содержимое каталога

- `docker-compose.local.yml` — локальный runtime-стек.
- `docker/api.Dockerfile` — образ backend/runtime для `Django` и Telegram bot command.
- `docker/web.Dockerfile` — образ frontend `Next.js`.
- `env/infinda.app.env.example` — единый пример env для серверного запуска.
- `systemd/infinda-api.service` — шаблон запуска `Django API`.
- `systemd/infinda-web.service` — шаблон запуска `Next.js web`.
- `systemd/infinda-telegram-bot.service` — шаблон запуска Telegram runtime.
- `nginx/infinda.conf.example` — пример reverse proxy конфига.
- `RUNTIME_RUNBOOK.md` — простая инструкция установки, обновления и проверки.
- `scripts/smoke_check.sh` — быстрая базовая проверка `api` и `web`.

## Простой серверный сценарий

1. Скопировать env-шаблон:

```bash
cp infra/env/infinda.app.env.example infra/env/infinda.app.env
```

2. Установить и подготовить backend:

```bash
cd /opt/infinda/apps/api
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
```

3. Подготовить frontend:

```bash
cd /opt/infinda/apps/web
npm ci
npm run build
```

4. Установить `systemd`-юниты и `nginx`-конфиг как основу серверного запуска.

Что это дает:
- у проекта появляется понятный шаблон запуска на сервере;
- становится ясно, где живут env, сервисы и reverse proxy;
- появляется отдельная простая инструкция, как ставить, обновлять и проверять проект;
- следующий этап можно делать уже поверх более реального runtime.

## Следующее планируемое наполнение

- reverse proxy;
- production/stage env templates;
- process management и deployment artifacts;
- backup/restore runbooks;
- инфраструктурные health-check и watchdog сценарии.
