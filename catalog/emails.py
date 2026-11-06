import logging
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


def confirmation_inscription(inscription, langue=None) -> bool:
    """
    Envoie la confirmation d'inscription (texte + HTML) au client.
    Retourne False si l'envoi échoue : un e-mail raté n'annule jamais une inscription.
    """
    langue = langue or translation.get_language()
    intervention = inscription.intervention
    formation = intervention.formation

    # hors requête : pas de request.build_absolute_uri → SITE_URL + reverse() dans la langue de l'e-mail
    with translation.override(langue):
        contexte = {
            'client': inscription.client,
            'formation': formation,
            'intervention': intervention,
            'inscription': inscription,
            'url_espace': settings.SITE_URL + reverse('catalog:mon-espace'),
        }
        sujet = _('Inscription enregistrée : %(formation)s') % {'formation': formation.nom}
        texte = render_to_string('catalog/emails/confirmation_inscription.txt', contexte)
        html = render_to_string('catalog/emails/confirmation_inscription.html', contexte)

    message = EmailMultiAlternatives(sujet, texte, to=[inscription.client.email])
    message.attach_alternative(html, 'text/html')
    try:
        message.send()
    except (SMTPException, OSError):
        logger.exception("Envoi impossible de la confirmation de l'inscription %s", inscription.pk)
        return False
    return True
