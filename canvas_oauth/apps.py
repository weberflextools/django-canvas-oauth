from __future__ import unicode_literals
from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class CanvasOauthConfig(AppConfig):
    name = 'canvas_oauth'
    verbose_name = 'Django Canvas OAuth'


    def ready(self):
        for oauth_setting in ('CANVAS_OAUTH_CLIENT_ID',
                              'CANVAS_OAUTH_CLIENT_SECRET',
                              'CANVAS_OAUTH_CANVAS_FQDN'):
            if not hasattr(settings, oauth_setting):
                raise ImproperlyConfigured('Missing %s setting that is required to use the DJango Canvas OAuth library' %
                                           oauth_setting)
