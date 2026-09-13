# Raju Jha — Portfolio

Personal portfolio site built with **Django** and **Supabase**.

## Stack

- Django 6 + Supabase PostgreSQL
- Tailwind CSS
- Cloudflare Turnstile + SMTP OTP contact flow

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill Mandatory section
npm install && npm run build:css
python manage.py migrate   # OTP cache table + contact public_id + durable OTP fields
python manage.py runserver
```

## Environment

See `.env.example`. Production needs `DJANGO_SECRET_KEY`, `DJANGO_ENV=production`, `DATABASE_URL`, Turnstile keys, and SMTP (`EMAIL_USE_SECURITY`). Chatbot uses `CHATBOT_PROVIDER` + `CHATBOT_MODEL`. Security cookies/HSTS apply automatically in production.

## Deploy

Set production env vars, migrate against Supabase, collectstatic, then run Gunicorn or Docker:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn portfolio.wsgi:application --bind 0.0.0.0:8000
# or: docker compose up --build
```

## Tests

```bash
python manage.py test
python manage.py check --deploy
```
