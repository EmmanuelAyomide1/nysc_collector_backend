from decouple import config

is_dev = config("DEBUG", cast=bool)
is_prod = config("PRODUCTION", cast=bool)

if is_prod:
    from .prod import *
elif is_dev:
    from .dev import *
else:
    from .staging import *
