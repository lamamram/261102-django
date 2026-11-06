from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class CompteAdapter(DefaultAccountAdapter):
    """Les comptes locaux se créent par notre vue `creer_compte`, pas par les pages d'allauth."""

    def is_open_for_signup(self, request):
        return False


class SocialAdapter(DefaultSocialAccountAdapter):
    """L'inscription par un fournisseur (GitHub, Google) reste ouverte."""

    def is_open_for_signup(self, request, sociallogin):
        return True
