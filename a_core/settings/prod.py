from .base import *  # noqa: F403,F401

DEBUG = config("DEBUG", cast=bool)

ALLOWED_HOSTS = ["render.com", ".onrender.com"]


# CORS CONFIGURATION
CORS_ALLOWED_ORIGINS = [
    "https://nysc-ibn2.vercel.app",
    "https://www.nysc-ibn2.vercel.app",
]

CORS_ORIGIN_WHITELIST = (
    "https://nysc-ibn2.vercel.app",
    "https://www.nysc-ibn2.vercel.app",
)

CSRF_TRUSTED_ORIGINS = [
    "https://nysc-ibn2.vercel.app",
    "https://www.nysc-ibn2.vercel.app",
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
