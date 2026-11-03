from django.db import models

class Competence(models.Model):
    """Compétence visée par une formation (ex. « ORM », « Templates »)."""

    nom = models.CharField('compétence', max_length=80, unique=True)
    description = models.TextField('description', blank=True)

    class Meta:
        verbose_name = 'compétence'
        ordering = ['nom']

    def __str__(self):
        return self.nom

# Create your models here.
class Formation(models.Model):
    """Une formation du catalogue — le « produit » de l'organisme."""
    code = models.CharField('code', max_length=12, unique=True)  # PY-101
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

    ### relation many-to-many
    # la table de correspondance est automatiquement créé
    # maintenant un objet formation a un attribut .competences (collection d'objet competence)
    competences = models.ManyToManyField(
        Competence,
        blank=True,
        # relation réciproque: un objet comptetence a accès un attribut .formations
        related_name='formations',
        verbose_name='compétences',
    )

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


class Session(models.Model):
    """Une session : une formation planifiée à des dates, dans une ville, avec une capacité."""

    STATUS = [
        ("A", "à venir"),
        ("E", "En cours"),
        ("C", "Clotûrée"),
    ]

    numero = models.CharField('numéro', max_length=16, unique=True) # PY-101-002
    date_debut = models.DateField('date de début')
    date_fin = models.DateField('date de fin')
    ville = models.CharField('ville', max_length=60, default='Paris')
    capacite = models.PositiveSmallIntegerField('capacité (places)')
    nb_inscrits = models.PositiveSmallIntegerField('inscrits', default=0)
    
    # énumération: injecter une liste de tuple dans choices=
    statut = models.CharField('statut', max_length=1, default="A", choices=STATUS)


    ### relation One to Many (une session est liée à UNE formation mais une formation est liée à PLUSIEURS session)
    formation = models.ForeignKey(
        Formation,
        verbose_name='formation',
        null=True,
        # on_delete = SET_NULL: si l'objet reférencée (formation) est supprimée ==> on mais NULL 
        # dans le champs formation est mis à null ET l'objet session est préservée
        # on_delete = CASCADE: l'inverse, si formation supprimée ==> sessions supprimées

        on_delete=models.SET_NULL,
        related_name="sessions"
    )

    class Meta:
        verbose_name = 'session'
        ordering = ['date_debut']

    def __str__(self):
        return self.numero

    ## décorateur property permet d'utiliser un attribut self.places_dispo
    ## qui est calculé à la volée quand on l'utilise
    @property
    def places_dispo(self):
        return max(self.capacite - self.nb_inscrits, 0)