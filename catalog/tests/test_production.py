# catalog/tests/test_production.py
import importlib
import sys
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

ENV_VALIDE = {
    'SECRET_KEY': 'cle-factice',
    'ALLOWED_HOSTS': 'formation.example.org, www.example.org',
    'DATABASE_URL': 'postgres://gesti:pw@db:5432/gesti',
}


def charger_settings_prod(env):
    """Réimporte gesti.settings_prod avec un environnement donné (le module lit os.environ à l'import)."""
    sys.modules.pop('gesti.settings_prod', None)
    with patch.dict('os.environ', env, clear=True):
        return importlib.import_module('gesti.settings_prod')


class SettingsProdTests(SimpleTestCase):
    def test_durcissement(self):
        s = charger_settings_prod(ENV_VALIDE)
        self.assertFalse(s.DEBUG)
        self.assertEqual(s.ALLOWED_HOSTS, ['formation.example.org', 'www.example.org'])
        self.assertTrue(s.SECURE_SSL_REDIRECT)
        self.assertTrue(s.SESSION_COOKIE_SECURE)
        self.assertTrue(s.CSRF_COOKIE_SECURE)
        self.assertGreater(s.SECURE_HSTS_SECONDS, 0)

    def test_les_outils_de_developpement_sont_retires(self):
        s = charger_settings_prod(ENV_VALIDE)
        self.assertNotIn('debug_toolbar', s.INSTALLED_APPS)
        self.assertNotIn('django_extensions', s.INSTALLED_APPS)
        self.assertFalse([m for m in s.MIDDLEWARE if 'debug_toolbar' in m])

    def test_whitenoise_suit_le_middleware_de_securite(self):
        s = charger_settings_prod(ENV_VALIDE)
        self.assertEqual(s.MIDDLEWARE[:2], ['django.middleware.security.SecurityMiddleware', 'whitenoise.middleware.WhiteNoiseMiddleware'])

    def test_la_base_vient_de_l_environnement(self):
        base = charger_settings_prod(ENV_VALIDE).DATABASES['default']
        self.assertEqual((base['HOST'], base['NAME'], base['USER']), ('db', 'gesti', 'gesti'))

    def test_chaque_variable_obligatoire_est_exigee(self):
        for manquante in ENV_VALIDE:
            with self.subTest(variable=manquante):
                env = {k: v for k, v in ENV_VALIDE.items() if k != manquante}
                with self.assertRaisesMessage(ImproperlyConfigured, manquante):
                    charger_settings_prod(env)

    def tearDown(self):
        sys.modules.pop('gesti.settings_prod', None)
