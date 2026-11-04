from django import forms
from django.core.exceptions import ValidationError
from .models import Client

class NouveauClientForm(forms.Form):

    prenom = forms.CharField(label="Prénom", max_length=60,
                             widget=forms.TextInput(attrs={'placeholder': 'Entrez votre prénom ici...'}))
    nom = forms.CharField(label="Prénom", max_length=60)
    societe   = forms.CharField(label='Société', max_length=100, required=False)
    email     = forms.EmailField(label='E-mail') # pas nécessairement unique !!!
    telephone = forms.CharField(label='Téléphone', max_length=20, required=False)
    