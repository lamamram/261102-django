from django.shortcuts import render, get_object_or_404
from django.http import HttpRequest, HttpResponse
from .models import Formation

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

    return render(request, "catalog/detail_formation.html" , {
        "formation": formation, 
        "competences": competences
    })

def page_introuvable(request, exception):
    """
    page rendue par le handler404 du projet
    le handler 404 demande un 2ème paramètre exception dans la vue
    """
    return render(request, "catalog/404.html", status=404)

def interne(request):
    return render(request, "catalog/500.html", status=500)