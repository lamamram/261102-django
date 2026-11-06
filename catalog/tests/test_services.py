# catalog/tests/test_services.py
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.db import IntegrityError, transaction
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from catalog.models import Inscription, Intervention
from catalog.services import DejaInscrit, InterventionComplete, annuler, inscrire

from .factories import creer_client, creer_formation, creer_intervention


class InterventionTests(SimpleTestCase):
    """Aucun accès base : SimpleTestCase suffit."""

    def test_places_dispo(self):
        self.assertEqual(Intervention(capacite=10, nb_inscrits=3).places_dispo, 7)

    def test_places_dispo_ne_descend_pas_sous_zero(self):
        self.assertEqual(Intervention(capacite=5, nb_inscrits=7).places_dispo, 0)


class InscrireTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.formation = creer_formation(prix=Decimal('1890.00'))
        cls.alice = creer_client()
        cls.bob = creer_client()

    def setUp(self):
        self.intervention = creer_intervention(self.formation, capacite=2)

    def places_prises(self):
        self.intervention.refresh_from_db()
        return self.intervention.nb_inscrits

    def test_cree_la_ligne_et_prend_une_place(self):
        inscription = inscrire(self.alice, self.intervention)
        inscription.refresh_from_db()
        self.assertEqual(inscription.statut, 'P')
        self.assertEqual(inscription.montant_ht, Decimal('1890.00'))
        self.assertEqual(self.places_prises(), 1)

    def test_le_montant_est_copie_pas_reference(self):
        inscription = inscrire(self.alice, self.intervention)
        self.formation.prix = Decimal('2500.00')
        self.formation.save()
        inscription.refresh_from_db()
        self.assertEqual(inscription.montant_ht, Decimal('1890.00'))

    def test_refuse_le_doublon_sans_toucher_au_compteur(self):
        inscrire(self.alice, self.intervention)
        with self.assertRaises(DejaInscrit):
            inscrire(self.alice, self.intervention)
        self.assertEqual(self.places_prises(), 1)

    def test_refuse_la_derniere_place_deja_prise(self):
        inscrire(self.alice, self.intervention)
        inscrire(self.bob, self.intervention)
        troisieme = creer_client()
        with self.assertRaises(InterventionComplete):
            inscrire(troisieme, self.intervention)
        self.assertEqual(self.places_prises(), 2)
        self.assertFalse(Inscription.objects.filter(client=troisieme).exists())

    def test_refuse_une_intervention_non_ouverte(self):
        for statut in ('E', 'C'):
            with self.subTest(statut=statut):
                fermee = creer_intervention(self.formation, statut=statut)
                with self.assertRaises(InterventionComplete):
                    inscrire(self.alice, fermee)

    def test_l_echec_de_la_creation_annule_la_place_prise(self):
        with patch.object(Inscription.objects, 'create', side_effect=IntegrityError):
            with self.assertRaises(IntegrityError):
                inscrire(self.alice, self.intervention)
        self.assertEqual(self.places_prises(), 0)


class AnnulerTests(TestCase):
    def setUp(self):
        self.intervention = creer_intervention(capacite=2)
        self.alice = creer_client()
        self.inscription = inscrire(self.alice, self.intervention)

    def places_prises(self):
        self.intervention.refresh_from_db()
        return self.intervention.nb_inscrits

    def test_annuler_libere_la_place(self):
        self.assertTrue(annuler(self.inscription))
        self.inscription.refresh_from_db()
        self.assertEqual(self.inscription.statut, 'X')
        self.assertEqual(self.places_prises(), 0)

    def test_annuler_deux_fois_ne_libere_qu_une_place(self):
        annuler(self.inscription)
        self.assertFalse(annuler(self.inscription))
        self.assertEqual(self.places_prises(), 0)

    def test_reinscription_possible_apres_annulation(self):
        annuler(self.inscription)
        inscrire(self.alice, self.intervention)
        self.assertEqual(self.places_prises(), 1)


class ContrainteEnBaseTests(TestCase):
    """La contrainte protège aussi quand on contourne le service."""

    def setUp(self):
        self.intervention = creer_intervention()
        self.client_test = creer_client()

    def creer_directement(self, statut='P'):
        return Inscription.objects.create(
            client=self.client_test, intervention=self.intervention,
            montant_ht=Decimal('100.00'), statut=statut,
        )

    def test_deux_inscriptions_actives_sont_refusees(self):
        self.creer_directement()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.creer_directement()

    def test_une_inscription_annulee_ne_bloque_pas(self):
        self.creer_directement(statut='X')
        self.creer_directement()
        self.assertEqual(Inscription.objects.count(), 2)
