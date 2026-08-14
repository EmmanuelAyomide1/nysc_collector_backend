from .base import *  # noqa: F403,F401

DEBUG = config("DEBUG", cast=bool)

ALLOWED_HOSTS = [
    "render.com",
    ".onrender.com",
    ".vercel.app",
    "nysc-ibn2.vercel.app",
    "www.nysc-ibn2.vercel.app",
]


# CORS CONFIGURATION
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGINS = [
    "https://nysc-ibn2.vercel.app",
    "https://www.nysc-ibn2.vercel.app",
    "https://nysc-collector-frontend.owoeyeemmanuel206.workers.dev",
]

CORS_ORIGIN_WHITELIST = (
    "https://nysc-ibn2.vercel.app",
    "https://www.nysc-ibn2.vercel.app",
    "https://nysc-collector-frontend.owoeyeemmanuel206.workers.dev",
)

CSRF_TRUSTED_ORIGINS = [
    "https://nysc-ibn2.vercel.app",
    "https://www.nysc-ibn2.vercel.app",
    "https://nysc-collector-frontend.owoeyeemmanuel206.workers.dev",
]


INSTALLED_APPS += [
    "corsheaders",
]


MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
] + MIDDLEWARE


STATIC_URL = "/static/"

STATICFILES_STORAGE = "cloudinary_storage.storage.StaticCloudinaryStorage"

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# PAYSTACK CONFIG
PAYSTACK_SECRET_KEY = config("PAYSTACK_LIVE_SECRET_KEY")
PAYSTACK_PUBLIC_KEY = config("PAYSTACK_LIVE_PUBLIC_KEY")
