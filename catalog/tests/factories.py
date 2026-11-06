# catalog/tests/factories.py
from datetime import timedelta
from decimal import Decimal
from itertools import count

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.utils import timezone

from catalog.models import Client, Formation, Intervention

_sequence = count(1)


def creer_formation(**champs):
    n = next(_sequence)
    defauts = {'code': f'T-{n:03d}', 'nom': f'Formation {n}', 'duree': 2, 'prix': Decimal('1000.00')}
    return Formation.objects.create(**{**defauts, **champs})


def creer_intervention(formation=None, **champs):
    n = next(_sequence)
    debut = timezone.localdate() + timedelta(days=30)
    defauts = {
        'numero': f'T-{n:03d}-INT',
        'formation': formation or creer_formation(),
        'date_debut': debut,
        'date_fin': debut + timedelta(days=2),
        'capacite': 10,
        'statut': 'A',
    }
    return Intervention.objects.create(**{**defauts, **champs})


def creer_client(**champs):
    n = next(_sequence)
    defauts = {'prenom': 'Test', 'nom': f'Client{n}', 'email': f'client{n}@example.org'}
    return Client.objects.create(**{**defauts, **champs})


def creer_utilisateur(username, permissions=(), staff=False):
    """Compte sans mot de passe (pas de hachage coûteux) ; se connecte via force_login()."""
    user = get_user_model().objects.create_user(username, f'{username}@example.org', is_staff=staff)
    trouvees = Permission.objects.filter(content_type__app_label='catalog', codename__in=permissions)
    if trouvees.count() != len(set(permissions)):
        raise ValueError(f'Permission inconnue dans {permissions}')
    user.user_permissions.add(*trouvees)
    return user
