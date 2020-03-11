from django.test import TestCase
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from contextlib import contextmanager
import importlib
import datetime


CANVAS_OAUTH_SETTINGS_MODULE_NAME = "canvas_oauth.settings"


@contextmanager
def required_oauth_settings(oauth_settings={}):
    settings.CANVAS_OAUTH_CLIENT_ID = oauth_settings.get('CANVAS_OAUTH_CLIENT_ID', '10000000000012')
    settings.CANVAS_OAUTH_CLIENT_SECRET = oauth_settings.get('CANVAS_OAUTH_CLIENT_SECRET', 'yKZc1bJpdykVBUT4')
    settings.CANVAS_OAUTH_CANVAS_DOMAIN = oauth_settings.get('CANVAS_OAUTH_CANVAS_DOMAIN', 'canvas.localhost')
    yield
    delattr(settings, 'CANVAS_OAUTH_CLIENT_ID')
    delattr(settings, 'CANVAS_OAUTH_CLIENT_SECRET')
    delattr(settings, 'CANVAS_OAUTH_CANVAS_DOMAIN')


class TestCanvasOauthSettings(TestCase):

    def test_required_settings_raises_exception(self):
        with self.assertRaises(ImproperlyConfigured):
            canvas_oauth_settings = importlib.import_module(CANVAS_OAUTH_SETTINGS_MODULE_NAME)
            canvas_oauth_settings = importlib.reload(canvas_oauth_settings)

    def test_settings_are_present(self):
        with required_oauth_settings():
            canvas_oauth_settings = importlib.import_module(CANVAS_OAUTH_SETTINGS_MODULE_NAME)
            canvas_oauth_settings = importlib.reload(canvas_oauth_settings)
            self.assertTrue(hasattr(canvas_oauth_settings, 'CANVAS_OAUTH_CLIENT_ID'))
            self.assertTrue(hasattr(canvas_oauth_settings, 'CANVAS_OAUTH_CLIENT_SECRET'))
            self.assertTrue(hasattr(canvas_oauth_settings, 'CANVAS_OAUTH_CANVAS_DOMAIN'))
            self.assertTrue(hasattr(canvas_oauth_settings, 'CANVAS_OAUTH_TOKEN_EXPIRATION_BUFFER'))
            self.assertTrue(hasattr(canvas_oauth_settings, 'CANVAS_OAUTH_ERROR_TEMPLATE'))

    def test_optional_oauth_token_expiration_buffer_default_value(self):
        with required_oauth_settings():
            canvas_oauth_settings = importlib.import_module(CANVAS_OAUTH_SETTINGS_MODULE_NAME)
            canvas_oauth_settings = importlib.reload(canvas_oauth_settings)
            self.assertTrue(hasattr(canvas_oauth_settings, 'CANVAS_OAUTH_TOKEN_EXPIRATION_BUFFER'))
            self.assertEqual(datetime.timedelta(0), canvas_oauth_settings.CANVAS_OAUTH_TOKEN_EXPIRATION_BUFFER)

    def test_optional_oauth_error_template_default_value(self):
        with required_oauth_settings():
            canvas_oauth_settings = importlib.import_module(CANVAS_OAUTH_SETTINGS_MODULE_NAME)
            canvas_oauth_settings = importlib.reload(canvas_oauth_settings)
            self.assertTrue(hasattr(canvas_oauth_settings, 'CANVAS_OAUTH_ERROR_TEMPLATE'))
            self.assertEqual('oauth_error.html', canvas_oauth_settings.CANVAS_OAUTH_ERROR_TEMPLATE)
