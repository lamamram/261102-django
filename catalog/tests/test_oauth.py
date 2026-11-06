# catalog/tests/test_oauth.py
from allauth.account.signals import user_signed_up
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from catalog.models import Client

from .factories import creer_client

APP_FACTICE = {'APP': {'client_id': 'id-factice', 'secret': 'secret-factice', 'key': ''}}


class RattachementDuClientTests(TestCase):
    """Un compte créé par un fournisseur (ou par allauth) reçoit son profil Client — sans réseau."""

    def inscrire_par_fournisseur(self, **champs):
        user = get_user_model().objects.create_user(**champs)
        user_signed_up.send(sender=get_user_model(), request=None, user=user)
        return user

    def test_cree_le_client_quand_l_email_est_inconnu(self):
        user = self.inscrire_par_fournisseur(username='octocat', email='Octo@Example.org', first_name='Octo', last_name='Cat')
        client = Client.objects.get(utilisateur=user)
        self.assertEqual((client.email, client.prenom, client.nom), ('octo@example.org', 'Octo', 'Cat'))

    def test_rattache_le_client_existant_de_meme_email(self):
        existant = creer_client(email='octo@example.org')
        user = self.inscrire_par_fournisseur(username='octocat', email='octo@example.org')
        existant.refresh_from_db()
        self.assertEqual(existant.utilisateur, user)
        self.assertEqual(Client.objects.count(), 1)

    def test_ne_prend_pas_un_client_deja_lie_a_un_autre_compte(self):
        proprietaire = get_user_model().objects.create_user('alice', 'alice@example.org')
        client = creer_client(email='alice@example.org', utilisateur=proprietaire)
        self.inscrire_par_fournisseur(username='intrus', email='alice@example.org')
        client.refresh_from_db()
        self.assertEqual(client.utilisateur, proprietaire)

    def test_sans_email_aucun_client_n_est_cree(self):
        self.inscrire_par_fournisseur(username='anonyme', email='')
        self.assertEqual(Client.objects.count(), 0)


class FluxOAuthTests(TestCase):
    @override_settings(SOCIALACCOUNT_PROVIDERS={})
    def test_aucun_bouton_sans_fournisseur_configure(self):
        self.assertNotContains(self.client.get(reverse('login')), 'GitHub')

    @override_settings(SOCIALACCOUNT_PROVIDERS={'github': APP_FACTICE})
    def test_un_bouton_par_fournisseur_configure(self):
        reponse = self.client.get(reverse('login'))
        self.assertContains(reponse, 'GitHub')
        self.assertContains(reponse, 'action="/accounts/github/login/')
        self.assertNotContains(reponse, 'Google')

    @override_settings(SOCIALACCOUNT_PROVIDERS={'github': APP_FACTICE})
    def test_le_post_redirige_vers_le_fournisseur_avec_un_state(self):
        reponse = self.client.post('/accounts/github/login/')
        self.assertEqual(reponse.status_code, 302)
        self.assertTrue(reponse['Location'].startswith('https://github.com/login/oauth/authorize?'))
        self.assertIn('client_id=id-factice', reponse['Location'])
        self.assertIn('state=', reponse['Location'])

    @override_settings(SOCIALACCOUNT_PROVIDERS={'github': APP_FACTICE})
    def test_le_get_ne_demarre_pas_le_flux(self):
        reponse = self.client.get('/accounts/github/login/')
        self.assertEqual(reponse.status_code, 200)

    def test_l_inscription_locale_d_allauth_est_fermee(self):
        self.assertTemplateUsed(self.client.get('/accounts/signup/'), 'account/signup_closed.html')
