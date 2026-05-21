import os
import warnings
from datetime import timedelta
from pathlib import Path

from decouple import Csv, config
from dotenv import load_dotenv
from dj_database_url import config as dj_database_url_config

BASE_DIR = Path(__file__).resolve().parent.parent
# Prefer the project-local .env during local development, even if the shell
# already has conflicting variables set.
load_dotenv(BASE_DIR / ".env", override=True)


def _is_placeholder(value):
    if not value:
        return True
    normalized = value.strip().lower()
    return normalized.startswith("your_") or normalized in {
        "changeme",
        "change-me",
        "replace-me",
        "example",
    }

SECRET_KEY = config("DJANGO_SECRET_KEY", default="replace-me")
DEBUG = config("DEBUG", default=False, cast=bool)

# Configure ALLOWED_HOSTS based on environment
if DEBUG:
    ALLOWED_HOSTS = [
        "novaprofit.onrender.com",
        ".onrender.com",
        "localhost",
        "127.0.0.1",
        "testserver",
        "*.localhost",
        "0.0.0.0",
        "*"  # Allow all hosts in development
    ]
else:
    ALLOWED_HOSTS = [
        "novaprofit.onrender.com",
        ".onrender.com",
    ]

if not DEBUG and _is_placeholder(SECRET_KEY):
    raise ValueError("DJANGO_SECRET_KEY must be set in production")

if not DEBUG and not ALLOWED_HOSTS:
    raise ValueError("ALLOWED_HOSTS must be configured in production")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "channels",
    "accounts",
    "core",
    "wallet",
    "notifications",
    "admin_panel",
    "django_celery_results",
    "tasks",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.cache.UpdateCacheMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.cache.FetchFromCacheMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "novaprofit.middleware.RequestLoggingMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Security settings
if not DEBUG:
    SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "True").lower() in ("1", "true", "yes")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = os.environ.get("SECURE_BROWSER_XSS_FILTER", "True").lower() in ("1", "true", "yes")
    SECURE_CONTENT_TYPE_NOSNIFF = os.environ.get("SECURE_CONTENT_TYPE_NOSNIFF", "True").lower() in ("1", "true", "yes")
    X_FRAME_OPTIONS = os.environ.get("X_FRAME_OPTIONS", "DENY")
    SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", 31536000))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get("SECURE_HSTS_INCLUDE_SUBDOMAINS", "True").lower() in ("1", "true", "yes")
    SECURE_HSTS_PRELOAD = os.environ.get("SECURE_HSTS_PRELOAD", "True").lower() in ("1", "true", "yes")
    SECURE_REFERRER_POLICY = os.environ.get("SECURE_REFERRER_POLICY", "strict-origin-when-cross-origin")
else:
    # Development mode - disable SSL
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_BROWSER_XSS_FILTER = False
    SECURE_CONTENT_TYPE_NOSNIFF = False
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
    SECURE_REFERRER_POLICY = 'no-referrer-when-downgrade'

ROOT_URLCONF = "novaprofit.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "accounts.context_processors.social_links",
            ],
        },
    },
]

WSGI_APPLICATION = "novaprofit.wsgi.application"
ASGI_APPLICATION = "novaprofit.asgi.application"

DATABASE_URL = config("DATABASE_URL", default=None)

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url_config(
            default=DATABASE_URL,
            conn_max_age=config("CONN_MAX_AGE", default=60, cast=int),
            ssl_require=config("DATABASE_SSL_REQUIRE", default=False, cast=bool),
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config("DB_NAME", default="novaprofit"),
            "USER": config("DB_USER", default="postgres"),
            "PASSWORD": config("DB_PASSWORD", default=""),
            "HOST": config("DB_HOST", default="localhost"),
            "PORT": config("DB_PORT", default="5432"),
            "CONN_MAX_AGE": config("CONN_MAX_AGE", default=60, cast=int),
        }
    }

if DATABASES["default"]["ENGINE"] == "django.db.backends.mysql":

    DATABASES["default"].setdefault("OPTIONS", {})
    DATABASES["default"]["OPTIONS"].setdefault("init_command", "SET sql_mode='STRICT_TRANS_TABLES'")

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/login/"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 20,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.environ.get("SIMPLE_JWT_ACCESS_TOKEN_LIFETIME_MINUTES", 60))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.environ.get("SIMPLE_JWT_REFRESH_TOKEN_LIFETIME_DAYS", 7))),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
if DEBUG:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        },
    }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [REDIS_URL],
            },
        },
    }

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = "django-db"
CELERY_BEAT_SCHEDULE = {
    "reward_active_users": {
        "task": "wallet.tasks.reward_active_users",
        "schedule": 300.0,
    },
}

# CORS settings
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
    # Add localhost to CSRF_TRUSTED_ORIGINS for development
    CSRF_TRUSTED_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000']
else:
    cors_origins = [origin.strip() for origin in os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',') if origin.strip()]
    CORS_ALLOWED_ORIGINS = cors_origins if cors_origins else []
    csrf_origins = [origin.strip() for origin in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if origin.strip()]
    CSRF_TRUSTED_ORIGINS = csrf_origins if csrf_origins else []

# Cache and session settings for faster request performance
REDIS_CACHE_URL = os.environ.get('REDIS_CACHE_URL', REDIS_URL)
if DEBUG:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_CACHE_URL,
        }
    }

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_CACHE_ALIAS = 'default'
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = int(os.environ.get('CACHE_MIDDLEWARE_SECONDS', 300))
CACHE_MIDDLEWARE_KEY_PREFIX = 'novaprofit'
CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True

# Email configuration for OTP
# IMPORTANT: Must set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD environment variables
# For Gmail: Use App Password (not regular password) - https://support.google.com/accounts/answer/185833
# For SendGrid: Use API Key - https://sendgrid.com
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'profitexcustomerservice@gmail.com'
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = "Profitx Customer Service <profitexcustomerservice@gmail.com>"

# SendGrid configuration (recommended for production)
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', '')
SENDGRID_FROM_EMAIL = os.environ.get('SENDGRID_FROM_EMAIL', '')
SENDGRID_USE_SENDGRID_BACKEND = os.environ.get('SENDGRID_USE_SENDGRID_BACKEND', 'False').lower() in ('1', 'true', 'yes')
if SENDGRID_API_KEY and not _is_placeholder(SENDGRID_API_KEY):
    DEFAULT_FROM_EMAIL = SENDGRID_FROM_EMAIL or DEFAULT_FROM_EMAIL
    if SENDGRID_USE_SENDGRID_BACKEND:
        try:
            import sgbackend  # noqa: F401
            EMAIL_BACKEND = 'sgbackend.SendGridBackend'
            EMAIL_HOST = ''
            EMAIL_PORT = 0
            EMAIL_USE_TLS = False
            EMAIL_HOST_USER = ''
            EMAIL_HOST_PASSWORD = ''
        except ImportError:
            warnings.warn(
                'SendGrid Django backend not installed. Falling back to SMTP via sendgrid.net.',
            )
            EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
            EMAIL_HOST = 'smtp.sendgrid.net'
            EMAIL_PORT = 587
            EMAIL_USE_TLS = True
            EMAIL_HOST_USER = 'apikey'
            EMAIL_HOST_PASSWORD = SENDGRID_API_KEY
    else:
        EMAIL_HOST = 'smtp.sendgrid.net'
        EMAIL_PORT = 587
        EMAIL_USE_TLS = True
        EMAIL_HOST_USER = 'apikey'
        EMAIL_HOST_PASSWORD = SENDGRID_API_KEY

# In local development, fall back to console email if credentials are missing.
if DEBUG and (_is_placeholder(EMAIL_HOST_USER) or _is_placeholder(EMAIL_HOST_PASSWORD)):
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    EMAIL_HOST = ''
    EMAIL_PORT = 25
    EMAIL_HOST_USER = ''
    EMAIL_HOST_PASSWORD = ''
elif not EMAIL_HOST_USER or not EMAIL_HOST_PASSWORD:
    warnings.warn(
        "WARNING: EMAIL_HOST_USER and EMAIL_HOST_PASSWORD environment variables are not set. "
        "OTP emails will NOT be sent. Please configure SMTP credentials for production use. "
        "For Gmail, generate an App Password at https://myaccount.google.com/apppasswords "
        "For SendGrid, get API Key at https://sendgrid.com",
        RuntimeWarning
    )

# Static files
static_dir = BASE_DIR / "static"
if static_dir.exists():
    STATICFILES_DIRS = [static_dir]
else:
    STATICFILES_DIRS = []
