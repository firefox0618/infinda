# Runtime Runbook

Простой runbook для этапа `runtime foundation`.

Задача документа:
- быстро поднять `INFINDA` на сервере;
- уметь обновить код без хаоса;
- уметь быстро проверить, что `api`, `web` и `telegram bot` живы.

## 1. Что должно быть на сервере

Минимально:
- `python3`
- `python3-venv`
- `nodejs`
- `npm`
- `postgresql`
- `nginx`
- `systemd`

## 2. Первая установка

### 2.1. Подготовить env

```bash
cd /opt/infinda
cp infra/env/infinda.app.env.example infra/env/infinda.app.env
```

После этого заполнить реальные значения:
- `DJANGO_SECRET_KEY`
- `POSTGRES_*`
- `PLATEGA_*`
- `TELEGRAM_*`
- `DJANGO_ALLOWED_HOSTS`

### 2.2. Подготовить backend

```bash
cd /opt/infinda/apps/api
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py check
```

### 2.3. Подготовить frontend

```bash
cd /opt/infinda/apps/web
npm ci
npm run build
```

### 2.4. Установить сервисы

Скопировать шаблоны:
- `infra/systemd/infinda-api.service`
- `infra/systemd/infinda-web.service`
- `infra/systemd/infinda-telegram-bot.service`

в:

```bash
/etc/systemd/system/
```

Потом:

```bash
sudo systemctl daemon-reload
sudo systemctl enable infinda-api.service
sudo systemctl enable infinda-web.service
sudo systemctl enable infinda-telegram-bot.service
sudo systemctl start infinda-api.service
sudo systemctl start infinda-web.service
sudo systemctl start infinda-telegram-bot.service
```

### 2.5. Установить nginx

Скопировать:

```bash
infra/nginx/infinda.conf.example
```

в конфиг сайта `nginx`, потом:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 3. Обновление проекта

Когда код уже стоит на сервере:

### 3.1. Обновить backend

```bash
cd /opt/infinda/apps/api
. .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py check
sudo systemctl restart infinda-api.service
sudo systemctl restart infinda-telegram-bot.service
```

### 3.2. Обновить frontend

```bash
cd /opt/infinda/apps/web
npm ci
npm run build
sudo systemctl restart infinda-web.service
```

## 4. Быстрая проверка после запуска

Самый простой вариант:

```bash
bash /opt/infinda/infra/scripts/smoke_check.sh
```

Если нужны нестандартные адреса:

```bash
API_URL=http://127.0.0.1:8000/api/health/ \
WEB_URL=http://127.0.0.1:3000/api/health \
bash /opt/infinda/infra/scripts/smoke_check.sh
```

### 4.1. Проверка API

```bash
curl -sf http://127.0.0.1:8000/api/health/
```

Ожидается:

```json
{"status":"ok","service":"api"}
```

### 4.2. Проверка web

```bash
curl -sf http://127.0.0.1:3000/api/health
```

Ожидается:

```json
{"status":"ok","service":"web"}
```

### 4.3. Проверка systemd

```bash
systemctl status infinda-api.service
systemctl status infinda-web.service
systemctl status infinda-telegram-bot.service
```

### 4.4. Проверка nginx

```bash
sudo nginx -t
```

## 5. Если что-то не поднялось

### API

```bash
journalctl -u infinda-api.service -n 100 --no-pager
```

### Web

```bash
journalctl -u infinda-web.service -n 100 --no-pager
```

### Telegram bot

```bash
journalctl -u infinda-telegram-bot.service -n 100 --no-pager
```

## 6. Что это дает

- есть единый понятный сценарий установки;
- есть единый понятный сценарий обновления;
- есть простой smoke-check после запуска;
- следующий этап можно делать уже как развитие рабочего runtime, а не просто кода в репозитории.
