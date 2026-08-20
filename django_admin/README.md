# django_admin — Admin Panel & Analytics

A Django admin panel that reads/writes the **same MySQL database**
(`ecommerce_db`) that `fastapi_backend` owns. It does not run its own
migrations against `users`, `products`, or `cart_items` — those tables are
created and versioned by fastapi_backend's Alembic migrations. Django's
models for them are declared `managed = False` (see `storefront/models.py`)
so `manage.py migrate` only touches Django's own internal tables
(admin log, sessions, Django's own `auth_user` table for logging into
*this* panel).

## Design note: two separate logins, on purpose
- **App users** (customers/staff/admins who use the React storefront) live
  in the `users` table and log in via FastAPI's JWT endpoints.
- **Django admin panel access** uses Django's own built-in auth
  (`auth_user`, a table Django creates for itself) via `createsuperuser`.

These are intentionally separate systems — the Django panel is an internal
tool for whoever manages the store, not something app customers ever see
or log into.

## Setup
```
cd django_admin
python -m venv venv
.\venv\Scripts\Activate.ps1        # Windows PowerShell
pip install -r requirements.txt
copy .env.example .env             # then edit DB_PASSWORD to match your MySQL
python manage.py migrate           # only creates Django's own tables
python manage.py createsuperuser   # this is YOUR admin panel login, separate from app users
python manage.py runserver 8001    # 8001 so it doesn't clash with FastAPI's 8000
```
Open `http://127.0.0.1:8001/admin/` and log in with the superuser you just created.

## What's in the panel
- **Users** — id, name, email, role, is_active, created_at (password hash
  and Auth0 link are shown read-only — they're owned by FastAPI's auth logic)
- **Products** — full CRUD, stock is editable directly from the list view
- **Cart Items** — read view of what's currently in every user's cart
- **Analytics** (`/analytics/`, also linked from the admin home page) —
  user counts by role, product/inventory stats, and cart activity, all
  computed live from the same three tables
