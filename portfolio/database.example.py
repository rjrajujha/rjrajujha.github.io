"""Example database configuration snippets — copy patterns into .env when enabling USE_DATABASE.

See docs/DATABASE.md for full adoption guide.
"""

# SQLite (local / Vercel ephemeral)
SQLITE_EXAMPLE = {
    "USE_DATABASE": "true",
    "DB_ENGINE": "django.db.backends.sqlite3",
    "SQLITE_PATH": "/path/to/db.sqlite3",  # or /tmp/db.sqlite3 on Vercel
}

# PostgreSQL (production)
POSTGRESQL_EXAMPLE = {
    "USE_DATABASE": "true",
    "DB_ENGINE": "django.db.backends.postgresql",
    "DB_NAME": "portfolio",
    "DB_USER": "portfolio_app",
    "DB_PASSWORD": "change-me",
    "DB_HOST": "db.internal",
    "DB_PORT": "5432",
    "DB_CONN_MAX_AGE": "60",
}

# Future: vector retrieval (documented only — not wired by default)
VECTOR_EXAMPLE = {
    "USE_DATABASE": "true",
    "DB_ENGINE": "django.db.backends.postgresql",
    "VECTOR_DATABASE_URL": "postgresql://user:pass@host:5432/portfolio",
    "VECTOR_EXTENSION": "pgvector",
}
