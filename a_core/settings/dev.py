from .base import *  # noqa: F403,F401

DEBUG = True

INSTALLED_APPS += ["django_seed"]


# CORS CONFIGURATION
INSTALLED_APPS += [
    "corsheaders",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
] + MIDDLEWARE

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://nonmetrical-pokingly-gabriele.ngrok-free.dev",
]

CORS_ALLOW_CREDENTIALS = True


# MEDIA & STATIC FILES (local dev overrides)
# Use local filesystem storage for media uploads in development instead of
# Cloudinary (base.py's default), since local dev has no Cloudinary
# credentials configured. Static files need no override here — Django's
# runserver auto-serves STATIC_URL/STATIC_ROOT when DEBUG=True.
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

MEDIA_ROOT = os.path.join(BASE_DIR, "media")


# PAYSTACK CONFIG
PAYSTACK_SECRET_KEY = config("PAYSTACK_TEST_SECRET_KEY")
PAYSTACK_PUBLIC_KEY = config("PAYSTACK_TEST_PUBLIC_KEY")


# LOGGING CONFIGURATION (local dev overrides)
# Add a console handler so logs are visible while running the dev server,
# and drop mail_admins from 'django.request' (no SMTP/ADMINS configured
# locally) so request errors are actually visible during development.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message} {exc_info}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "logs/debug.log"),
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True,
        },
        "django.request": {
            "handlers": ["console", "file"],
            "level": "ERROR",
            "propagate": False,
        },
        "celery": {
            "handlers": ["console", "file"],
            "level": "INFO",
        },
    },
}
