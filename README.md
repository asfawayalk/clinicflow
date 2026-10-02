# ClinicFlow

[![CI](https://github.com/asfawayalk/clinicflow/actions/workflows/ci.yml/badge.svg)](https://github.com/asfawayalk/clinicflow/actions/workflows/ci.yml)

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
- [x] Async confirmation emails (Celery + Redis)
  - booking an appointment queues a confirmation email via a `post_save` signal (`transaction.on_commit`)
  - dedicated `worker` service in Docker compose; Redis as the message broker
  - without a broker configured (plain local dev), tasks run eagerly in-process
- [x] Scheduled reminders (Celery-beat)
  - nightly job (18:00 UTC) emails every patient with a *scheduled* appointment the next day
  - dedicated `beat` service in Docker compose; schedule defined in `CELERY_BEAT_SCHEDULE`
- [x] Stripe payments (test mode)
  - `POST /api/appointments/{id}/pay/` returns a Stripe Checkout URL for the booking fee
  - `POST /api/stripe/webhook/` verifies the Stripe signature and marks the payment paid
    on `checkout.session.completed`
  - payment status embedded in the appointment response; double payment blocked
  - set `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET` env vars to enable (503 otherwise)
- [x] Live waiting-room queue (Django Channels + WebSockets)
  - open http://localhost:8000/queue/ — today's queue updates in real time
  - `ws/queue/` sends a snapshot on connect, then pushes every booking / check-in / status change
  - broadcast from a `post_save` signal through the channel layer (Redis in Docker,
    in-memory for plain local dev); served by Daphne (ASGI)
- [x] Demo data in one command: `python manage.py seed_demo`
  - idempotent; creates demo logins for every role (password `demo-pass-123`):
    `admin` (Django admin), `receptionist`, `dr.jane`, `patient`
  - seeds today's queue (visible live at `/queue/`) and tomorrow's bookings
- [x] Tests + CI (pytest, GitHub Actions)
  - 26 tests: auth flow, role permission matrix, booking validation, Stripe checkout
    & signature-verified webhook, reminder task, and the live WebSocket queue
  - CI also runs Django system checks and validates the OpenAPI schema
  - run locally: `pip install -r requirements-dev.txt && pytest`

## Quick start (Docker)

```bash
docker compose up --build
docker compose exec web python manage.py seed_demo   # optional demo data
```

API is browsable at http://127.0.0.1:8000/api/ — interactive docs at http://127.0.0.1:8000/api/docs/ — live queue at http://127.0.0.1:8000/queue/

## Quick start (local, SQLite)

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

## Stack

Python 3.14 · Django 6 · Django REST Framework · Django Channels · PostgreSQL 17 · Celery · Redis · Docker
