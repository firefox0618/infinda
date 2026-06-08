# API Tests

Каталог `tests/api` предназначен для интеграционных проверок уровня репозитория.

Сюда должны попадать тесты, которые:
- затрагивают несколько backend-доменов сразу;
- проверяют общий пользовательский сценарий, а не только одно Django app;
- неудобно держать внутри `apps/api/apps/*/test_*.py`.

Примеры будущих сценариев:
- `register -> trial subscription -> cabinet bootstrap`;
- `telegram link -> support message -> admin reply`;
- `subscription checkout -> webhook -> active subscription`.

Текущие реальные сценарии:
- `test_cabinet_bootstrap.py` — проверяет цепочку `register -> login -> auth/profile/devices/subscription/support/telegram`.
- `test_telegram_support_flow.py` — проверяет цепочку `telegram link -> support message -> admin reply -> close conversation`.
- `test_subscription_checkout_flow.py` — проверяет цепочку `checkout -> webhook -> activation`.
- `test_public_subscription_flow.py` — проверяет цепочку `register -> public /sub token -> touch -> provisioned summary/feed -> cabinet/access sync`.
