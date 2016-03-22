from canvas_oauth.exceptions import (
    MissingTokenError, InvalidTokenError, CanvasOAuthError)
from canvas_oauth.oauth import (
    handle_missing_token, handle_invalid_token, render_oauth_error)


class OAuthMiddleware(object):
    """On catching a MissingTokenError - as is raised by the get_token function
    if there is no cached token for the user - this begins the oauth dance with
    canvas to get a new token.  An InvalidTokenError indicates that the user's
    token has expired, so in this case we request a refresh token from Canvas
    and reprocess the request.  An InvalidTokenError is expected to be raised
    by the consuming library if an API request returns a 401 with a
    WWW-Authenticate header (to distinguish from API requests where the user is
    simply unauthorized to perform the action).  For other CanvasOAuthErrors,
    we render an error page with the exception text."""
    def process_exception(self, request, exception):
        if isinstance(exception, MissingTokenError):
            return handle_missing_token(request)
        elif isinstance(exception, InvalidTokenError):
            return handle_invalid_token(request)
        elif isinstance(exception, CanvasOAuthError):
            return render_oauth_error(str(exception))
        return
