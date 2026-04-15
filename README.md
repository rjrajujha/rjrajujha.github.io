# rjrajujha.github.io

Production-ready personal portfolio built with Django + TailwindCSS, designed for backend scalability and future platform features.

## Stack
- Django (server-rendered templates, modular app architecture)
- TailwindCSS (compiled build, purge-enabled)
- SQLite (default; swappable for PostgreSQL)
- Optional AI providers: OpenAI / Ollama / mock fallback

## Project Structure
```text
manage.py
portfolio/                  # project config (settings, urls, ASGI/WSGI)
apps/
  core/                     # homepage sections and shared content
  projects/                 # project model + list/detail pages
  contact/                  # validated contact form + SMTP dispatch
  chatbot/                  # AI endpoint + chatbot logs
templates/
  base.html
  core/home.html
  projects/*.html
  partials/                 # navbar, hero, project_card, contact_form, chatbot_widget
static/
  src/styles.css            # Tailwind source
  css/main.css              # compiled Tailwind bundle
  js/site.js
  js/chatbot.js
```

## Core Features
- Hero, About, Skills, Projects, Experience, Testimonials placeholder, Contact
- Reusable template partials for maintainable UI composition
- Contact workflow with validation, spam honeypot, DB persistence, and SMTP email sending
- Floating chatbot widget with backend API endpoint (`/chatbot/api/chat/`)
- Chatbot context grounded in profile, skills, experience, and project data
- Environment-based configuration for security and provider setup

## Local Setup
1. Create and activate virtual environment, then install Python dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy environment file:
   ```bash
   cp .env.example .env
   ```
3. Install Tailwind dependencies and build CSS:
   ```bash
   npm install
   npm run build:css
   ```
4. Run migrations (includes seeded featured projects):
   ```bash
   python manage.py migrate
   ```
5. Start development server:
   ```bash
   python manage.py runserver
   ```

## Tailwind Workflow
- One-time production build:
  ```bash
  npm run build:css
  ```
- Watch mode during development:
  ```bash
  npm run watch:css
  ```

## Environment Variables
Defined in `.env.example`:
- Django: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`
- SMTP: `EMAIL_*`, `DEFAULT_FROM_EMAIL`, `CONTACT_RECEIVER_EMAIL`
- Chatbot: `CHATBOT_PROVIDER`, `OPENAI_API_KEY`, `OPENAI_MODEL`, `OLLAMA_*`, `CHATBOT_STORE_LOGS`

## AI Chatbot Architecture
- Frontend widget (`static/js/chatbot.js`) posts JSON to `/chatbot/api/chat/`
- API view (`apps/chatbot/views.py`) validates input and returns structured JSON response
- Service layer (`apps/chatbot/services.py`) routes to:
  - `openai` provider (Chat Completions API)
  - `ollama` provider (`/api/generate`)
  - `mock` provider (deterministic portfolio-aware fallback)
- Optional logging via `ChatbotLog` model for analytics/debugging

## Contact Architecture
- Form object (`apps/contact/forms.py`) for validation + anti-spam
- Submission view (`apps/contact/views.py`) stores entries and sends SMTP email
- Admin panel includes searchable contact submissions

## Deployment Suggestions
### Render
- Use `gunicorn portfolio.wsgi`
- Set env vars in Render dashboard
- Run build steps:
  - `pip install -r requirements.txt`
  - `npm install && npm run build:css`
  - `python manage.py migrate`

### VPS (Ubuntu + Nginx)
- App server: Gunicorn + systemd
- Reverse proxy: Nginx
- SSL: Let's Encrypt
- Static strategy: `collectstatic` + Nginx static location

## Scaling Plan
- Move to PostgreSQL and enable managed backups
- Add Redis for caching and queueing
- Offload chatbot logging/analytics to async workers
- Split chatbot into a dedicated internal API service if traffic grows

## Future Improvements
- Blog app with markdown/WYSIWYG publishing
- Public API app (`/api/`) for projects and profile data
- Admin-authored content model for non-code portfolio updates
- Analytics dashboard for contact conversions and chatbot usage
