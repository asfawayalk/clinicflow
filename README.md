# ClinicFlow

A clinic appointment & queue management REST API built with Django and Django REST Framework.

> Portfolio project — built feature by feature, each in its own commit.

## Features so far

- [x] REST API: doctors, patients, appointments (CRUD) with validation
  - no double-booking a doctor for the same time slot
  - appointments must be in the future
  - filter appointments by `?status=` and `?doctor=`
- [x] Auto-generated OpenAPI 3 docs (drf-spectacular)
  - Swagger UI at `/api/docs/`
  - ReDoc at `/api/redoc/`
  - raw schema at `/api/schema/`
- [x] Dockerized: `docker compose up` runs the API + PostgreSQL
  - environment-driven settings (secret key, debug, hosts, database)
  - Postgres with healthcheck; automatic migrations on startup
- [x] JWT authentication (simple-jwt)
  - `POST /api/auth/register/` — sign up (with password strength validation)
  - `POST /api/auth/token/` and `/api/auth/token/refresh/` — obtain / refresh tokens
  - `GET /api/auth/me/` — current user profile
  - all clinic endpoints require authentication; API docs stay public
- [x] Role-based permissions (patient / receptionist / doctor)
  - self-registration creates a **patient** account with a linked patient record
  - patients see only their own record and appointments, and can book only for themselves
  - doctors see only appointments assigned to them
  - receptionists (and staff) manage everything; staff assign roles via Django admin

## Quick start (Docker)

```bash
docker compose up --build
```

API is browsable at http://127.0.0.1:8000/api/ — interactive docs at http://127.0.0.1:8000/api/docs/

## Quick start (local, SQLite)

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

## Stack

Python 3.14 · Django 6 · Django REST Framework · PostgreSQL 17 · Docker
