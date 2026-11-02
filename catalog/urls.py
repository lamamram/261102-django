from django.contrib import admin
from django.urls import path
# ne fonctionne pas depuis la racine
# import views
from . import views 

urlpatterns = [
    # ces chemins sont la continuation de la partie du gesti/urls.py
    # un vue est un CALLABLE (fonction ou classe)
    path('', views.accueil)
]