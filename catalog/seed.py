"""Peupler la base SQLite de démonstration.

Usage (depuis la racine du projet, après `python manage.py migrate`) :
    python -m catalog.seed

Idempotent : peut être relancé sans dupliquer les données.
"""
from datetime import date
import os

# django.core.exceptions.ImproperlyConfigured: 
# Requested setting INSTALLED_APPS, but settings are not configured. 
# You must either define the environment variable 
# DJANGO_SETTINGS_MODULE or call settings.configure() before accessing settings.
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gesti.settings')
django.setup()

# à importer après avoir utiliser django !!!
from catalog.models import Client, Competence, Contrat, Formation, Session

COMPETENCES = ['Django', 'ORM', 'Templates', 'Formulaires']

# code, nom, public, durée (j), prix HT, nouveauté, compétences
FORMATIONS = [
    ('PY-101', 'Django : initiation',        'Développeurs', 3, 1890.00, False, ['Django', 'Templates']),
    ('PY-102', 'Django : approfondissement', 'Développeurs', 2, 2490.00, False, ['Django', 'ORM']),
    ('DA-201', 'Data analysis with Python',  'Analystes',    5, 2190.00, True,  ['ORM']),
]

# numéro, code formation, début, fin, ville, capacité, inscrits, statut
SESSIONS = [
    ('PY-101-2612', 'PY-101', date(2026, 12, 1), date(2026, 12, 3),  'Paris', 12, 7, 'A'),
    ('PY-102-2601', 'PY-102', date(2027, 1, 12), date(2027, 1, 13),  'Lyon',   8, 8, 'A'),  # complet
    ('DA-201-2611', 'DA-201', date(2026, 11, 9), date(2026, 11, 13), 'Paris', 10, 3, 'E'),
]


def seed_competences():
    for nom in COMPETENCES:
        # create ==> INSERT ==> non idempotent
        # get ==> SELECT mais lève une exc si n'existe pas => non idempotent
        # get_or_create ==> retourne ou créer => idempotent 
        Competence.objects.get_or_create(nom=nom)

if __name__ == "__main__":
    seed_competences()
