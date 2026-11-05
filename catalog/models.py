from django.db import models
from django.db.models import Q

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
    # blank=True permet d'avoir un champs de formulaire (python) vide avec un placeholder lié à ce modèle
    # le placeholder par défaut est ""
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


class Intervention(models.Model):
    """Une intervention : une formation planifiée à des dates, dans une ville, avec une capacité."""

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


    ### relation Many to One (une intervention est liée à UNE formation mais une formation est liée à PLUSIEURS intervention)
    formation = models.ForeignKey(
        Formation,
        verbose_name='formation',
        null=True,
        # on_delete = SET_NULL: si l'objet reférencée (formation) est supprimée ==> on mais NULL 
        # dans le champs formation est mis à null ET l'objet intervention est préservée
        # on_delete = CASCADE: l'inverse, si formation supprimée ==> interventions supprimées

        on_delete=models.SET_NULL,
        related_name="interventions"
    )

    class Meta:
        verbose_name = 'intervention'
        ordering = ['date_debut']

    def __str__(self):
        return self.numero

    ## décorateur property permet d'utiliser un attribut self.places_dispo
    ## qui est calculé à la volée quand on l'utilise
    @property
    def places_dispo(self):
        return max(self.capacite - self.nb_inscrits, 0)


class Client(models.Model):
    """Un client (société ou stagiaire) — créé par le formulaire du bloc 6."""

    prenom = models.CharField('prénom', max_length=60)
    nom = models.CharField('nom', max_length=60)
    societe = models.CharField('société', max_length=100, blank=True)
    email = models.EmailField('e-mail', unique=True)
    telephone = models.CharField('téléphone', max_length=20, blank=True)
    date_creation = models.DateTimeField('créé le', auto_now_add=True)

    class Meta:
        verbose_name = 'client'
        ordering = ['nom', 'prenom']

    def __str__(self):
        return f'{self.prenom} {self.nom}'

class Document(models.Model):
    """Base **abstraite** : les documents administratifs partagent le même squelette."""

    titre = models.CharField('titre', max_length=160)
    numero = models.CharField('numéro', max_length=32, unique=True)
    date_creation = models.DateTimeField('créé le', auto_now_add=True)
    commentaire = models.TextField('commentaire', blank=True)

    class Meta:
        # ce modèle ne génèrera jamais une table !!!!! ni n'instanciera aucun objet
        abstract = True
        verbose_name = 'document'
        ordering = ['-date_creation']

    def __str__(self):
        return self.titre

class Contrat(Document):
    """Contrat de formation signé avec un client — hérite de Document (§5.8)."""

    client = models.ForeignKey(
        Client,
        # PROTECT est la contrepartie python de RESTRICT
        on_delete=models.PROTECT,          # un client avec des contrats ne se supprime pas
        related_name='contrats',
        verbose_name='client',
    )
    montant_ht = models.DecimalField('montant HT (€)', max_digits=12, decimal_places=2)
    date_signature = models.DateField('signé le', null=True, blank=True)

    class Meta:
        verbose_name = 'contrat'
        # à coupler avec des outils comme |pluralize
        verbose_name_plural = 'contrats'


class Inscription(models.Model):
    """Un client inscrit à une intervention — la table de liaison porte ses propres données."""
    STATUTS = [
        ('P', 'En attente'),
        ('C', 'Confirmée'),
        ('X', 'Annulée'),
    ]
    
    statut = models.CharField('statut', max_length=1, default="P", choices=STATUTS)
    montant_ht = models.DecimalField('montant HT (€)', max_digits=10, decimal_places=2)
    date_inscription = models.DateTimeField('inscrit le', auto_now_add=True)

    client = models.ForeignKey(
        Client, on_delete=models.PROTECT, related_name='inscriptions', verbose_name='client'
    )

    intervention = models.ForeignKey(
        Intervention, on_delete=models.PROTECT, related_name='inscriptions', verbose_name='intervention',
    )

    class Meta:
        verbose_name = 'inscription'
        # ---------> - : décroissant
        ordering = ['-date_inscription']
        ## contraintes composites impossible d'exprimer dans un champs
        constraints = [
            models.UniqueConstraint(
                fields=["client", "intervention"],
                # la contrainte est assurée si l'inscription n'est pas annulée (non statut X)
                # métier: un client peut annuler et ensuite se réinscrire !!!!
                condition=~Q(statut='X'),
                name='inscription_unique_client_intervention_active',
            )
        ]

    def __str__(self):
        return f"{self.client} --> {self.intervention}"   

