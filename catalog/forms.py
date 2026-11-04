from django import forms
from django.core.exceptions import ValidationError
from .models import Client
import re

class NouveauClientForm(forms.Form):

    prenom = forms.CharField(label="Prénom", max_length=60,
                             widget=forms.TextInput(attrs={'placeholder': 'Entrez votre prénom ici...'}))
    nom = forms.CharField(label="Nom", max_length=60)
    societe   = forms.CharField(label='Société', max_length=100, required=False)
    email     = forms.EmailField(label='E-mail') # pas nécessairement unique !!!
    telephone = forms.CharField(label='Téléphone', max_length=20, required=False)

    # --------------- méthodes de validation de champs individuel ----------------
    # forme_générique = def clean_<field>(self):
    #                       ....
    #                       raise ValidationError("msg")
    
    def clean_telephone(self) -> str:
        """
        validation METIER du champs téléphone à partir de cleaned_data
        cleaned_data données déjà analysée par django (detection d'injections ...)
        """
        valeur = self.cleaned_data.get('telephone', '')
        if valeur and not re.fullmatch(r"[\d\s+]{8,20}", valeur):
            raise ValidationError("Format invalide - chiffres, espace et + attendu.")
        # CE RETURN EST IMPORTANT !!!
        return valeur

    def clean_email(self) -> str:
        valeur = self.cleaned_data.get('email')
        if valeur and Client.objects.filter(email__iexact=valeur).exists():
            raise ValidationError("Un client existe déjà avec cet e-mail.")
        return valeur

    # -------------- validation globale: nettoyage cross - champs -----------------------

    def clean(self):
        data = self.cleaned_data
        prenom, nom = self.cleaned_data.get('prenom'), self.cleaned_data.get('nom')
        if prenom and nom and prenom.lower() == 'marie' and nom.lower() == 'dupont' \
                and not data.get('societe'):

            # add_error permet de cibler le champs en erreur dans le cas de validation cross-champs
            self.add_error('societe', 'Marie Dupont est connue avec une société — la rappeler.')
            # ou créer une erreur globale
            # self.add_error(None, 'Marie Dupont est connue avec une société — la rappeler.')
        return data

class ClientForm(forms.ModelForm):
    """
    remplace NouveauClientForm et aussi la MAJ
    """

    class Meta:
        model = Client
        # champs à afficher (liste blanche)
        fields = ['prenom', 'nom', 'societe', 'email', 'telephone']
        widgets = {
            'prenom': forms.TextInput(attrs={'placeholder': 'Entrez votre prénom ici...'}) 
        }
        error_messages = {
            'email': {'unique': 'Un client existe déjà avec cet e-mail.'}
        }

    def clean_email(self):
        """
        le check a été au niveau du modèle Mais on peut normaliser !
        """
        return self.cleaned_data.get('email', '').lower()

    def clean_telephone(self):
        valeur = self.cleaned_data.get('telephone', '')
        if valeur and not re.fullmatch(r"[\d\s+]{8,20}", valeur):
            raise ValidationError("Format invalide - chiffres, espace et + attendu.")
        return valeur



