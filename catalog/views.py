from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpRequest, HttpResponse
from .models import Formation, Intervention, Client, Inscription
from django.contrib import messages # messages Flash
from django.contrib.messages.views import SuccessMessageMixin
from .forms import NouveauClientForm, ClientForm, InscriptionForm, CompteForm
from .services import inscrire, annuler, DejaInscrit, InterventionComplete
from django.db.models import Q, ProtectedError
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, permission_required
from django.views.decorators.http import require_POST

# Create your views here.
def accueil(request: HttpRequest) -> HttpResponse:
    """
    Page d'accueil - réponse brute
    demande un objet request de type HttpRequest
    et retourne un objet HttpResponse
    """
    return HttpResponse(
        """<h1>GestiFormation</h1>
    <p>Gestion d'un organisme de formation : catalogue, sessions, inscriptions.</p>
    <a href="/formations/">Voir le catalogue</a>""",
        content_type="text/html",
        status=200)

def liste_formations(request: HttpRequest) -> HttpResponse:
    """
    liste des formations
    utilise render, qui injecte le contexte dans un fichier HTML "template"
    les templates doivent être insérés dans <app>/templates/<app>/<xxxx>.html
    """
    formations = Formation.objects.all()
    return render(request, "catalog/liste_formations.html" , {"formations": formations})

def detail_formation(request: HttpRequest, pk: int) -> HttpResponse:
    """
    détail d'une formation indexée par un id, par défaut l'indice de la liste
    """
    # prefetch_related: 1 requête supplémentaire par relation (M2M ou FK inverse), jointure faite en Python
    formation = get_object_or_404(
        Formation.objects.prefetch_related("competences"),
        pk=pk,
    )
    # formation = Formation.objects.prefetch_related('competences').filter(pk=pk).first()
    competences = formation.competences.all()
    interventions = formation.interventions.filter(statut="A").order_by('date_debut')

    return render(request, "catalog/detail_formation.html" , {
        "formation": formation, 
        "competences": competences,
        "interventions": interventions
    })

def page_introuvable(request, exception):
    """
    page rendue par le handler404 du projet
    le handler 404 demande un 2ème paramètre exception dans la vue
    """
    return render(request, "catalog/404.html", status=404)

def interne(request):
    return render(request, "catalog/500.html", status=500)

def acces_refuse(request, exception=None):
    return render(request, 'catalog/403.html', status=403)

################################ CLIENTS #######################################

########## version vues fonctions

@login_required
# ------------------> permission ou [permissions] --------> 403
@permission_required('catalog.view_client', raise_exception=True)
def liste_clients(request: HttpRequest):
    # q vient d'un queryPAram adossée à l'url en GET: domain/xxxx?q=blabla%20blibli
    q = request.GET.get('q', '').strip()
    if q:
        clients = Client.objects.filter(
            # Q permet d'utiliser les opérateur logiques dans filter: |, &, ~
            Q(prenom__icontains=q) |
            Q(nom__icontains=q) |
            Q(societe__icontains=q) |
            Q(email__icontains=q)
        )
    else:
        clients = Client.objects.all()
    return render(request, 'catalog/liste_clients.html', {
        "clients": clients
    })


def deprecated_nouveau_client(request):
    # en POST j'arrive ici car j'ai soumis le formulaire
    if request.method == 'POST':
        form = NouveauClientForm(request.POST)
        # is_valid => exécute tous les nettoyages/validations
        # génère le clean_data, exécute clean_<champs>() et à la fin clean()
        if form.is_valid():
            Client.objects.create(**form.cleaned_data)
            return redirect('catalog:clients')
    else:
        # En GET j'arrive depuis un lien et je vois le formulaire vierge 
        # form = NouveauClientForm()
        form = ClientForm()

    return render(request, 'catalog/form.html', {
        'form': form
    })

@login_required
@permission_required('catalog.add_client', raise_exception=True)
def nouveau_client(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            # ici forme CONTIENT un objet Modèle !!! qui peut utiliser save() --> create et/ ou  update
            client = form.save()
            return redirect('catalog:clients')
    else:
        form = ClientForm()

    # à partir de deux vues qui pourraient utiliser le template GENERIQUE form.html 
    # on a besoin de variabiliser d'autres éléments
    return render(request, 'catalog/form.html', {
        'form': form,
        'titre': 'Nouveau client',
        'retour': 'catalog:clients'
    })

def modifier_client(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)       # ← la seule différence
        if form.is_valid():
            form.save()
            messages.success(request, f'Client « {client} » modifié.')
            return redirect('catalog:clients')
    else:
        form = ClientForm(instance=client)                     # pré-rempli
    return render(request, 'catalog/form.html', {
        'form': form, 'titre': f'Modifier {client}', 'retour': 'catalog:clients',
    })

@login_required
@permission_required('catalog.delete_client', raise_exception=True)
def supprimer_client(request, pk: int):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        # si le modèle utilise une relation avec contrainte RESTRICT ou PROTECTED en python
        try:
            client.delete()
        except ProtectedError:
            messages.error(request, 'Suppression impossible : ce client a des contrats ou des inscriptions.')
        # else adossé à try/except garantit que le try s'est exécuté jusqu'ou bout ==> pas d'erreur
        else:
            messages.success(request, f'Client « {client} » supprimé.')
        return redirect('catalog:clients')
    return render(request, 'catalog/confirmer_suppression.html', {
        'objet': client, 'retour': 'catalog:clients',
    })

########### version CBV : Class Based View ; Cas suffisamment simples et générique

class ClientUpdateView(SuccessMessageMixin, UpdateView):
    """
    contrepartie en POO de la fonction "modifier_client"
    avec comportement génériques
    - model, form_class, template_name, success_url
    avec customisation directe
    - get_context_data
    avec customisation indirecte avec des Mixins 
       == classe auxiliaire à ajouter en héritage multiple !
    - SuccessMessageMixin.get_success_message
    """
    model = Client
    form_class = ClientForm
    template_name = 'catalog/form.html'
    # -----------> l'url sera redirigée si le formulaire est validé
    success_url = reverse_lazy('catalog:clients')

    def get_context_data(self, **kwargs):
        """
        customisation du contexte pour être compatible avec le template !!
        """
        # super() charge le form dans contexte !
        context = super().get_context_data(**kwargs)
        # ----------------------------> l'objet instancié (client) !
        context["titre"] = f'Modifier {self.get_object()}'
        context["retour"] = 'catalog:clients'
        return context

    def get_success_message(self, cleaned_data):
        """
        méthode héritée de la Mixin SuccessMessageMixin
        pour gérer les messages en succès
        """
        return f'Client « {self.get_object()} » modifié.'


################# INSCRIPTIONS
@login_required
@permission_required('catalog.view_inscription', raise_exception=True)
def liste_inscriptions(request):
    # ------------------------------------------------> 2 joins client et intervention avec leur propre relation formation
    inscriptions = Inscription.objects.select_related('client', 'intervention__formation')
    return render(request, 'catalog/liste_inscriptions.html', {'inscriptions': inscriptions})

@login_required
@permission_required('catalog.add_inscription', raise_exception=True)
def nouvelle_inscription(request):
    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            try:
                inscrire(form.cleaned_data['client'], form.cleaned_data['intervention'])
            except (DejaInscrit, InterventionComplete) as erreur:
                form.add_error(None, str(erreur))          # erreur « de formulaire »
            else:
                messages.success(request, 'Inscription enregistrée.')
                return redirect('catalog:inscriptions')
    else:
        form = InscriptionForm()
    return render(request, 'catalog/form.html', {
        'form': form, 'titre': 'Nouvelle inscription', 'retour': 'catalog:inscriptions',
    })

@login_required
@require_POST
def sinscrire(request, pk):
    intervention = get_object_or_404(Intervention.objects.select_related('formation'), pk=pk, statut='A')
    client = Client.objects.filter(utilisateur=request.user).first()
    if client is None:
        messages.error(request, "Aucun profil client n'est associé à votre compte.")
    else:
        try:
            inscrire(client, intervention)
        except (DejaInscrit, InterventionComplete) as erreur:
            messages.error(request, str(erreur))
        else:
            messages.success(request, f'Inscription à {intervention.formation.nom} enregistrée.')
    return redirect('catalog:detail-formation', pk=intervention.formation_id)

######### gestion authentification

def creer_compte(request):
    if request.method == 'POST':
        form = CompteForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)           # §7.4 : compléter avant d'écrire
            user.email = user.email.lower()
            user.save()
            client, _ = Client.objects.get_or_create(
                email=user.email,
                defaults={'prenom': user.first_name, 'nom': user.last_name},
            )
            if client.utilisateur_id is None:
                client.utilisateur = user
                client.save(update_fields=['utilisateur'])
            login(request, user)                     # connecté dès la création
            messages.success(request, 'Compte créé. Bienvenue !')
            return redirect('catalog:mon-espace')
    else:
        form = CompteForm()
    return render(request, 'catalog/form.html', {
        'form': form, 'titre': 'Créer un compte', 'retour': 'catalog:accueil',
    })

@login_required
def mon_espace(request):
    # -----------------------------------------> utilisateur loggé
    client = Client.objects.filter(utilisateur=request.user).first()
    inscriptions = (
        Inscription.objects
        .filter(client__utilisateur=request.user)        # ← la propriété est dans la requête
        .select_related('intervention__formation')
    )
    return render(request, 'catalog/mon_espace.html', {
        'client': client, 'inscriptions': inscriptions,
    })
