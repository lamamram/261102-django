# catalog/tests/test_views.py
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import Client as ClientHTTP
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from catalog.models import Client, Contrat, Inscription
from catalog.services import inscrire
from catalog.views import interne

from .factories import (creer_client, creer_formation, creer_intervention,
                        creer_utilisateur)

DONNEES_CLIENT = {
    'prenom': 'Marie', 'nom': 'Dupont', 'societe': 'Acme',
    'email': 'marie@acme.fr', 'telephone': '',
}


def niveaux(reponse):
    """Niveaux des messages affichés (« success », « error »…) : indépendants de la langue."""
    return [message.level_tag for message in reponse.context['messages']]


class PagesPubliquesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.formation = creer_formation(nom='Django initiation')
        cls.ouverte = creer_intervention(cls.formation, statut='A')
        cls.cloturee = creer_intervention(cls.formation, statut='C')

    def test_accueil(self):
        # ---------> urrlib/requests.get("http//xxxx.xx/yy/zz...")
        self.assertEqual(self.client.get(reverse('catalog:accueil')).status_code, 200)

    def test_catalogue_liste_les_formations(self):
        reponse = self.client.get(reverse('catalog:liste-formations'))
        self.assertContains(reponse, self.formation.code)
        self.assertTemplateUsed(reponse, 'catalog/liste_formations.html')

    def test_detail_n_affiche_que_les_interventions_a_venir(self):
        reponse = self.client.get(reverse('catalog:detail-formation', args=[self.formation.pk]))
        self.assertContains(reponse, self.ouverte.numero)
        self.assertNotContains(reponse, self.cloturee.numero)

    def test_formation_inconnue_utilise_la_page_404_du_projet(self):
        # ----------------------------------------------------------------> <int:pk>
        reponse = self.client.get(reverse('catalog:detail-formation', args=[999999]))
        self.assertEqual(reponse.status_code, 404)
        self.assertTemplateUsed(reponse, 'catalog/404.html')


class PagesErreurTests(SimpleTestCase):
    def test_la_page_500_appelee_directement(self):
        # --------> requête mockée
        requete = RequestFactory().get('/')          # pas de middleware, pas d'URL : la vue seule
        reponse = interne(requete)
        self.assertEqual(reponse.status_code, 500)


class CrudClientTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.gestionnaire = creer_utilisateur(
            'gestionnaire',
            ['view_client', 'add_client', 'change_client', 'delete_client'],
            staff=True,
        )

    def setUp(self):
        #-----------> authentification d'un utilisateur qui peut gérer les clients
        self.client.force_login(self.gestionnaire)

    def test_creation_valide(self):
        reponse = self.client.post(reverse('catalog:nouveau-client'), DONNEES_CLIENT, follow=True)
        self.assertRedirects(reponse, reverse('catalog:clients'))
        self.assertTrue(Client.objects.filter(email='marie@acme.fr').exists())
        self.assertEqual(niveaux(reponse), ['success'])

    def test_creation_invalide_reaffiche_le_formulaire_sans_rien_ecrire(self):
        reponse = self.client.post(reverse('catalog:nouveau-client'), {**DONNEES_CLIENT, 'email': ''})
        self.assertEqual(reponse.status_code, 200)
        self.assertTrue(reponse.context['form'].has_error('email', code='required'))
        self.assertEqual(Client.objects.count(), 0)

    def test_modification(self):
        existant = creer_client(prenom='Ancien', email='marie@acme.fr')
        self.client.post(reverse('catalog:modifier-client', args=[existant.pk]),
                         {**DONNEES_CLIENT, 'prenom': 'Nouveau'})
        existant.refresh_from_db()
        self.assertEqual(existant.prenom, 'Nouveau')

    def test_la_page_de_suppression_en_get_ne_supprime_rien(self):
        existant = creer_client()
        reponse = self.client.get(reverse('catalog:supprimer-client', args=[existant.pk]))
        self.assertEqual(reponse.status_code, 200)
        self.assertTrue(Client.objects.filter(pk=existant.pk).exists())

    def test_suppression(self):
        existant = creer_client()
        self.client.post(reverse('catalog:supprimer-client', args=[existant.pk]))
        self.assertFalse(Client.objects.filter(pk=existant.pk).exists())

    def test_suppression_d_un_client_avec_contrat_est_refusee_proprement(self):
        existant = creer_client()
        Contrat.objects.create(client=existant, titre='Contrat', numero='CT-T-1',
                               montant_ht=Decimal('100.00'))
        reponse = self.client.post(reverse('catalog:supprimer-client', args=[existant.pk]), follow=True)
        self.assertEqual(reponse.status_code, 200)            # pas de 500
        self.assertTrue(Client.objects.filter(pk=existant.pk).exists())
        self.assertEqual(niveaux(reponse), ['error'])

    def test_les_donnees_sont_echappees(self):
        creer_client(prenom='<b>gras</b>')
        reponse = self.client.get(reverse('catalog:clients'))
        self.assertContains(reponse, '&lt;b&gt;gras&lt;/b&gt;')
        self.assertNotContains(reponse, '<b>gras</b>')

    def test_recherche(self):
        creer_client(nom='Dupont')
        creer_client(nom='Martin')
        reponse = self.client.get(reverse('catalog:clients'), {'q': 'dup'})
        self.assertEqual([c.nom for c in reponse.context['clients']], ['Dupont'])


class InscriptionBackOfficeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.gestionnaire = creer_utilisateur(
            'gestionnaire', ['view_inscription', 'add_inscription'], staff=True,
        )
        cls.intervention = creer_intervention(capacite=50)
        cls.alice = creer_client()

    def setUp(self):
        self.client.force_login(self.gestionnaire)

    def test_le_formulaire_inscrit_le_client(self):
        reponse = self.client.post(reverse('catalog:nouvelle-inscription'),
                                   {'client': self.alice.pk, 'intervention': self.intervention.pk})
        self.assertRedirects(reponse, reverse('catalog:inscriptions'))
        self.intervention.refresh_from_db()
        self.assertEqual(self.intervention.nb_inscrits, 1)

    def test_un_doublon_devient_une_erreur_de_formulaire(self):
        donnees = {'client': self.alice.pk, 'intervention': self.intervention.pk}
        self.client.post(reverse('catalog:nouvelle-inscription'), donnees)
        reponse = self.client.post(reverse('catalog:nouvelle-inscription'), donnees)
        self.assertEqual(reponse.status_code, 200)
        self.assertTrue(reponse.context['form'].non_field_errors())
        self.assertEqual(Inscription.objects.count(), 1)

    def test_le_nombre_de_requetes_ne_depend_pas_du_nombre_de_lignes(self):
        def compter():
            """
            compter le nb de requêtes effectuées en exécutant un flux
            test l'utilisation de lazy/eager loading pour les requêtes liées
            """
            with CaptureQueriesContext(connection) as contexte:
                self.client.get(reverse('catalog:inscriptions'))
            return len(contexte)

        inscrire(self.alice, self.intervention)
        avec_une_ligne = compter()
        for _ in range(4):
            inscrire(creer_client(), self.intervention)
        self.assertEqual(compter(), avec_une_ligne)


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class CreerCompteTests(TestCase):
    donnees = {
        'username': 'nora', 'first_name': 'Nora', 'last_name': 'Vidal',
        'email': 'Nora@Example.org',
        'password1': 'ZephyrQuartz-2026!', 'password2': 'ZephyrQuartz-2026!',
    }

    def test_cree_le_compte_connecte_et_rattache_le_client_existant(self):
        existant = creer_client(email='nora@example.org')
        reponse = self.client.post(reverse('catalog:creer-compte'), self.donnees)
        self.assertRedirects(reponse, reverse('catalog:mon-espace'))
        user = get_user_model().objects.get(username='nora')
        self.assertEqual(user.email, 'nora@example.org')                   # normalisé
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)
        existant.refresh_from_db()
        self.assertEqual(existant.utilisateur, user)

    def test_cree_un_client_quand_l_adresse_est_inconnue(self):
        self.client.post(reverse('catalog:creer-compte'), self.donnees)
        self.assertEqual(Client.objects.get(email='nora@example.org').utilisateur.username, 'nora')

    def test_mots_de_passe_differents_ne_creent_rien(self):
        reponse = self.client.post(reverse('catalog:creer-compte'),
                                   {**self.donnees, 'password2': 'autre-2026-xyz!'})
        self.assertEqual(reponse.status_code, 200)
        self.assertFalse(get_user_model().objects.filter(username='nora').exists())


class MonEspaceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.intervention = creer_intervention(capacite=5)
        cls.alice = creer_utilisateur('alice')
        cls.bob = creer_utilisateur('bob')
        cls.client_alice = creer_client(utilisateur=cls.alice)
        cls.client_bob = creer_client(utilisateur=cls.bob)
        cls.inscription_alice = inscrire(cls.client_alice, cls.intervention)
        cls.inscription_bob = inscrire(cls.client_bob, cls.intervention)

    def setUp(self):
        self.client.force_login(self.alice)

    def test_ne_liste_que_mes_inscriptions(self):
        reponse = self.client.get(reverse('catalog:mon-espace'))
        self.assertEqual(list(reponse.context['inscriptions']), [self.inscription_alice])

    def test_annuler_la_mienne_libere_la_place(self):
        reponse = self.client.post(reverse('catalog:annuler-ma-inscription', args=[self.inscription_alice.pk]))
        self.assertRedirects(reponse, reverse('catalog:mon-espace'))
        self.inscription_alice.refresh_from_db()
        self.assertEqual(self.inscription_alice.statut, 'X')

    def test_annuler_celle_d_un_autre_renvoie_404(self):
        reponse = self.client.post(reverse('catalog:annuler-ma-inscription', args=[self.inscription_bob.pk]))
        self.assertEqual(reponse.status_code, 404)
        self.inscription_bob.refresh_from_db()
        self.assertNotEqual(self.inscription_bob.statut, 'X')

    def test_annuler_exige_un_post(self):
        reponse = self.client.get(reverse('catalog:annuler-ma-inscription', args=[self.inscription_alice.pk]))
        self.assertEqual(reponse.status_code, 405)

    def test_s_inscrire(self):
        libre = creer_intervention(capacite=5)
        reponse = self.client.post(reverse('catalog:sinscrire', args=[libre.pk]), follow=True)
        self.assertRedirects(reponse, reverse('catalog:detail-formation', args=[libre.formation_id]))
        self.assertTrue(Inscription.objects.filter(client=self.client_alice, intervention=libre).exists())
        self.assertEqual(niveaux(reponse), ['success'])

    def test_s_inscrire_a_une_intervention_complete(self):
        pleine = creer_intervention(capacite=1, nb_inscrits=1)
        reponse = self.client.post(reverse('catalog:sinscrire', args=[pleine.pk]), follow=True)
        self.assertEqual(niveaux(reponse), ['error'])
        self.assertFalse(Inscription.objects.filter(intervention=pleine).exists())

    def test_s_inscrire_sans_profil_client(self):
        self.client.force_login(creer_utilisateur('sans-profil'))
        libre = creer_intervention()
        reponse = self.client.post(reverse('catalog:sinscrire', args=[libre.pk]), follow=True)
        self.assertEqual(niveaux(reponse), ['error'])

    def test_s_inscrire_exige_un_post(self):
        libre = creer_intervention()
        self.assertEqual(self.client.get(reverse('catalog:sinscrire', args=[libre.pk])).status_code, 405)


class CsrfTests(TestCase):
    def test_un_post_sans_jeton_est_refuse(self):
        # -----------> client custom
        navigateur = ClientHTTP(enforce_csrf_checks=True)       # le client de test n'applique pas le CSRF par défaut
        navigateur.force_login(creer_utilisateur('alice'))
        reponse = navigateur.post(reverse('catalog:sinscrire', args=[1]))
        self.assertEqual(reponse.status_code, 403)
