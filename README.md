# INFINDA

Проект находится на этапе перехода от HTML-макетов к полноценному приложению.

Текущее состояние:
- Визуальные HTML-макеты находятся в каталоге `шаблоны и работа/` и являются эталоном внешнего вида.
- Инициализированы `apps/web` на `Next.js` и `apps/api` на `Django + DRF`.
- Текущий этап: доработка и полировка первой продуктовой страницы `главная` в `apps/web`, плюс подготовка общих frontend-шаблонов.

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
- В `apps/web` перенесена и дорабатывается страница `главная`.
- Общие `header` и `footer` вынесены в layout-слой.
- Для мобильной версии добавлен общий burger-menu паттерн.
- Для frontend выделены общие слои `shared/layout`, `shared/ui`, `shared/styles`.

Принцип работы:
- Сначала планирование и уточнение.
- Затем согласование ключевых решений.
- После этого реализация небольшими понятными этапами.
- Постоянные правила процесса хранятся в `AGENTS.md`.
