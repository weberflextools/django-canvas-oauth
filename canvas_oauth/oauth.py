import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.template import loader
from django.template.exceptions import TemplateDoesNotExist
from django.utils.crypto import get_random_string

from canvas_oauth import canvas
from canvas_oauth.models import CanvasOAuthToken
from canvas_oauth.exceptions import (
    MissingTokenError, InvalidOAuthStateError)

logger = logging.getLogger(__name__)

OAUTH_ERROR_TEMPLATE = "oauth_error.html"
if hasattr(settings, "CANVAS_OAUTH_ERROR_TEMPLATE"):
    OAUTH_ERROR_TEMPLATE = settings.CANVAS_OAUTH_ERROR_TEMPLATE


def get_oauth_token(request):
    """Retrieve an OAuth token for the user if one exists already.

    If there isn't one, it raises a MissingTokenError exception.  If this
    happens inside a view, this exception will be handled by the
    django_canvas_oauth middleware to call handle_missing_token.  If this
    happens outside of a view, then there is no token available for
    that user and they must be directed to the site to authorize a token.
    """
    try:
        return request.user.canvas_oauth_token.access_token
    except CanvasOAuthToken.DoesNotExist:
        """ If this exception is raised by a view function and not caught,
        it is probably because the oauth_middleware is not installed, since it
        is supposed to catch this error."""
        raise MissingTokenError("No token found for user %s" % request.user.pk)


def handle_missing_token(request):
    """Redirect user to canvas with a request for token.

    """
    # Store where the user came from so they can be redirected back there
    # at the end.  https://canvas.instructure.com/doc/api/file.oauth.html
    request.session["canvas_oauth_initial_uri"] = request.get_full_path()

    # The request state is a recommended security check on the callback, so
    # store in session for later
    oauth_request_state = get_random_string()
    request.session["canvas_oauth_request_state"] = oauth_request_state

    # The return URI is required to be the same when POSTing to generate
    # a token on callback, so also store it in session (although it could
    # be regenerated again via the same method call).
    oauth_redirect_uri = request.build_absolute_uri(
        reverse('canvas-oauth-callback'))
    request.session["canvas_oauth_redirect_uri"] = oauth_redirect_uri

    authorize_url = canvas.get_oauth_login_url(
        settings.CANVAS_OAUTH_CLIENT_ID,
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

    access_token, refresh_token, _ = canvas.get_access_token(
        grant_type='authorization_code',
        client_id=settings.CANVAS_OAUTH_CLIENT_ID,
        client_secret=settings.CANVAS_OAUTH_CLIENT_SECRET,
        redirect_uri=request.session["canvas_oauth_redirect_uri"],
        code=code)

    CanvasOAuthToken.objects.create(user=request.user,
                                    access_token=access_token,
                                    refresh_token=refresh_token)
    return redirect(request.session['canvas_oauth_initial_uri'])


def handle_invalid_token(request):
    oauth_token_model = request.user.canvas_oauth_token

    # Assign the new access token to the user model
    oauth_token_model.access_token, _, _ = canvas.get_access_token(
        grant_type='refresh_token',
        client_id=settings.CANVAS_OAUTH_CLIENT_ID,
        client_secret=settings.CANVAS_OAUTH_CLIENT_SECRET,
        redirect_uri=request.session["canvas_oauth_redirect_uri"],
        refresh_token=oauth_token_model.refresh_token)

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
