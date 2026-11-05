from django.contrib import admin, messages
from django.db.models import Count, F, Avg, Min, Max

from .models import Client, Competence, Contrat, Formation, Inscription, Intervention
from .services import annuler

admin.site.site_header = 'GestiFormation — administration'
admin.site.site_title = 'GestiFormation'
admin.site.index_title = "Pilotage de l'organisme"


# ---------- inlines : les objets liés, dans la page du parent ----------

class InterventionInline(admin.TabularInline):
    """
    section de la fiche d'une interface de modèle différent qui l'utilise comme relation
    """
    model = Intervention
    extra = 0
    fields = ('numero', 'date_debut', 'date_fin', 'ville', 'capacite', 'statut')
    show_change_link = True


class ContratInline(admin.TabularInline):
    model = Contrat
    extra = 0
    fields = ('numero', 'titre', 'montant_ht', 'date_signature')
    show_change_link = True


# ---------- catalogue ----------

@admin.register(Competence)
class CompetenceAdmin(admin.ModelAdmin):
    list_display = ('nom', 'nb_formations')
    search_fields = ('nom',)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_nb_formations=Count('formations'))

    @admin.display(description='formations', ordering='_nb_formations')
    def nb_formations(self, obj):
        return obj._nb_formations


@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'duree', 'prix', 'nouveaute', 'nb_interventions')
    list_editable = ('nouveaute',)
    list_filter = ('nouveaute', 'duree', 'competences')
    search_fields = ('code', 'nom')            # requis par autocomplete_fields ailleurs
    filter_horizontal = ('competences',)
    inlines = [InterventionInline]
    actions = ['marquer_nouveaute']
    fieldsets = (
        (None, {'fields': ('code', 'nom', 'public')}),
        ('Offre', {'fields': ('duree', 'prix', 'nouveaute')}),
        ('Compétences visées', {'fields': ('competences',), 'classes': ('collapse',)}),
    )

    def get_queryset(self, request):
        # distinct=True : le filtre « competences » ajoute un JOIN qui dupliquerait le comptage
        return super().get_queryset(request).annotate(_nb_interventions=Count('interventions', distinct=True))

    @admin.display(description='interventions', ordering='_nb_interventions')
    def nb_interventions(self, obj):
        return obj._nb_interventions

    @admin.action(description='Marquer comme nouveauté', permissions=['change'])
    def marquer_nouveaute(self, request, queryset):
        n = queryset.update(nouveaute=True)
        self.message_user(request, f'{n} formation(s) marquée(s) comme nouveauté.', messages.SUCCESS)


@admin.register(Intervention)
class InterventionAdmin(admin.ModelAdmin):
    list_display = ('numero', 'formation', 'date_debut', 'ville', 'statut',
                    'nb_inscrits', 'capacite', 'places')
    list_filter = ('statut', 'ville')
    search_fields = ('numero', 'formation__code', 'formation__nom')
    date_hierarchy = 'date_debut'
    list_select_related = ('formation',)
    autocomplete_fields = ('formation',)
    readonly_fields = ('nb_inscrits',)         # tenu par services.inscrire / annuler
    actions = ['cloturer']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_places=F('capacite') - F('nb_inscrits'))

    @admin.display(description='places libres', ordering='_places')
    def places(self, obj):
        return obj._places

    @admin.action(description='Clôturer les interventions sélectionnées', permissions=['change'])
    def cloturer(self, request, queryset):
        n = queryset.update(statut='C')
        self.message_user(request, f'{n} intervention(s) clôturée(s).', messages.SUCCESS)


# ---------- clients, contrats, inscriptions ----------

# @admin.register(Client)
# class ClientAdmin(admin.ModelAdmin):
#     list_display = ('nom', 'prenom', 'societe', 'email', 'utilisateur', 'date_creation')
#     list_select_related = ('utilisateur',)
#     search_fields = ('nom', 'prenom', 'societe', 'email')
#     autocomplete_fields = ('utilisateur',)
#     inlines = [ContratInline]


# @admin.register(Contrat)
# class ContratAdmin(admin.ModelAdmin):
#     list_display = ('numero', 'titre', 'client', 'montant_ht', 'date_signature')
#     list_select_related = ('client',)
#     list_filter = ('date_signature',)
#     search_fields = ('numero', 'titre', 'client__nom', 'client__email')
#     autocomplete_fields = ('client',)
#     date_hierarchy = 'date_signature'


@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display = ('client', 'intervention', 'statut', 'montant_ht', 'date_inscription')
    list_filter = ('statut', 'intervention__formation')
    list_select_related = ('client', 'intervention')
    search_fields = ('client__nom', 'client__email', 'intervention__numero')
    # tout est en lecture seule : l'état ne change que par les actions, qui respectent les règles
    readonly_fields = ('client', 'intervention', 'statut', 'montant_ht', 'date_inscription')
    actions = ['confirmer', 'annuler_selection']

    def has_add_permission(self, request):
        return False                            # une inscription se crée par services.inscrire

    def has_delete_permission(self, request, obj=None):
        return False                            # on annule, on ne supprime pas

    def has_annuler_permission(self, request):  # appelée par permissions=['annuler']
        return request.user.has_perm('catalog.annuler_inscription')

    @admin.action(description='Confirmer les inscriptions sélectionnées', permissions=['change'])
    def confirmer(self, request, queryset):
        n = queryset.filter(statut='P').update(statut='C')
        self.message_user(request, f'{n} inscription(s) confirmée(s).', messages.SUCCESS)

    @admin.action(description='Annuler les inscriptions sélectionnées', permissions=['annuler'])
    def annuler_selection(self, request, queryset):
        n = sum(annuler(inscription) for inscription in queryset)
        self.message_user(request, f'{n} inscription(s) annulée(s), places libérées.', messages.SUCCESS)

