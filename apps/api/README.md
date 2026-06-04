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

## Структура

- `config` — настройки и корневые urls.
- `apps` — Django-приложения по доменам.

## Ограничения текущего этапа

- Реальная доменная модель еще не создана.
- Подключен только базовый `health` endpoint.
- Продакшн-настройки и интеграции будут добавляться отдельными этапами.
