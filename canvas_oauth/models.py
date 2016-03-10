from __future__ import unicode_literals

from django.db import models
from django.conf import settings


class CanvasOAuthToken(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='canvas_oauth_token',
    )
    access_token = models.TextField()
    refresh_token = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
