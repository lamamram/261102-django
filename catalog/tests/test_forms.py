# catalog/tests/test_forms.py
from django.test import TestCase

from catalog.forms import ClientForm, CompteForm, InscriptionForm

from .factories import creer_client, creer_intervention


class ClientFormTests(TestCase):
    donnees = {
        'prenom': 'Marie', 'nom': 'Dupont', 'societe': 'Acme',
        'email': 'Marie@Acme.FR', 'telephone': '+33 1 23 45 67 89',
    }

    def formulaire(self, **changements):
        return ClientForm({**self.donnees, **changements})

    def test_donnees_valides(self):
        self.assertTrue(self.formulaire().is_valid())

    def test_email_normalise_en_minuscules(self):
        form = self.formulaire()
        form.is_valid()
        self.assertEqual(form.cleaned_data['email'], 'marie@acme.fr')

    def test_email_deja_pris_meme_avec_une_autre_casse(self):
        creer_client(email='marie@acme.fr')
        form = self.formulaire()
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('email', code='unique'))

    def test_modifier_son_propre_client_ne_declenche_pas_l_unicite(self):
        existant = creer_client(email='marie@acme.fr')
        form = ClientForm({**self.donnees, 'societe': 'Autre'}, instance=existant)
        self.assertTrue(form.is_valid(), form.errors)

    def test_telephone_invalide(self):
        form = self.formulaire(telephone='abc')
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('telephone', code='telephone_invalide'))

    def test_prenom_et_nom_obligatoires(self):
        form = self.formulaire(prenom='', nom='')
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('prenom', code='required'))
        self.assertTrue(form.has_error('nom', code='required'))

    def test_seuls_les_champs_prevus_sont_exposes(self):
        self.assertEqual(list(ClientForm().fields), ['prenom', 'nom', 'societe', 'email', 'telephone'])


class InscriptionFormTests(TestCase):
    def test_ne_propose_que_les_interventions_ouvertes_avec_des_places(self):
        ouverte = creer_intervention(capacite=5)
        creer_intervention(capacite=2, nb_inscrits=2)    # complète
        creer_intervention(statut='C')                   # clôturée
        queryset = InscriptionForm().fields['intervention'].queryset
        self.assertQuerySetEqual(queryset, [ouverte], ordered=False)


class CompteFormTests(TestCase):
    donnees = {
        'username': 'nouveau', 'first_name': 'Nora', 'last_name': 'Vidal',
        'email': 'nora@example.org',
        'password1': 'ZephyrQuartz-2026!', 'password2': 'ZephyrQuartz-2026!',
    }

    def test_valide(self):
        self.assertTrue(CompteForm(self.donnees).is_valid())

    def test_confirmation_differente(self):
        form = CompteForm({**self.donnees, 'password2': 'autre-chose-2026!'})
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('password2', code='password_mismatch'))

    def test_mot_de_passe_trop_courant(self):
        form = CompteForm({**self.donnees, 'password1': '12345678', 'password2': '12345678'})
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
