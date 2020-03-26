from django.test import TestCase
from django.test.client import RequestFactory
from django.http import HttpResponse
from unittest.mock import patch

from canvas_oauth.middleware import OAuthMiddleware
from canvas_oauth.exceptions import MissingTokenError, CanvasOAuthError


def dummy_response(request):
    return HttpResponse("Dummy")


class TestOAuthMiddleware(TestCase):

    def test_without_triggering_oauth_flow(self):
        request = RequestFactory().get('/index')
        middleware = OAuthMiddleware(dummy_response)
        response = middleware(request)
        expected_response = dummy_response(request)
        self.assertEqual(expected_response.status_code, response.status_code)
        self.assertEqual(expected_response.content, response.content)

    @patch('canvas_oauth.middleware.handle_missing_token')
    def test_missing_token_error(self, mock_handle_missing_token):
        request = RequestFactory().get('/index')
        exception = MissingTokenError()
        middleware = OAuthMiddleware(dummy_response)
        middleware.process_exception(request, exception)
        mock_handle_missing_token.assert_called_with(request)

    @patch('canvas_oauth.middleware.render_oauth_error')
    def test_canvas_oauth_error(self, mock_render_oauth_error):
        request = RequestFactory().get('/index')
        exception = CanvasOAuthError("Authorization denied")
        middleware = OAuthMiddleware(dummy_response)
        middleware.process_exception(request, exception)
        mock_render_oauth_error.assert_called_with(str(exception))
