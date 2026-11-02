from django.shortcuts import render
from django.http import HttpRequest, HttpResponse

# Create your views here.
def accueil(request: HttpRequest) -> HttpResponse:
    """
    Page d'accueil - réponse brute
    demande un objet request de type HttpRequest
    et retourne un objet HttpResponse
    """
    return HttpResponse("""<h1>GestiFormation</h1>
    <p>Gestion d'un organisme de formation : catalogue, sessions, inscriptions.</p>
    <a href="/formations/">Voir le catalogue</a>""",content_type="text/html")