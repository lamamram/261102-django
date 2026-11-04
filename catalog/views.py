from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpRequest, HttpResponse
from .models import Formation, Intervention, Client
from .forms import NouveauClientForm, ClientForm
from django.db.models import Q

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