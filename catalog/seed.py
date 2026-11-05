"""Peupler la base SQLite de démonstration.

Usage (depuis la racine du projet, après `python manage.py migrate`) :
    python -m catalog.seed

Idempotent : peut être relancé sans dupliquer les données.
"""
from datetime import date
import os
from django.db import transaction
from django.contrib.auth import get_user_model

# django.core.exceptions.ImproperlyConfigured: 
# Requested setting INSTALLED_APPS, but settings are not configured. 
# You must either define the environment variable 
# DJANGO_SETTINGS_MODULE or call settings.configure() before accessing settings.
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gesti.settings')
django.setup()

# à importer après avoir utiliser django !!!
from django.contrib.auth.models import Group, Permission
from catalog.models import Client, Competence, Contrat, Formation, Intervention


GROUPES = {
    'Formateurs': [
        'view_formation', 'view_intervention', 'view_client', 'view_inscription',
    ],
    'Gestionnaires': [
        'view_formation', 'add_formation', 'change_formation',
        'view_intervention', 'add_intervention', 'change_intervention',
        'view_client', 'add_client', 'change_client',
        'view_contrat', 'add_contrat', 'change_contrat',
        'view_inscription', 'add_inscription', 'change_inscription',
        'annuler_inscription',
    ],
}

MOT_DE_PASSE_DEMO = 'demo-2026'      # ⚠️ démonstration uniquement

# identifiant, prénom, nom, e-mail, groupe, is_staff
COMPTES = [
    ('alice',    'Alice',    'Martin',  'alice@example.org',    None,            False),
    ('francois', 'François', 'Lemaire', 'francois@example.org', 'Formateurs',    True),
    ('gaelle',   'Gaëlle',   'Roux',    'gaelle@example.org',   'Gestionnaires', True),
]

COMPETENCES = ['Django', 'ORM', 'Templates', 'Formulaires']

# code, nom, public, durée (j), prix HT, nouveauté, compétences
FORMATIONS = [
    ('PY-101', 'Django : initiation',        'Développeurs', 3, 1890.00, False, ['Django', 'Templates']),
    ('PY-102', 'Django : approfondissement', 'Développeurs', 2, 2490.00, False, ['Django', 'ORM']),
    ('DA-201', 'Data analysis with Python',  'Analystes',    5, 2190.00, True,  ['ORM']),
]

# numéro, code formation, début, fin, ville, capacité, inscrits, statut
INTERVENTIONS = [
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
        # Competence.objects.get_or_create(**{"nom": nom})

def seed_formations():
    for code, nom, public, duree, prix, nouveaute, comps in FORMATIONS:
        formation, _ = Formation.objects.update_or_create(
            # WHERE
            code=code,
            # SET
            defaults={
                'nom': nom, 'public': public, 'duree': duree,
                'prix': prix, 'nouveaute': nouveaute,
            },
        )
        # j'alimente la table de correspondance entre formation <-> competences
        # avec les ids liés au noms de compétence de la source donnée
        #    --------------------------------------- WHERE  nom IN ("django", "ORM")
        formation.competences.set(Competence.objects.filter(nom__in=comps))

# catalog/seed.py — seed_interventions() corrigée
def seed_interventions():
    for numero, code, d_debut, d_fin, ville, capacite, inscrits, statut in INTERVENTIONS:
        commun = {
            'formation': Formation.objects.get(code=code),
            'date_debut': d_debut, 'date_fin': d_fin, 'ville': ville,
            'capacite': capacite, 'statut': statut,
        }
        Intervention.objects.update_or_create(
            numero=numero,
            defaults=commun,                                     # mises à jour à chaque relance (UPDATE OR INSERT)
            create_defaults={**commun, 'nb_inscrits': inscrits}, # le compteur, une seule fois (INSERT)
        )

def seed_clients_contrats():
    client, _ = Client.objects.get_or_create(
        email='m.dupont@acme.fr',
        defaults={'prenom': 'Marie', 'nom': 'Dupont', 'societe': 'Acme'},
    )
    Contrat.objects.get_or_create(
        numero='CT-2026-011',
        defaults={
            'titre': 'Contrat PY-102 — Acme',
            'client': client,
            'montant_ht': 2490.00,
            'date_signature': date(2026, 10, 15),
        },
    )

def seed_groupes():
    for nom, codenames in GROUPES.items():
        groupe, _ = Group.objects.get_or_create(name=nom)
        groupe.permissions.set(
            Permission.objects.filter(content_type__app_label='catalog', codename__in=codenames)
        )

def seed_comptes():
    # get_user_model(): factory qui retourne le modèle d'utilisateur lié au type d'authenfication
    # par défaut auth: username/pass
    User = get_user_model()
    for username, prenom, nom, email, groupe, staff in COMPTES:
        user, cree = User.objects.get_or_create(
            username=username,
            defaults={'first_name': prenom, 'last_name': nom, 'email': email, 'is_staff': staff},
        )
        if cree:
            # génère un hash "salé" en base de donnée
            user.set_password(MOT_DE_PASSE_DEMO)
            user.save()
        if groupe:
            user.groups.add(Group.objects.get(name=groupe))

    # le compte « alice » est aussi un client
    alice = User.objects.get(username='alice')
    Client.objects.update_or_create(
        email='alice@example.org',
        defaults={'prenom': 'Alice', 'nom': 'Martin', 'utilisateur': alice},
    )

# transforme le script en transaction (tout ou rien)
@transaction.atomic
def run():
    seed_competences()
    seed_formations()
    seed_interventions()
    seed_clients_contrats()
    seed_groupes()
    seed_comptes()
    print(
        f'Seed OK — {Competence.objects.count()} compétences, '
        f'{Formation.objects.count()} formations, '
        f'{Intervention.objects.count()} interventions, '
        f'{Client.objects.count()} client(s), '
        f'{Contrat.objects.count()} contrat(s).'
    )

if __name__ == "__main__":
    run()
