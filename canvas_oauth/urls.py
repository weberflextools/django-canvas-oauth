from django.conf.urls import url
from oauth import oauth_callback

urlpatterns = [
    url(r'^canvas_redirect$', oauth_callback, name='canvas-oauth-callback'),
]
