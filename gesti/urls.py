"""
URL configuration for gesti project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import path, include
# pas d'import relatif ni absolu car le dossier racine n'est PAS un package
# import catalog.urls 

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')), # set_language (POST)
    # hors i18n_patterns : l'URL de retour (callback) enregistrée chez GitHub/Google ne doit pas changer avec la langue
    path('accounts/', include('allauth.urls')),
]

urlpatterns += i18n_patterns(
    # ce chemin permet de consulter les urls de 
    # l'application admin déjà installé dans settings INSTALLED_APPS
    path('admin/', admin.site.urls),
    path('comptes/', include('django.contrib.auth.urls')), # contiennent login, logout, password_change ...
    # => catalog/urls.py
    path('', include('catalog.urls')),
) 
# settings_prod: pas de debug_toolbar
if 'debug_toolbar' in settings.INSTALLED_APPS:
    from debug_toolbar.toolbar import debug_toolbar_urls
    urlpatterns += debug_toolbar_urls()

# gestion != d'urlpatterns
# pour le voir ==> DEBUG = False
handler404 = 'catalog.views.page_introuvable'
handler500 = 'catalog.views.interne'
handler403 = 'catalog.views.acces_refuse'
