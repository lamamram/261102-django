from allauth.account.signals import user_signed_up
from django.dispatch import receiver

from .services import rattacher_client


@receiver(user_signed_up)
def rattacher_client_au_premier_acces(request, user, **kwargs):
    """Émis par allauth à la création d'un compte (y compris social) : même profil Client que `creer_compte`."""
    rattacher_client(user)
