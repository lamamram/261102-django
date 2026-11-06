# gesti/settings_prod.py
"""
Production : DJANGO_SETTINGS_MODULE=gesti.settings_prod

Tout ce qui est secret ou propre à la machine vient de l'environnement ; une valeur
obligatoire absente arrête le démarrage au lieu de produire un site à moitié configuré.
"""
import os

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

from .settings import *  # noqa: F401,F403 — on part de la configuration commune, puis on durcit


def requis(nom):
    valeur = os.environ.get(nom, '').strip()
    if not valeur:
        raise ImproperlyConfigured(f'Variable d\'environnement obligatoire absente : {nom}')
    return valeur


DEBUG = False
SECRET_KEY = requis('SECRET_KEY')
ALLOWED_HOSTS = env_list('ALLOWED_HOSTS') or requis('ALLOWED_HOSTS')   # noqa: F405
CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS')                # noqa: F405 — ex. https://formation.example.org

# les outils de développement n'existent pas en production
INSTALLED_APPS = [a for a in INSTALLED_APPS if a not in ('debug_toolbar', 'django_extensions')]  # noqa: F405
MIDDLEWARE = [m for m in MIDDLEWARE if 'debug_toolbar' not in m]                                  # noqa: F405
# WhiteNoise sert les fichiers de STATIC_ROOT : juste après SecurityMiddleware
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    # noms hachés (cache navigateur illimité) + versions gzip/brotli ; exige `collectstatic`
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

DATABASES = {'default': dj_database_url.parse(requis('DATABASE_URL'), conn_max_age=600, conn_health_checks=True)}

# HTTPS : le reverse proxy termine TLS et transmet X-Forwarded-Proto
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = env_bool('SECURE_SSL_REDIRECT', True)     # noqa: F405
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '3600'))   # à relever (1 an) une fois HTTPS validé
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', False)   # noqa: F405
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'                         # URL de retour OAuth construites en https

EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')

# journaux sur la sortie standard : c'est la plateforme (Docker, systemd…) qui les collecte
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {'simple': {'format': '{asctime} {levelname} {name} {message}', 'style': '{'}},
    'handlers': {'console': {'class': 'logging.StreamHandler', 'formatter': 'simple'}},
    'root': {'handlers': ['console'], 'level': os.environ.get('LOG_LEVEL', 'INFO')},
}
