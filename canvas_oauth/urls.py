from django.urls import re_path
from .oauth import oauth_callback

urlpatterns = [
    re_path(r'^oauth-callback$', oauth_callback, name='canvas-oauth-callback'),
]
