# Web App

Frontend-приложение проекта `INFINDA` на `Next.js`.

## Команды

- `npm install`
- `npm run dev`
- `npm run lint`
- `npm run typecheck`
- `npm run build`

## Env

- для standalone-локального запуска frontend использует `apps/web/.env.example`;
- базовая переменная: `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/`;
- внутри docker-compose foundation-стека backend URL переопределяется на внутренний host `api`.

## Структура

- `src/app` — маршруты и layout.
- `src/features` — функциональные модули.
- `src/shared` — общие конфиги, auth-слой, layout, ui и переиспользуемые сущности.

## Текущее состояние

- Маршруты в `src/app` используются как тонкие entry-point'ы.
- Основная UI-логика страниц вынесена в `src/features`.
- Перенесены страницы `главная`, `возможности`, `цены`, `ресурсы`, `о нас`, `авторизация`, `личный кабинет`, а также отдельные страницы ошибок.
- `header` и `footer` вынесены в общий layout-слой для повторного использования.
- Для мобильной навигации используется общий burger-menu паттерн.
- Реальный backend уже подключен через Next route handlers в `src/app/api`.
- Auth и часть cabinet-сценариев уже работают через локальный `Django + DRF` backend.
- Cabinet уже использует backend-данные по устройствам и подписке: история оплат, история продлений, `pending_payment`, единый `access-state` и revoke-flow с причиной.
- Transport DTO и endpoint-paths для `auth/profile/devices/subscription/support/telegram/access` подключены из `packages/shared`.
- Для этапа `public access` добавлена первая публичная surface-страница `/sub/[token]`, которая показывает summary подписки без входа в кабинет.
- Для публичной подписки также добавлены `/sub/[token]/feed` и `/happ/add?sub=...` как базовый foundation для client-flow.

## Ограничения текущего этапа

- Frontend зависит от локально поднятого backend `apps/api` и его BFF-прокси в `src/app/api`.
- Backend-платежный контур уже реализован, но пользовательские post-payment сценарии и UX оплаты еще требуют дальнейшей доработки.
- Пользовательский inbox для notification-домена пока не вынесен в отдельную вкладку кабинета: backend-события уже есть, frontend-список уведомлений еще не сделан.
- Frontend-тесты в приложении пока не развернуты.
