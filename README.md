# LocalHub Management System 

Project: `localhub_config` · App: `core` · DB: SQLite

## Layout
```
localhub_config/
    settings_additions.py   <- merge into your settings.py
    urls.py                 <- project-level urls (replace generated one)
core/
    managers.py
    models.py
    signals.py
    apps.py
    decorators.py
    forms.py
    views.py
    urls.py
    admin.py
templates/
    base.html
    auth/login.html
    auth/register.html
    dashboards/{seeker,provider,artist,admin}.html
```

## Setup

1. Create the project/app if you haven't already:
   ```bash
   django-admin startproject localhub_config .
   python manage.py startapp core
   ```
2. Drop these files into place (overwrite the generated `core/models.py`,
   `core/apps.py`, `core/admin.py`, `localhub_config/urls.py`; merge
   `settings_additions.py` into `localhub_config/settings.py`).
3. Install Pillow (required for `ImageField`):
   ```bash
   pip install django Pillow
   ```
4. Add a default avatar at `media/profiles/default.png` (any small
   placeholder image), since `Profile.profile_picture` defaults to it.
5. Migrate and run:
   ```bash
   python manage.py makemigrations core
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```
6. Visit `/register/` to create a seeker/provider/artist account, or
   `/login/` if you already have one. Post-login you're bounced to
   `/dashboard/`, which redirects to the role-specific dashboard.

## Notes
- `AUTH_USER_MODEL = 'core.User'` must be set **before** the first
  migration — if you already have migrations from a different user
  model, start a fresh SQLite DB.
- `role_required()` in `core/decorators.py` is reusable for any future
  view: `@role_required(['provider', 'admin'])`.
- The `Profile` row is created automatically via the `post_save` signal
  in `core/signals.py`, wired up in `CoreConfig.ready()` — no circular
  imports since the signal module is only imported at app-ready time.
