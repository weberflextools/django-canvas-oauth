import logging

import requests
from django.conf import settings

from canvas_oauth.exceptions import InvalidOAuthReturnError

logger = logging.getLogger(__name__)

AUTHORIZE_URL_PATTERN = "https://%s/login/oauth2/auth"
ACCESS_TOKEN_URL_PATTERN = "https://%s/login/oauth2/token"


def get_oauth_login_url(client_id, redirect_uri, response_type='code',
                        state=None, scopes=None, purpose=None,
                        force_login=None):
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


def get_access_token(grant_type, client_id, client_secret, redirect_uri,
                     code=None, refresh_token=None):
    # Call Canvas endpoint to
    oauth_token_url = ACCESS_TOKEN_URL_PATTERN % settings.CANVAS_OAUTH_CANVAS_FQDN
    post_params = {
        'grant_type': grant_type,  # Use 'authorization_code' for new tokens
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
    }

    # Need to add in code or refresh_token, depending on the grant_type
    if grant_type == 'authorization_code':
        post_params['code'] = code
    else:
        post_params['refresh_token'] = refresh_token

    r = requests.post(oauth_token_url, post_params)
    logger.info("%s POST response from Canvas is %s", grant_type, r.text)
    if r.status_code != 200:
        raise InvalidOAuthReturnError("%s request failed to get a token: %s" % (
            grant_type, r.text))

    # Parse the response for the access_token, expiration time, and (possibly)
    # the refresh token
    response_data = r.json()
    access_token = response_data['access_token']
    expires_in = response_data['expires_in']
    # Whether a refresh token is included in the response depends on the
    # grant_type - it only appears to be returned for 'authorization_code',
    # but to be safe check the response_data for it
    refresh_token = ''
    if 'refresh_token' in response_data:
        refresh_token = response_data['refresh_token']

    return (access_token, refresh_token, expires_in)
