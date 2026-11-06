from datetime import date
from decimal import Decimal

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils import translation
from django.utils.formats import date_format, number_format
from django.utils.translation import ngettext

from catalog.models import Inscription, Intervention
from catalog.services import DejaInscrit, inscrire

from .factories import creer_client, creer_intervention


class NegociationDeLangueTests(TestCase):
    def test_la_racine_redirige_vers_la_langue_par_defaut(self):
        self.assertRedirects(self.client.get('/'), '/fr/')

    def test_accept_language_est_respecte_sans_prefixe(self):
        reponse = self.client.get('/', headers={'accept-language': 'en'})
        self.assertRedirects(reponse, '/en/')

    def test_le_prefixe_de_l_url_l_emporte_sur_le_navigateur(self):
        reponse = self.client.get('/fr/formations/', headers={'accept-language': 'en'})
        self.assertContains(reponse, 'Connexion')

    def test_set_language_pose_le_cookie_et_traduit_le_prefixe(self):
        reponse = self.client.post(reverse('set_language'), {'language': 'en', 'next': '/fr/formations/'})
        self.assertRedirects(reponse, '/en/formations/')
        self.assertEqual(reponse.cookies[settings.LANGUAGE_COOKIE_NAME].value, 'en')


class PagesTraduitesTests(TestCase):
    def test_navigation_en_francais_et_en_anglais(self):
        fr = self.client.get('/fr/formations/')
        en = self.client.get('/en/formations/')
        self.assertContains(fr, 'Connexion')
        self.assertNotContains(fr, 'Log in')
        self.assertContains(en, 'Log in')
        self.assertNotContains(en, 'Connexion')

    def test_l_attribut_lang_suit_la_langue(self):
        self.assertContains(self.client.get('/en/formations/'), '<html lang="en">')

    def test_les_liens_internes_gardent_la_langue(self):
        with translation.override('en'):
            connexion = reverse('login')
        self.assertEqual(connexion, '/en/comptes/login/')
        self.assertContains(self.client.get('/en/formations/'), f'href="{connexion}"')


class TraductionsDesDonneesTests(TestCase):
    def test_libelles_du_modele(self):
        with translation.override('fr'):
            self.assertEqual(str(Intervention._meta.verbose_name), 'intervention')
        with translation.override('en'):
            self.assertEqual(str(Intervention._meta.verbose_name), 'training session')

    def test_choix_d_un_champ(self):
        inscription = Inscription(statut='X')
        with translation.override('fr'):
            self.assertEqual(inscription.get_statut_display(), 'Annulée')
        with translation.override('en'):
            self.assertEqual(inscription.get_statut_display(), 'Cancelled')

    def test_message_d_erreur_d_un_service(self):
        intervention, alice = creer_intervention(), creer_client()
        inscrire(alice, intervention)
        with translation.override('en'):
            with self.assertRaisesMessage(DejaInscrit, 'already registered'):
                inscrire(alice, intervention)

    def test_pluriel(self):
        def places(n):
            return ngettext('%(n)d place', '%(n)d places', n) % {'n': n}
        with translation.override('fr'):
            self.assertEqual([places(0), places(1), places(2)], ['0 place', '1 place', '2 places'])
        with translation.override('en'):
            self.assertEqual([places(0), places(1), places(2)], ['0 seats', '1 seat', '2 seats'])


class FormatsLocauxTests(TestCase):
    def test_date(self):
        jour = date(2026, 12, 1)
        with translation.override('fr'):
            self.assertEqual(date_format(jour), '1 décembre 2026')
        with translation.override('en'):
            self.assertEqual(date_format(jour), 'Dec. 1, 2026')

    def test_nombre(self):
        prix = Decimal('1890.50')
        with translation.override('fr'):
            self.assertEqual(number_format(prix, decimal_pos=2, force_grouping=True), '1\xa0890,50')
        with translation.override('en'):
            self.assertEqual(number_format(prix, decimal_pos=2, force_grouping=True), '1,890.50')