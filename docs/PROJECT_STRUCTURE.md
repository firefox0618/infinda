# PROJECT STRUCTURE

Цель:
- Подготовить проект к поэтапной разработке из HTML-макетов в полноценное приложение.

Принятая базовая структура:

```text
infinda/
├─ apps/
│  ├─ web/
│  └─ api/
├─ packages/
│  └─ shared/
├─ tests/
├─ infra/
├─ docs/
├─ шаблоны и работа/
└─ README.md
```

Назначение каталогов:
- `apps/web` — клиентское приложение на `Next.js`, в которое поэтапно переносятся HTML-макеты.
- `apps/api` — серверное приложение на `Django + DRF`, API, авторизация, подписки, платежи, интеграции.
- `packages/shared` — общие контракты, типы, схемы, константы, переиспользуемая логика.
- `tests` — каталог под интеграционные, e2e и другие общие тесты уровня системы.
- `infra` — заготовка под окружения, reverse proxy, контейнеризацию, CI/CD и конфиги инфраструктуры.
- `docs` — документация, правила, память проекта, поэтапные планы.
- `шаблоны и работа` — визуальный эталон, исходные HTML-макеты и связанные материалы.

Что пока остается в корне:
- Базовые репозиторные файлы.

Текущее состояние:
- Стек выбран и зафиксирован.
- Каркас `apps/web` и `apps/api` инициализирован.
- В `apps/web` уже перенесены основные страницы лендинга, auth, cabinet и страницы ошибок.
- Для frontend уже выделены общие слои `shared/layout`, `shared/ui`, `shared/styles`, `shared/auth`, `shared/config`.
- В `apps/web/src/app` маршруты остаются тонкими, а основная реализация вынесена в `apps/web/src/features`.
- В `apps/web` уже есть собственные `/api/*` route handlers как BFF/proxy-слой перед Django API.
- В `apps/api` уже реализованы доменные приложения `auth`, `profile`, `devices`, `subscription`, `support`, `telegram`, `notifications`, `servers`, `routing`, `access`, `activity`, `health`.
- `packages/shared` уже содержит общий слой transport-контрактов и API error-format.
- `packages/shared` уже расширен контрактами для `auth/profile/devices/subscription/support/telegram/access`.
- В `apps/api` уже есть app-level тесты по доменам, а в корневом `tests/` уже оформлены слои `tests/api` и `tests/web` под будущие интеграционные и e2e-сценарии.
- `infra` пока остается пустым слотом под последующие инфраструктурные этапы.
- В репозитории уже добавлен базовый GitHub Actions CI для backend и frontend проверок.
