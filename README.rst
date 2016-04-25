============
Django Canvas OAuth
============

Django Canvas OAuth is a Django app that manages OAuth2 Tokens used to make API calls against a Canvas LMS instance.  The OAuth workflow is managed by this library and a CanvasOAuth2Token model is used to store authenticated tokens. Tokens are short-lived, so some logic is introduced at the point of retrieving the the stored token to capture and handle the necessary refresh calls.


Quick start
-----------

1. Add "canvas_oauth" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'canvas_oauth.apps.CanvasOAuthConfig',
    ]

2. Include the canvas_oauth URLconf in your project urls.py like this::

    url(r'^oauth/', include('canvas_oauth.urls')),

3. Install middleware to begin the oauth2 dance when a token is not
   present and to consume any errors encountered by the library.

   MIDDLEWARE_CLASSES = [
    ...
    'canvas_oauth.middleware.OAuthMiddleware'
   ]

4. Run `python manage.py migrate` to create the canvas_oauth models.

5. Wherever you are making API requests in your code, start out by
   calling the `get_oauth_token` method in the library's oauth module,
   i.e.:

   from canvas_oauth.oauth import get_oauth_token

   ...
   access_token = get_oauth_token(request)
   #  Make request to the Canvas API using above token.

NOTE: the `get_token` method will raise an `MissingTokenError` exception if
no token is present, as would be the case when a new user calls your app.
There is logic within the `get_oauth_token` method that checks for and refreshes expired tokens, and even allows for a user-defined expiration buffer (defined as a timedelta by the consuming project).  It's recommended to not store the access token in session for requests across view methods.  Application that do so will be responsible for handling invalid token errors that may arise if the access token being used has expired.
