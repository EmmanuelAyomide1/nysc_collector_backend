# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

This is the Django/DRF backend of the NYSC CDS Management System. It sits inside a monorepo (`../`) with a Next.js frontend (`../nysc_collector_frontend`). The parent `../CLAUDE.md` holds the project-wide working rules, and `PLAN.md` here is the backend spec. Read `PLAN.md` before making changes.

## Commands

All commands run from this directory, using the local virtualenv at `./venv`.

```bash
source venv/bin/activate
pip install -r requirements/dev.txt      # base + django-seed, Faker, flake8

python manage.py runserver
python manage.py makemigrations && python manage.py migrate
python manage.py createsuperuser          # prompts for batch (Batch UUID), code_no, names

# Tests (Django test runner + rest_framework.test.APITestCase; no pytest)
python manage.py test                                         # all
python manage.py test apps.payments                           # one app
python manage.py test apps.payments.tests.PaymentItemListCreateViewTests             # one class
python manage.py test apps.payments.tests.PaymentItemListCreateViewTests.test_name   # one test

flake8 apps a_core                        # lint (flake8 + flake8-django; no config file)
```

API docs are served at `/swagger/` and `/redoc/`.

### Environment / settings selection

`a_core/settings/__init__.py` picks the settings module from `.env` (read by python-decouple). See `.env-example`:
- `PRODUCTION=True` → `prod.py`
- otherwise `DEBUG=True` → `dev.py`
- otherwise → `staging.py`

Both `DEBUG` and `PRODUCTION` are read with `cast=bool` and no default, so both must be set. `DATABASE_URL` must point at PostgreSQL, which the tests also need. `base.py` also requires the Cloudinary vars to exist. `dev.py` swaps in local filesystem media storage, adds CORS for `localhost:3000`, and reads the `PAYSTACK_TEST_*` keys.

## Architecture

### Layout
- `a_core/`: project package holding settings (`base`, `dev`, `staging`, `prod`), root `urls.py`, and `pagination.py`.
- `apps/<domain>/`: one Django app per domain, each mounted at `api/<domain>/` in `a_core/urls.py`. The apps are `users`, `authentication`, `members`, `payments`, `reports`, `games` and `common`.

### Conventions that span the codebase
- **Models** inherit `apps.common.models.BaseModel`, which provides a UUID pk, `created_at` and `updated_at`, and default ordering `-created_at`.
- **User model** is `users.CustomUser` (`AUTH_USER_MODEL`). It uses email as the username, and emails are lowercased in the manager (see the recent case-insensitivity fix). It has a `role` (`member` / `admin`) and a required FK to `members.Batch`, with `(batch, code_no)` unique. `state_code` is derived from them (`OY/<yy><A|B|C>/<code_no:04>`).
- **Auth** uses JWT in HttpOnly cookies, not headers. `apps.authentication.authentication.CookieJWTAuthentication` (the default auth class) reads the `access_token` cookie. `apps.authentication.utils.set_auth_cookies` writes the access and refresh cookies. Cookie names live in `apps/common/constants.py`. Refresh tokens rotate and are blacklisted.
- **Permissions**: the global default is `IsAuthenticated`. Role checks use `apps.common.permissions` (`IsMember`, `IsAdministrator`, `IsAdminOrSelf`). Views set `permission_classes` explicitly, or override `get_permissions` per HTTP method.
- **Response envelope**: success responses are `{"success": true, "data": ...}` and errors are `{"success": false, "message": "..."}`.
  - Errors are normalized globally by `apps.common.exceptions.custom_exception_handler`, which reduces DRF error dicts to one message string.
  - Paginated lists are wrapped by `a_core.pagination.CustomPagination` (`?page_size=`, max 100, default 20).
  - `APIView`s build the envelope by hand. Generic views in `payments` wrap their output in a repeated `finalize_response` override, so follow the existing pattern when adding new ones.
- **Layering**: views stay thin and business logic goes in `services.py` (`payments/services.py`, `reports/services.py`, `authentication/services.py`). The project rules say query logic belongs in selectors, but there are no `selectors.py` modules yet. Querysets currently live in views' `get_queryset` and in services.
- **Swagger**: endpoints are annotated with `@method_decorator(name="<method>", decorator=swagger_auto_schema(..., tags=[...]))`.

### Payments (Paystack)
`payments` models: `PaymentItem` (what admins charge for), then `Payment` (a member's attempt at an item), then `Transaction` (one Paystack reference, holding the raw response).

The flow in `payments/services.py`:
1. `initialize_payment` creates the Payment and calls Paystack `/transaction/initialize`, then stores a Transaction with reference `NYSC-<hex>`.
2. `verify_payment` calls `/transaction/verify` and runs `_apply_transaction_result`, which updates the Transaction and the Payment status.

The webhook (`PaystackWebhookView`) checks the HMAC-SHA512 `x-paystack-signature`. On `charge.success` it calls `verify_payment` in a background thread scheduled with `transaction.on_commit`. Per `PLAN.md`, webhooks are the source of truth. Paystack errors surface as `PaystackError` (HTTP 502). Tests mock `requests` rather than calling Paystack.

### Password reset
Forgot-password creates an `authentication.Otp` that is valid for 24h. An admin resolves these requests manually, through the admin-only `password-reset-requests/` endpoint and WhatsApp. No email is sent.

### Tests
Each app has a `tests.py` built on `APITestCase`. Tests build fixtures with module-level helpers such as `make_user(...)` and `make_payment_item(...)` in `payments/tests.py`. A user always needs a `Batch`, so tests create one with `Batch.objects.get_or_create(...)`. Authenticate in tests by setting the auth cookie or using `force_authenticate`, following the existing tests in the same app.
