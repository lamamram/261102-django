FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=gesti.settings_prod

# gettext : compilemessages (.mo) ; non versionnés, ils sont produits à la construction
RUN apt-get update \
    && apt-get install -y --no-install-recommends gettext \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN useradd --create-home appuser && chown appuser /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# SQLite (essai local) doit écrire le fichier ET son dossier : ils appartiennent à appuser
COPY --chown=appuser:appuser . .

# valeurs factices : seules les commandes de construction en ont besoin, jamais l'image finale
RUN SECRET_KEY=construction ALLOWED_HOSTS=construction DATABASE_URL=sqlite:////tmp/build.db \
    python manage.py compilemessages \
    && SECRET_KEY=construction ALLOWED_HOSTS=construction DATABASE_URL=sqlite:////tmp/build.db \
    python manage.py collectstatic --noinput

USER appuser

EXPOSE 8000
CMD ["gunicorn", "gesti.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-"]
