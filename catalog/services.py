from django.db import transaction
from django.db.models import F, Q
from django.utils.translation import get_language

from . import emails
from .models import Inscription, Intervention, Client
from django.utils.translation import gettext as _

class DejaInscrit(Exception):
    def __init__(self, cl, inter):
        self.cl = cl
        self.inter = inter

    def __str__(self):
        return _("client: %(client)s est déjà été inscrit à l'intervention: %(inter)s") % {"client": self.cl, "inter": self.inter}

class InterventionComplete(Exception):
    def __init__(self, inter):
        self.inter = inter

    def __str__(self):
        return _("plus de places sur l'intervention: %(inter)s !!") % {"inter": self.inter}

@transaction.atomic
def inscrire(client: Client, intervention: Intervention):
    """
    on inscrit si
        - le client n'est pas déjà inscrit !!!
        - s'il ya des places dispo !!!
          dans ce cas on met à jour les nb_inscrits de l'intervention
    dans ce cas on créé une inscription 
    """
    # if Inscription.objects.filter(
    #     Q(client=client) & 
    #     Q(intervention=intervention) &
    #     ~Q(statut='X')
    # ).exists():
    # exclude (NAND) != filter (AND)
    if Inscription.objects.filter(
        client=client, intervention=intervention
    ).exclude(statut='X'):
        raise DejaInscrit(client, intervention)

    # 1. retourne l'intervention s'il ya des places dispo OU QuerySet vide
    # 2. s'il ya intervention : on incrémente les places dispo
    places_prises = Intervention.objects.filter(
        pk=intervention.pk, statut='A', nb_inscrits__lt=F('capacite')
    ).update(nb_inscrits=F('nb_inscrits') +  1)
    if not places_prises:
        raise InterventionComplete(intervention)

    inscription = Inscription.objects.create(
        client=client, 
        intervention=intervention,
        montant_ht=intervention.formation.prix
    )
    # l'e-mail part APRÈS le commit : jamais pour une inscription finalement annulée par un rollback
    langue = get_language()
    transaction.on_commit(lambda: emails.confirmation_inscription(inscription, langue))
    return inscription

def annuler(inscription: Inscription) -> bool:
    """
    libère la place et change le statut à X et retourne True si le changement est fait 
    """
    # si on veut utiliser plusieurs transactions dans la même procédure
    with transaction.atomic():
       change = Inscription.objects.filter(
           pk=inscription.pk
        ).exclude(statut='X').update(statut='X')
       # change est le nb éléments modifiés: 1 => True, 0 => False
       if change:
           Intervention.objects.filter(
               pk=inscription.intervention_id
            ).update(nb_inscrits=F('nb_inscrits') - 1)
    return bool(change)


def rattacher_client(user) -> Client | None:
    """
    retrouve (ou crée) le Client portant l'e-mail de l'utilisateur et le lui rattache
    sans jamais voler un Client déjà lié à un autre compte ; None si le compte n'a pas d'e-mail
    """
    email = user.email.lower()
    if not email:
        return None
    client, _cree = Client.objects.get_or_create(
        email=email,
        defaults={'prenom': user.first_name, 'nom': user.last_name},
    )
    if client.utilisateur_id is None:
        client.utilisateur = user
        client.save(update_fields=['utilisateur'])
    return client

    