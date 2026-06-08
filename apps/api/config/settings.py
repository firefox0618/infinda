import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent.parent


def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue

        os.environ[key] = value.strip()


load_env_file(PROJECT_ROOT / ".env")


def env_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default

    return int(raw_value.strip())

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "change-me-for-local-development")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "DJANGO_ALLOWED_HOSTS",
        "127.0.0.1,localhost,testserver",
    ).split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "apps.activity.apps.ActivityConfig",
    "apps.auth.apps.AuthConfig",
    "apps.profile.apps.ProfileConfig",
    "apps.devices.apps.DevicesConfig",
    "apps.servers.apps.ServersConfig",
    "apps.routing.apps.RoutingConfig",
    "apps.provisioning.apps.ProvisioningConfig",
    "apps.access.apps.AccessConfig",
    "apps.notifications.apps.NotificationsConfig",
    "apps.subscription.apps.SubscriptionConfig",
    "apps.support.apps.SupportConfig",
    "apps.telegram.apps.TelegramConfig",
    "apps.legacy_sync.apps.LegacySyncConfig",
    "apps.health.apps.HealthConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASE_ENGINE = os.getenv("DJANGO_DB_ENGINE", "sqlite").strip().lower()

if DATABASE_ENGINE in {"postgres", "postgresql"}:
    database_config = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "infinda"),
        "USER": os.getenv("POSTGRES_USER", "infinda"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "infinda"),
        "HOST": os.getenv("POSTGRES_HOST", "127.0.0.1"),
        "PORT": env_int("POSTGRES_PORT", 5432),
        "CONN_MAX_AGE": env_int("POSTGRES_CONN_MAX_AGE", 60),
    }

    connect_timeout = env_int("POSTGRES_CONNECT_TIMEOUT", 5)
    ssl_mode = os.getenv("POSTGRES_SSLMODE", "").strip()
    options: dict[str, object] = {"connect_timeout": connect_timeout}
    if ssl_mode:
        options["sslmode"] = ssl_mode

    database_config["OPTIONS"] = options
    DATABASES = {"default": database_config}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Asia/Yekaterinburg"

USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "EXCEPTION_HANDLER": "config.api_errors.api_exception_handler",
}

PLATEGA_MERCHANT_ID = os.getenv("PLATEGA_MERCHANT_ID", "")
PLATEGA_SECRET_KEY = os.getenv("PLATEGA_SECRET_KEY", "")
PLATEGA_BASE_URL = os.getenv("PLATEGA_BASE_URL", "https://api.platega.io")
PLATEGA_WEBHOOK_SECRET = os.getenv("PLATEGA_WEBHOOK_SECRET", "")
PUBLIC_WEB_BASE_URL = os.getenv("PUBLIC_WEB_BASE_URL", "http://localhost:3000")
PUBLIC_HAPP_PROFILE_NAME = os.getenv("PUBLIC_HAPP_PROFILE_NAME", "INFINDA")
PLATEGA_RETURN_URL = os.getenv("PLATEGA_RETURN_URL", "http://localhost:3000/cabinet")
PLATEGA_FAILED_URL = os.getenv("PLATEGA_FAILED_URL", "http://localhost:3000/prices")
TELEGRAM_MAIN_BOT_USERNAME = os.getenv("TELEGRAM_MAIN_BOT_USERNAME", "infinda_bot")
TELEGRAM_MAIN_BOT_TOKEN = os.getenv("TELEGRAM_MAIN_BOT_TOKEN", "")
TELEGRAM_BOT_API_BASE_URL = os.getenv("TELEGRAM_BOT_API_BASE_URL", "https://api.telegram.org")
TELEGRAM_BOT_POLL_TIMEOUT_SECONDS = int(os.getenv("TELEGRAM_BOT_POLL_TIMEOUT_SECONDS", "30"))
TELEGRAM_BOT_REQUEST_TIMEOUT_SECONDS = float(
    os.getenv("TELEGRAM_BOT_REQUEST_TIMEOUT_SECONDS", "35"),
)
TELEGRAM_BOT_RETRY_DELAY_SECONDS = int(os.getenv("TELEGRAM_BOT_RETRY_DELAY_SECONDS", "5"))
TELEGRAM_SUPPORT_NOTIFICATIONS_CHAT_ID = os.getenv("TELEGRAM_SUPPORT_NOTIFICATIONS_CHAT_ID", "")
PROVISIONING_XUI_DEFAULT_USERNAME = os.getenv("PROVISIONING_XUI_DEFAULT_USERNAME", "")
PROVISIONING_XUI_DEFAULT_PASSWORD = os.getenv("PROVISIONING_XUI_DEFAULT_PASSWORD", "")
PROVISIONING_XUI_VERIFY_TLS = env_bool("PROVISIONING_XUI_VERIFY_TLS", True)
PROVISIONING_XUI_REQUEST_TIMEOUT_SECONDS = env_int("PROVISIONING_XUI_REQUEST_TIMEOUT_SECONDS", 15)
