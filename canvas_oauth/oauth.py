import requests
import logging
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.template import loader
from django.template.exceptions import TemplateDoesNotExist
from django.utils.crypto import get_random_string
from canvas_oauth.models import CanvasOAuthToken
from canvas_oauth.exceptions import (MissingTokenError,
    InvalidOAuthStateError, InvalidOAuthReturnError)

logger = logging.getLogger(__name__)

AUTHORIZE_URL_PATTERN = "https://%s/login/oauth2/auth"
ACCESS_TOKEN_URL_PATTERN = "https://%s/login/oauth2/token"
OAUTH_ERROR_TEMPLATE = "oauth_error.html"
if hasattr(settings, "CANVAS_OAUTH_ERROR_TEMPLATE"):
    OAUTH_ERROR_TEMPLATE = settings.CANVAS_OAUTH_ERROR_TEMPLATE


def _build_auth_url(client_id, redirect_uri, response_type='code', state=None,
                    scopes=None, purpose=None, force_login=None):
    """Build an OAuth request url for Canvas.

    With the parameters as defined here ().

    """
    authorize_url = AUTHORIZE_URL_PATTERN % settings.CANVAS_OAUTH_CANVAS_FQDN

    auth_request_params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': response_type,
        'state': state,
        'scopes': scopes,
        'purpose': purpose,
        'force_login': force_login,
    }
    # Use requests library to help build our url
    auth_request = requests.Request('GET', authorize_url,
                                    params=auth_request_params)
    # Prepared request url uses urlencode for encoding and scrubs any None
    # key-value pairs
    return auth_request.prepare().url


def get_oauth_token(request):
    """Retrieve an OAuth token for the user if one exists already.

    If there isn't one, it raises a NewTokenNeeded exception.  If this
    happens inside a view, this exception will be handled by the
    django_canvas_oauth middleware to call begin_oauth.  If this
    happens outside of a view, then there is no token available for
    that user and they must be directed to the site to authorize a token.
    """
    try:
        return request.user.canvas_oauth_token.access_token
    except CanvasOAuthToken.DoesNotExist:
        """ If this exception is raised by a view function and not caught,
        it is probably because the oauth_middleware is not installed, since it
        is supposed to catch this error."""
        raise MissingTokenError("No token found for user id %s" % request.user.pk)


def begin_oauth(request):
    """Redirect user to canvas with a request for token.

    Stores where the user came from so they can be redirected back there at the
    end.  https://canvas.instructure.com/doc/api/file.oauth.html
    """
    oauth_request_state = get_random_string()  # OAuth request security
    request.session["canvas_oauth_return_uri"] = request.get_full_path()
    request.session["canvas_oauth_request_state"] = oauth_request_state
    oauth_redirect_uri = request.build_absolute_uri(reverse('canvas-oauth-callback'))
    authorize_url = _build_auth_url(settings.CANVAS_OAUTH_CLIENT_ID,
                                    redirect_uri=oauth_redirect_uri,
                                    state=oauth_request_state)
    return HttpResponseRedirect(authorize_url)


def oauth_callback(request):
    """ Receives the callback from canvas and saves the token to the database.
        Redirects user to the page they came from at the start of the oauth
        procedure. """
    error = request.GET.get('error')
    if error:
        return render_oauth_error(error)
    code = request.GET.get('code')
    state = request.GET.get('state')

    if state != request.session['canvas_oauth_request_state']:
        raise InvalidOAuthStateError("OAuth state mismatch!")

    access_token, refresh_token, _ = get_access_token_response(request, code)

    CanvasOAuthToken.objects.create(user=request.user,
                                    access_token=access_token,
                                    refresh_token=refresh_token)
    return redirect(request.session['canvas_oauth_return_uri'])


def get_access_token_response(request, code):
    resp = _get_token_post_response(request, 'access_token', code=code)
    access_token = resp['access_token']
    refresh_token = resp['refresh_token']
    expires_in = resp['expires_in']
    return access_token, refresh_token, expires_in


def get_refresh_token_response(request, token):
    resp = _get_token_post_response(request, 'refresh_token', refresh_token=token)
    access_token = resp['access_token']
    expires_in = resp['expires_in']
    return access_token, expires_in


def _get_token_post_response(request, grant_type, code=None, refresh_token=None):
    # Call Canvas endpoint to
    oauth_token_url = ACCESS_TOKEN_URL_PATTERN % settings.CANVAS_OAUTH_CANVAS_FQDN
    post_params = {
        'grant_type': grant_type,  # Use 'authorization_code' for new tokens
        'client_id': settings.CANVAS_OAUTH_CLIENT_ID,
        'client_secret': settings.CANVAS_OAUTH_CLIENT_SECRET,
        'redirect_uri': request.build_absolute_uri(reverse('canvas-oauth-callback')),
    }

    if grant_type == 'authorization_code':
        post_params['code'] = code
    else:
        post_params['refresh_token'] = refresh_token

    r = requests.post(oauth_token_url, post_params)
    if r.status_code != 200:
        raise InvalidOAuthReturnError("failed to retrieve token: %s" % r.text)

    logger.info("%s POST response from Canvas is %s", grant_type, r.text)
    response_data = r.json()

    return response_data


def process_refresh_token(request):
    oauth_token_model = request.user.canvas_oauth_token

    # Assign the new access and refresh tokens to the user's oauth_token
    oauth_token_model.access_token, _ = get_refresh_token_response(
        request, oauth_token_model.refresh_token)

    oauth_token_model.save()  # Update the token

    # Send user back to the prior request
    return redirect(request.get_full_path())


def render_oauth_error(error_message):
    """ If there is an error in the oauth callback, attempts to render it in a
        template that can be styled; otherwise, if OAUTH_ERROR_TEMPLATE not
        found, this will return a HttpResponse with status 403 """
    try:
        template = loader.render_to_string(OAUTH_ERROR_TEMPLATE,
                                           {"message": error_message})
    except TemplateDoesNotExist:
        return HttpResponse("Error: %s" % error_message, status=403)
    return HttpResponse(template, status=403)
