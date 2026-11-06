from django.apps import apps
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from catalog.services import inscrire

from .factories import creer_client, creer_intervention, creer_utilisateur


class GardesDAccesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cible = creer_client()
        cls.stagiaire = creer_utilisateur('stagiaire')

    def pages(self):
        pk = [self.cible.pk]
        return [
            # nom d'URL, arguments, permission minimale
            ('catalog:clients', [], 'view_client'),
            ('catalog:nouveau-client', [], 'add_client'),
            ('catalog:modifier-client', pk, 'change_client'),
            ('catalog:supprimer-client', pk, 'delete_client'),
            ('catalog:inscriptions', [], 'view_inscription'),
            ('catalog:nouvelle-inscription', [], 'add_inscription'),
        ]

    def test_anonyme_est_redirige_vers_la_connexion(self):
        for nom, args, _ in self.pages():
            with self.subTest(page=nom):
                url = reverse(nom, args=args)
                self.assertRedirects(self.client.get(url), f"{reverse('login')}?next={url}")

    def test_connecte_sans_permission_recoit_403(self):
        self.client.force_login(self.stagiaire)
        for nom, args, _ in self.pages():
            with self.subTest(page=nom):
                reponse = self.client.get(reverse(nom, args=args))
                self.assertEqual(reponse.status_code, 403)
                self.assertTemplateUsed(reponse, 'catalog/403.html')

    def test_la_permission_prevue_suffit(self):
        for nom, args, permission in self.pages():
            with self.subTest(page=nom):
                self.client.force_login(creer_utilisateur(f'u-{permission}', [permission]))
                self.assertEqual(self.client.get(reverse(nom, args=args)).status_code, 200)

    def test_mon_espace_exige_la_connexion(self):
        url = reverse('catalog:mon-espace')
        self.assertRedirects(self.client.get(url), f"{reverse('login')}?next={url}")

    def test_pages_publiques_restent_publiques(self):
        for nom in ('catalog:accueil', 'catalog:liste-formations', 'catalog:creer-compte', 'login'):
            with self.subTest(page=nom):
                self.assertEqual(self.client.get(reverse(nom)).status_code, 200)


class AdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.root = get_user_model().objects.create_superuser('root', 'root@example.org')

    def setUp(self):
        self.client.force_login(self.root)

    def test_toutes_les_listes_repondent(self):
        for modele in apps.get_app_config('catalog').get_models():
            if not admin.site.is_registered(modele):
                continue
            with self.subTest(modele=modele.__name__):
                url = reverse(f'admin:catalog_{modele._meta.model_name}_changelist')
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_l_action_annuler_passe_par_le_service(self):
        intervention = creer_intervention()
        inscription = inscrire(creer_client(), intervention)
        self.client.post(reverse('admin:catalog_inscription_changelist'), {
            'action': 'annuler_selection', '_selected_action': [inscription.pk],
        })
        inscription.refresh_from_db()
        intervention.refresh_from_db()
        self.assertEqual(inscription.statut, 'X')
        self.assertEqual(intervention.nb_inscrits, 0)

    def test_pas_d_ajout_d_inscription_dans_l_admin(self):
        self.assertEqual(self.client.get(reverse('admin:catalog_inscription_add')).status_code, 403)