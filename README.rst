============
Django Canvas OAuth
============

Django Canvas OAuth is a Django app that manages OAuth2 Tokens used to make API
calls against a Canvas LMS instance.  The OAuth workflow is managed by this
library and a CanvasOAuthToken model is used to store authenticated tokens.
Tokens are short-lived, so some middleware is introduced to capture and handle the
necessary refresh calls.


Quick start
-----------

1. Add "canvas_oauth" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'canvas_oauth.apps.CanvasOAuthConfig',
    ]

2. Include the canvas_oauth URLconf in your project urls.py like this::

    url(r'^oauth/', include('canvas_oauth.urls')),

3. Install middleware to either begin the oauth dance when a token is not
   present or to use the refresh token to get a new access token.

   MIDDLEWARE_CLASSES = [
    ...
    'canvas_oauth.middleware.OAuthMiddleware'
   ]

4. Run `python manage.py migrate` to create the canvas_oauth models.

5. Wherever you are making API requests in your code, start out by calling
   the `get_token` method in the library's oauth module, i.e.:

   from canvas_oauth.oauth import get_token

   ...
   access_token = get_token(request)
   #  Make request to the Canvas API using above token.

NOTE: the `get_token` method will raise an `MissingTokenError` exception if
no token is present, as would be the case when a new user calls your app.
Your application is responsible, however, for raising an `InvalidTokenError`
if the response from a Canvas API call is a 401 with a `WWW-Authenticate`
header.  That will trigger a request to replace the user's access token by
using the refresh token, and the previous request is tried again.  It's very
important that the token response from `get_token` not be saved to session so
that a refreshed access token can be retrieved from the model on subsequent
calls.
