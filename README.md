# rjrajujha.github.io

Production-ready personal portfolio built with Django + TailwindCSS. Database-optional by default, offline-first NLP chatbot, and Docker-ready deployment.

## Stack
- Django 6 (server-rendered templates, modular apps)
- TailwindCSS (compiled, purge-enabled)
- Offline NLP chatbot with optional OpenAI / Gemini providers
- Docker multi-stage image (Gunicorn)

## Project Structure
```text
manage.py
portfolio/                  # settings, urls, database_config
apps/
  core/                     # homepage content (content.py)
  projects/                 # content-driven project pages
  contact/                  # email-only contact workflow
  chatbot/                  # NLP + provider API
docs/DATABASE.md            # optional persistence guide
```

## Local Setup
1. Create virtualenv and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy environment file:
   ```bash
   cp .env.example .env
   ```
3. Build CSS:
   ```bash
   npm install
   npm run build:css
   ```
4. Start server (no migrations required):
   ```bash
   python manage.py runserver
   ```

## Docker
```bash
docker compose up --build
```
Health check: `http://127.0.0.1:8000/health`

## Environment Variables
See `.env.example` for full list. Highlights:
- `USE_DATABASE=false` (default) — content-driven, no ORM persistence
- `CHATBOT_PROVIDER=local|openai|gemini` — external provider with local NLP fallback
- `RESUME_URL`, `RESUME_ACCESS_KEY`, `RESUME_SECRET_KEY` — secure resume link flow
- SMTP/contact settings for email delivery

## Chatbot
- Endpoint: `POST /chatbot/api/chat/`
- Offline intents: identity, skills, projects, contact, resume secret (fuzzy match)
- Provider priority: `CHATBOT_PROVIDER` env → fallback to local NLP

## Optional Database
Set `USE_DATABASE=true` and configure SQLite/PostgreSQL per `docs/DATABASE.md` and `portfolio/database.example.py`.

## Tests
```bash
python manage.py test
```
