from django.contrib import admin
from django.urls import path, re_path
# ne fonctionne pas depuis la racine
# import views
from . import views 

# espace de nom des urls de cette app à appeler dans les templates et/ou les vues
app_name = "catalog"

urlpatterns = [
    # ces chemins sont la continuation de la partie du gesti/urls.py
    # un vue est un CALLABLE (fonction ou classe)
    path('', views.accueil),
    path('formations/', views.liste_formations, name="liste-formations"),

    # l'attribut name fait le lien entre l'url et son invocation dans un template et/ou dans une vue
    path('formations/<int:pk>', views.detail_formation, name="detail-formation"),
    
    
    
    # exemple de route matchée par une regex
    
    # django réutilise le mécnisme de nommage de groupe de capture du module 
    # re en python (?P<name>) pour dynamiser l'identifiant
    
    # non-obstant, la valeur capturée est une str !!!

    # re_path utilise re.match ==> capture au début de la cible
    # ==> écrire des regex stricte : ^<regex>$
    # re_path("^formations/(?P<pk>[0-9]{,2})$", views.detail_formation)
]