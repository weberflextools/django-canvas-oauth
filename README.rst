============
Canvas OAuth
============

Canvas OAuth is a Django app that manages OAuth2 Tokens used to make API calls
against a Canvas LMS instance.  The OAuth workflow is managed by this library
and a CanvasOAuthToken model is used to store authenticated tokens.  Tokens are
short-lived, so some middleware is introduced to capture and handle the 
necessary refresh call.s


Quick start
-----------

1. Add "canvas_oauth" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'canvas_oauth',
    ]

2. Include the canvas_oauth URLconf in your project urls.py like this::

    url(r'^oauth/', include('canvas_oauth.urls')),

3. Install middleware?

4. Run `python manage.py migrate` to create the canvas_oauth models.
