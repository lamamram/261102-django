from django.shortcuts import render
from django.http import HttpRequest, HttpResponse

# --- données fictives pour le jour 1 (elles seront remplacées par l'ORM le jour 2) ---
FORMATIONS = [
    {'code': 'PY-101', 'nom': 'Django : initiation',
     'prix': 1890.0, 'duree': 3, 'public': 'Développeurs', 'nouveaute': False},
    {'code': 'PY-102', 'nom': 'Django : approfondissement',
     'prix': 2490.0, 'duree': 1, 'public': '', 'nouveaute': False},
    {'code': 'DA-201', 'nom': 'Data analysis with Python',
     'prix': 2190.0, 'duree': 5, 'public': 'Analystes', 'nouveaute': True},
]

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
    return render(request, "catalog/liste_formations.html" , {"formations": FORMATIONS})

def detail_formation(request: HttpRequest, pk: int) -> HttpResponse:
    """
    détail d'une formation indexée par un id, par défaut l'indice de la liste
    """
    return render(request, "catalog/detail_formation.html" , {"formation": FORMATIONS[int(pk) - 1]})

