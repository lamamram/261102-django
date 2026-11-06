# catalog/tests/test_emails.py
from decimal import Decimal
from smtplib import SMTPException
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import translation

from catalog.models import Inscription
from catalog.services import InterventionComplete, inscrire

from .factories import creer_client, creer_formation, creer_intervention


@override_settings(SITE_URL='https://formation.example.org')
class ConfirmationInscriptionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.formation = creer_formation(nom='Django : initiation', prix=Decimal('1890.00'))
        cls.alice = creer_client(prenom='Alice', email='alice@example.org')

    def setUp(self):
        # hors requête, la langue active est celle laissée par le test précédent : on la fixe
        self.enterContext(translation.override('fr'))
        self.intervention = creer_intervention(self.formation, capacite=2, ville='Lyon')

    def inscrire_et_envoyer(self, client=None, intervention=None):
        """Dans un TestCase la transaction n'est jamais validée : on exécute les on_commit à la main."""
        with self.captureOnCommitCallbacks(execute=True) as rappels:
            inscription = inscrire(client or self.alice, intervention or self.intervention)
        return inscription, rappels

    def test_aucun_mail_tant_que_la_transaction_n_est_pas_validee(self):
        inscrire(self.alice, self.intervention)
        self.assertEqual(mail.outbox, [])

    def test_un_mail_part_apres_le_commit(self):
        _, rappels = self.inscrire_et_envoyer()
        self.assertEqual(len(rappels), 1)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.to, ['alice@example.org'])
        self.assertEqual(message.subject, 'Inscription enregistrée : Django : initiation')

    def test_le_corps_contient_les_informations_utiles(self):
        self.inscrire_et_envoyer()
        corps = mail.outbox[0].body
        for attendu in ('Alice', 'Django : initiation', 'Lyon', '1\xa0890,00', 'https://formation.example.org/fr/mon-espace/'):
            with self.subTest(attendu=attendu):
                self.assertIn(attendu, corps)

    def test_une_version_html_accompagne_le_texte(self):
        self.inscrire_et_envoyer()
        contenu, type_mime = mail.outbox[0].alternatives[0]
        self.assertEqual(type_mime, 'text/html')
        self.assertIn('<strong>« Django : initiation »</strong>', contenu)

    def test_le_mail_suit_la_langue_active(self):
        with translation.override('en'):
            self.inscrire_et_envoyer()
        message = mail.outbox[0]
        self.assertEqual(message.subject, 'Registration saved: Django : initiation')
        self.assertIn('https://formation.example.org/en/mon-espace/', message.body)

    def test_aucun_mail_quand_l_inscription_est_refusee(self):
        complete = creer_intervention(self.formation, capacite=1, nb_inscrits=1)
        with self.captureOnCommitCallbacks(execute=True) as rappels:
            with self.assertRaises(InterventionComplete):
                inscrire(self.alice, complete)
        self.assertEqual(rappels, [])
        self.assertEqual(mail.outbox, [])

    def test_une_panne_smtp_n_annule_pas_l_inscription(self):
        with patch('django.core.mail.message.EmailMultiAlternatives.send', side_effect=SMTPException('hors service')):
            with self.assertLogs('catalog.emails', level='ERROR'):
                inscription, _ = self.inscrire_et_envoyer()
        self.assertTrue(Inscription.objects.filter(pk=inscription.pk).exists())
        self.assertEqual(mail.outbox, [])
