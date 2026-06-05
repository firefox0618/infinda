# Web App

Frontend-приложение проекта `INFINDA` на `Next.js`.

## Команды

- `npm install`
- `npm run dev`
- `npm run lint`
- `npm run typecheck`
- `npm run build`

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
- Transport DTO и endpoint-paths для `auth/profile/devices/subscription` подключены из `packages/shared`.

## Ограничения текущего этапа

- Внешние продуктовые интеграции и платежный контур еще не реализованы.
- Часть системных маршрутов кабинета пока остается UI-first и требует дальнейшей backend-стыковки.
- Frontend-тесты в приложении пока не развернуты.
