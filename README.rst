.. figure:: ./coverage.svg
   :alt: Coverage Status

============
Django Canvas OAuth
============

**Django Canvas OAuth** is a Django app that manages OAuth2 Tokens used to make API calls against a Canvas LMS instance.  

The `OAuth workflow`_ is managed by this library and a CanvasOAuth2Token model is used to store authenticated tokens. 

Tokens are short-lived, so some logic is introduced at the point of retrieving the the stored token to capture and handle the necessary refresh calls.

.. _OAuth workflow: https://canvas.instructure.com/doc/api/file.oauth.html

Installation
------------

Requires python >= 3.6 and Django >= 2.0

.. code-block:: bash

    pip install git+https://github.com/Harvard-University-iCommons/django-canvas-oauth.git#egg=canvas-oauth


Quickstart
----------

1. Add "canvas_oauth" to your INSTALLED_APPS setting like this::

.. code-block:: python
    
    INSTALLED_APPS = [
        # ...
        'canvas_oauth.apps.CanvasOAuthConfig',
    ]

2. Include the canvas_oauth URLconf in your project urls.py like this::

.. code-block:: python

    path('oauth/', include('canvas_oauth.urls')),

3. Install middleware to begin the oauth2 dance when a token is not
   present and to consume any errors encountered by the library.

.. code-block:: python
    
    MIDDLEWARE = [
        # ...
        'canvas_oauth.middleware.OAuthMiddleware',
    ]

4. Run ``python manage.py migrate`` to create the canvas_oauth models.

5. Use the ``get_oauth_token`` method from ``canvas_oauth.oauth`` to obtain a 
   token. This method contains all of the logic to obtain a new token, refresh 
   an expired one, or return an existing one.

.. code-block:: python

    from canvas_oauth.oauth import get_oauth_token
    
    access_token = get_oauth_token(request)
    #  Make request to the Canvas API using above token.


Settings
---------

Settings should be added to your django settings module (e.g. ``settings.py``).


CANVAS_OAUTH_CLIENT_ID:
    (required) The client id is the integer client id value of your Canvas developer key. 

CANVAS_OAUTH_CLIENT_SECRET:
    (required) The client secret is the random string (secret) value of your Canvas developer key.

CANVAS_OAUTH_CANVAS_DOMAIN:
    (required) The domain of your canvas instance (e.g. canvas.instructure.com)

CANVAS_OAUTH_TOKEN_EXPIRATION_BUFFER:
    Specify an earlier token expiration as a ``datetime.timedelta``. Defaults to ``timedelta(0)``.

CANVAS_OAUTH_ERROR_TEMPLATE:
    Specify a template for rendering errors that occur in the authorization flow. Defaults to ``oauth_error.html``.



Usage
------

Wherever you are making API requests in your code, use the ``get_oauth_token`` method to retrieve a token.

Example:

.. code-block:: python

    from canvas_oauth.oauth import get_oauth_token

    @login_required
    def index(request):
        access_token = get_oauth_token(request)
        #  Make request to the Canvas API using above token.

**Implementation notes:**

- The ``get_oauth_token`` assumes that ``request.user`` is authenticated.
- The ``get_oauth_token`` method will raise an ``MissingTokenError`` exception if no token is present (e.g. new user). The exception is handled by the middleware, which then initiates the Oauth2 flow. The user will be returned to the original view once the authorization completes successfully.
- The ``get_oauth_token`` method automatically refreshes expired tokens. By default, the token is not refreshed until it has fully expired. However, you can force the token to refresh earlier by configuring an expiration buffer period (defined as a timedelta by the consuming project).

**Best practices:**

- Avoid storing the access token in a session to use across views. If you do so, your application will be responsible for handling invalid token errors that may arise when the token expires.


Development
-----------

Setup environment:

.. code-block:: bash

    $ python3 -m venv ~/.virtualenvs/django-canvas-oauth
    $ source ~/.virtualenvs/django-canvas-oauth/bin/activate
    $ pip install -r requirements-dev.txt

To run tests in your venv:

.. code-block:: bash

    $ python run_tests.py

Or to run tests against multiple versions of python and django use tox_:

.. code-block:: bash

    $ tox
    $ tox -e flake8 

.. _tox: https://tox.readthedocs.io/

To update the coverage badge:

.. code-block:: bash

    $ coverage run --source='.' run_tests.py
    $ coverage-badge -f -o coverage.svg
