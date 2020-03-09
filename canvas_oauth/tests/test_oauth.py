import logging
from django.test import TestCase
from django.test.client import RequestFactory
from django.utils import timezone
from django.urls import reverse
from django.http import HttpResponseRedirect
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, PropertyMock, patch

from canvas_oauth import settings
from canvas_oauth.models import CanvasOAuth2Token
from canvas_oauth.exceptions import InvalidOAuthStateError, MissingTokenError
from canvas_oauth.canvas import get_oauth_login_url
from canvas_oauth.oauth import (
    get_oauth_token,
    handle_missing_token,
     oauth_callback,
    refresh_oauth_token, 
    render_oauth_error)


logging.disable(logging.CRITICAL) # disable logging for anything less than critical

class StubCanvasOAuth2Token(object):
    # TODO: figure out better way to stub this
    def __init__(self, access_token, refresh_token, expires):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires = expires

        # internal to stub
        self._save_called = False
        self._expires_within_return_value = False
        self._expires_within_delta = None

    def save(self):
        self._called_save_method = True
    
    def expires_within(self, delta):
        self._expires_within_delta = delta
        return self._expires_within_return_value

    def stub_save_called(self):
        return bool(self._called_save_method)
    
    def stub_expires_within_return_value(self, return_value):
        self._expires_within_return_value = return_value

    def stub_expires_within_called_with(self, delta):
        return self._expires_within_delta == delta



class TestRefreshOauthToken(TestCase):

    @patch('canvas_oauth.oauth.canvas.get_access_token')
    def test_refresh_oauth_token(self, mock_get_access_token):
        refresh_token = "refresh-token"
        old_access_token = "old-access-token"
        old_expires = timezone.now() + timedelta(seconds=100)
        new_access_token = "new-access-token"
        new_expires = old_expires + timedelta(seconds=100)

        # mock the get_access_token() function
        mock_get_access_token.return_value = (new_access_token, new_expires, refresh_token)

        # mock the user and related CanvasOAuth2Token model
        stub_canvas_oauth2_token = StubCanvasOAuth2Token(old_access_token, refresh_token, old_expires)
        mock_user = MagicMock()
        type(mock_user).canvas_oauth2_token = PropertyMock(return_value=stub_canvas_oauth2_token)

        # initialize request object
        request = RequestFactory().get('/index')
        request.user = mock_user

        # run tests
        actual_oauth_token = refresh_oauth_token(request)

        self.assertEqual(refresh_token, actual_oauth_token.refresh_token)
        self.assertEqual(new_access_token, actual_oauth_token.access_token)
        self.assertEqual(new_expires, actual_oauth_token.expires)

        mock_get_access_token.assert_called_with(
            grant_type='refresh_token',
            client_id=settings.CANVAS_OAUTH_CLIENT_ID,
            client_secret=settings.CANVAS_OAUTH_CLIENT_SECRET,
            redirect_uri=request.build_absolute_uri(reverse('canvas-oauth-callback')),
            refresh_token=refresh_token)

        self.assertTrue(stub_canvas_oauth2_token.stub_save_called())


class TestOauthCallback(TestCase):

    @patch('canvas_oauth.oauth.render_oauth_error')
    def test_oauth_callback_has_error(self, mock_render_oauth_error):
        error = "access_denied"
        rf = RequestFactory()
        request = rf.get('/index', data={"error": error})
        oauth_callback(request)
        mock_render_oauth_error.assert_called_with(error)

    def test_oauth_callback_state_mismatch(self):
        request_state = "RandomState100"

        rf = RequestFactory()
        query_params = {"code": "blue", "state": request_state + "XYZ"}
        request = rf.get('/index', data=query_params)
        request.session = {'canvas_oauth_request_state': request_state}

        with self.assertRaises(InvalidOAuthStateError) as cm:
            oauth_callback(request)
        self.assertEqual("OAuth state mismatch!", str(cm.exception))

    @patch('canvas_oauth.oauth.CanvasOAuth2Token.objects.create')
    @patch('canvas_oauth.oauth.canvas.get_access_token')
    def test_oauth_callback_succes(self, mock_get_access_token, mock_create):
        refresh_token = "refresh-token-111"
        access_token = "access-token-222"
        expires = timezone.now() + timedelta(seconds=100)

        # mock the get_access_token() function
        mock_get_access_token.return_value = (access_token, expires, refresh_token)

        # setup request
        rf = RequestFactory()
        query_params = {
            "code": "red-green-blue", 
            "state": "RandomState100"
        }
        request = rf.get('/index', data=query_params)
        request.user = MagicMock()
        request.session = {
            'canvas_oauth_redirect_uri': request.build_absolute_uri(reverse('canvas-oauth-callback')),
            'canvas_oauth_request_state': query_params['state'],
            'canvas_oauth_initial_uri': '/endpoint-requires-token'
        }

        # run tests
        actual_response = oauth_callback(request)
        expected_response = HttpResponseRedirect(request.session['canvas_oauth_initial_uri'])
        self.assertEqual(expected_response.status_code, actual_response.status_code)
        self.assertEqual(expected_response['Location'], actual_response['Location'])

        mock_get_access_token.assert_called_with(
            grant_type='authorization_code',
            client_id=settings.CANVAS_OAUTH_CLIENT_ID,
            client_secret=settings.CANVAS_OAUTH_CLIENT_SECRET,
            redirect_uri=request.session["canvas_oauth_redirect_uri"],
            code=query_params['code'])

        mock_create.assert_called_with(
            user=request.user,
            access_token=access_token,
            expires=expires,
            refresh_token=refresh_token)


class TestHandleMissingToken(TestCase):

    @patch('canvas_oauth.oauth.get_random_string')
    def test_redirect_to_login_url(self, mock_get_random_string):
        request_state = 'ABC-123-RANDOM-STRING'

        # mock the get_random_string() function used to generate the "state" for the oauth request
        mock_get_random_string.return_value = request_state

        # setup request
        rf = RequestFactory()
        query_params = {
            "q": "education", 
            "page": "5"
        }
        request = rf.get('/index', data=query_params)
        request.user = MagicMock()
        request.session = {}

        redirect_uri = request.build_absolute_uri(reverse('canvas-oauth-callback'))
        login_url = get_oauth_login_url(
            client_id=settings.CANVAS_OAUTH_CLIENT_ID,
            redirect_uri=redirect_uri,
            state=request_state)

        # run tests
        response = handle_missing_token(request)

        # check the response 
        self.assertEqual(302, response.status_code)
        self.assertEqual(login_url, response['Location'])

        # check the session values
        self.assertEqual(request.get_full_path(), request.session['canvas_oauth_initial_uri'])
        self.assertEqual(request_state, request.session['canvas_oauth_request_state'])
        self.assertEqual(redirect_uri, request.session["canvas_oauth_redirect_uri"])


class TestGetOauthToken(TestCase):

    def get_mock_request_with_token(self, expired=False, **kwargs):
        access_token = kwargs.get("access_token", "access-token-123")
        refresh_token = kwargs.get("refresh_token", "refresh-token-abc")
        expires = kwargs.get("expires", datetime(2001, 1, 1) if expired else timezone.now() + timedelta(seconds=100))

        stub_canvas_oauth2_token = StubCanvasOAuth2Token(access_token, refresh_token, expires)
        stub_canvas_oauth2_token.stub_expires_within_return_value(expired)
        
        mock_user = MagicMock()
        type(mock_user).canvas_oauth2_token = PropertyMock(return_value=stub_canvas_oauth2_token)
        
        request = RequestFactory().get('/index')
        request.user = mock_user

        return request

    @patch('canvas_oauth.oauth.refresh_oauth_token')
    def test_unexpired_access_token(self, mock_refresh_oauth_token):
        expected_access_token = "unexpired-access-token-123"
        request = self.get_mock_request_with_token(expired=False, access_token=expected_access_token)
        actual_access_token = get_oauth_token(request)
        self.assertFalse(mock_refresh_oauth_token.called)
        self.assertEqual(expected_access_token, actual_access_token)

    @patch('canvas_oauth.oauth.refresh_oauth_token')
    def test_expired_access_token(self, mock_refresh_oauth_token):
        request = self.get_mock_request_with_token(expired=True)
        get_oauth_token(request)
        mock_refresh_oauth_token.assert_called_with(request)

        stub_canvas_oauth2_token = request.user.canvas_oauth2_token
        self.assertTrue(stub_canvas_oauth2_token.stub_expires_within_called_with(settings.CANVAS_OAUTH_TOKEN_EXPIRATION_BUFFER))

    def test_missing_token_error(self):
        mock_user = MagicMock()
        type(mock_user).canvas_oauth2_token = PropertyMock(side_effect=CanvasOAuth2Token.DoesNotExist())

        request = RequestFactory().get('/index')
        request.user = mock_user

        with self.assertRaises(MissingTokenError):
            get_oauth_token(request)