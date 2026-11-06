# catalog/tests/test_export.py
import csv
import io
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from catalog.services import annuler, inscrire

from .factories import creer_client, creer_formation, creer_intervention, creer_utilisateur


class ExportInscriptionsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        formation = creer_formation(nom='Django : initiation', prix=Decimal('1890.50'))
        intervention = creer_intervention(formation, capacite=5)
        cls.alice = creer_client(prenom='Alice', nom='Martin', societe='Acme')
        cls.mallory = creer_client(prenom='Mallory', nom='Dupont', societe='=HYPERLINK("http://x")')
        cls.confirmee = inscrire(cls.alice, intervention)
        cls.annulee = inscrire(cls.mallory, intervention)
        annuler(cls.annulee)
        cls.gestionnaire = creer_utilisateur('gestionnaire', ['view_inscription'])

    def setUp(self):
        self.enterContext(translation.override('fr'))     # l'URL porte le préfixe de la langue active
        self.url = reverse('catalog:export-inscriptions')

    def lignes(self, reponse):
        # utf-8-sig : retire le BOM avant de relire le fichier comme le ferait Excel
        texte = reponse.content.decode('utf-8-sig')
        return list(csv.reader(io.StringIO(texte), delimiter=';'))

    def test_anonyme_est_redirige_vers_la_connexion(self):
        self.assertRedirects(self.client.get(self.url), f"{reverse('login')}?next={self.url}")

    def test_sans_permission_recoit_403(self):
        self.client.force_login(creer_utilisateur('stagiaire'))
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_entetes_http(self):
        self.client.force_login(self.gestionnaire)
        reponse = self.client.get(self.url)
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(reponse['Content-Type'], 'text/csv; charset=utf-8')
        self.assertRegex(reponse['Content-Disposition'], r'^attachment; filename="inscriptions-\d{8}\.csv"$')
        self.assertTrue(reponse.content.startswith(b'\xef\xbb\xbf'))

    def test_une_ligne_par_inscription_apres_l_entete(self):
        self.client.force_login(self.gestionnaire)
        lignes = self.lignes(self.client.get(self.url))
        self.assertEqual(len(lignes), 3)
        self.assertEqual(lignes[0][:2], ['Client', 'E-mail'])
        self.assertEqual(len({len(ligne) for ligne in lignes}), 1)

    def test_filtre_par_statut(self):
        self.client.force_login(self.gestionnaire)
        lignes = self.lignes(self.client.get(self.url, {'statut': 'X'}))
        self.assertEqual(len(lignes), 2)
        self.assertEqual(lignes[1][0], 'Mallory Dupont')

    def test_un_statut_inconnu_est_ignore(self):
        self.client.force_login(self.gestionnaire)
        self.assertEqual(len(self.lignes(self.client.get(self.url, {'statut': 'ZZ'}))), 3)

    def test_une_formule_est_neutralisee(self):
        self.client.force_login(self.gestionnaire)
        lignes = self.lignes(self.client.get(self.url, {'statut': 'X'}))
        self.assertEqual(lignes[1][2], '\'=HYPERLINK("http://x")')

    def test_le_montant_suit_la_langue_sans_separateur_de_milliers(self):
        self.client.force_login(self.gestionnaire)
        colonne = self.lignes(self.client.get(self.url, {'statut': 'P'}))[1][7]
        self.assertEqual(colonne, '1890,50')
        with translation.override('en'):
            url_en = reverse('catalog:export-inscriptions')
        self.assertEqual(self.lignes(self.client.get(url_en, {'statut': 'P'}))[1][7], '1890.50')
