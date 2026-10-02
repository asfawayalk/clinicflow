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
