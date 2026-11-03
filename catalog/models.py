from django.db import models


# Create your models here.
class Formation(models.Model):
    code = models.CharField('code', max_length=12, unique=True)
    nom = models.CharField('intitulé', max_length=120)
    
    # blank vs null: null=False par défaut en base, 
    # blank=True permet d'avoir un champs de formulaire (python) lié à ce modèle vide
    # ==> lié à des mécanisme de valeur par défaut 'tout public'
    public = models.CharField('public visé', max_length=60, blank=True)
    duree  = models.PositiveSmallIntegerField('durée (jours)')
    prix  = models.DecimalField('tarif HT (€)', max_digits=10, decimal_places=2)
    
    # gestion des valeurs par défaut:
    # default => calculé en python
    # db_default => //      SQL
    nouveaute = models.BooleanField('nouveauté', default=False)
    # auto_now_add: datetime.now() lié au 1er .save() ==> CURRENT_TIMESTAMP
    date_creation = models.DateTimeField('créée le', auto_now_add=True)

    class Meta:
        """
        Métadonnée de la table
        """
        # commentaire: le nom de la table est lié au nom de la classe
        verbose_name = 'formation'
        # tri par défaut dans une liste en python
        ordering = ['code']

    def __str__(self):
        return f'{self.code} - {self.nom}'

