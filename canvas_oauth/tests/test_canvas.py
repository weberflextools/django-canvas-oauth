from datetime import timedelta
from operator import itemgetter
from urllib.parse import urlencode
from uuid import uuid4
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from canvas_oauth.exceptions import InvalidOAuthReturnError
from canvas_oauth.canvas import get_oauth_login_url, get_access_token


class TestGetOauthLoginUrl(TestCase):

    def _get_expected_url(self, auth_params):
        canvas_domain = settings.CANVAS_OAUTH_CANVAS_DOMAIN
        auth_params = sorted(auth_params.items(), key=itemgetter(0))
        auth_qs = urlencode(auth_params)
        return 'https://%s/login/oauth2/auth?%s' % (canvas_domain, auth_qs)

    def test_oauth_login_url_with_empty_scopes(self):
        auth_params = {
            'response_type': 'code',
            'client_id': settings.CANVAS_OAUTH_CLIENT_ID,
            'redirect_uri': '/oauth/oauth-callback',
            'state': uuid4(),  # random string
        }
        expected_url = self._get_expected_url(auth_params)

        for scopes in ([], '', None):
            actual_url = get_oauth_login_url(
                client_id=auth_params['client_id'],
                redirect_uri=auth_params['redirect_uri'],
                state=auth_params['state'],
                scopes=scopes,
            )
            self.assertEqual(expected_url, actual_url)

    def test_oauth_login_url_with_scopes(self):
        scopes = [
            'url:GET|/api/v1/courses',
            'url:GET|/api/v1/courses/:id',
            'url:GET|/api/v1/courses/:course_id/assignments'
        ]
        auth_params = {
            'response_type': 'code',
            'client_id': settings.CANVAS_OAUTH_CLIENT_ID,
            'redirect_uri': '/oauth/oauth-callback',
            'state': uuid4(),  # random string
            'scope': " ".join(scopes),
        }

        expected_url = self._get_expected_url(auth_params)
        actual_url = get_oauth_login_url(
            client_id=auth_params['client_id'],
            redirect_uri=auth_params['redirect_uri'],
            state=auth_params['state'],
            scopes=scopes,
        )
        self.assertEqual(expected_url, actual_url)


class TestGetAccessToken(TestCase):

    def get_response_data(self, access_token, refresh_token, seconds_to_expire):
        response_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": seconds_to_expire,
            "token_type": "Bearer",
            "user": {
                "id": 123,
                "name": "John Smith"
            }
        }
        return response_data

    def get_token_url(self):
        return 'https://%s/login/oauth2/token' % settings.CANVAS_OAUTH_CANVAS_DOMAIN

    @patch('canvas_oauth.canvas.timezone.now')
    @patch('canvas_oauth.canvas.requests.post')
    def test_authorization_code(self, mock_post, mock_timezone_now):
        access_token = "29EcPu2JpbOOlss5Lo3BzP5OK4"
        refresh_token = "Io9aGV7HT6UzKawzEkf1aevGm"
        seconds_to_expire = 3600

        # mock the json response from the token endpoint
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = self.get_response_data(
            access_token=access_token,
            refresh_token=refresh_token,
            seconds_to_expire=seconds_to_expire)

        # mock timzone used to determine token expiration
        now = timezone.now()
        mock_timezone_now.return_value = now
        expires = now + timedelta(seconds=seconds_to_expire)

        # make the request
        params = dict(
            grant_type='authorization_code',
            code="D5xNoAMwrwSNI5P16zKeXxjT",
            client_id=settings.CANVAS_OAUTH_CLIENT_ID,
            client_secret=settings.CANVAS_OAUTH_CLIENT_SECRET,
            redirect_uri='/oauth/oauth-callback'
        )
        actual_tuple = get_access_token(**params)
        expected_tuple = (access_token, expires, refresh_token)

        self.assertEqual(expected_tuple, actual_tuple)
        mock_post.assert_called_with(self.get_token_url(), params)

    @patch('canvas_oauth.canvas.timezone.now')
    @patch('canvas_oauth.canvas.requests.post')
    def test_refresh_token(self, mock_post, mock_timezone_now):
        access_token = "29EcPu2JpbOOlss5Lo3BzP5OK4"
        refresh_token = "Io9aGV7HT6UzKawzEkf1aevGm"
        seconds_to_expire = 3600

        # mock the json response from the token endpoint
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = self.get_response_data(
            access_token=access_token,
            refresh_token=refresh_token,
            seconds_to_expire=seconds_to_expire)

        # mock timzone used to determine token expiration
        now = timezone.now()
        mock_timezone_now.return_value = now
        expires = now + timedelta(seconds=seconds_to_expire)

        # request an access token and check result
        params = dict(
            grant_type='refresh_token',
            refresh_token="zMaP0572EUof7iA83n6rmElC",
            client_id=settings.CANVAS_OAUTH_CLIENT_ID,
            client_secret=settings.CANVAS_OAUTH_CLIENT_SECRET,
            redirect_uri='/oauth/oauth-callback'
        )
        actual_tuple = get_access_token(**params)
        expected_tuple = (access_token, expires, refresh_token)

        self.assertEqual(expected_tuple, actual_tuple)
        mock_post.assert_called_with(self.get_token_url(), params)

    @patch('canvas_oauth.canvas.requests.post')
    def test_authorization_code_error(self, mock_post):
        mock_post.return_value.status_code = 403  # Forbidden

        params = dict(
            grant_type='authorization_code',
            code="D5xNoAMwrwSNI5P16zKeXxjT",
            client_id=settings.CANVAS_OAUTH_CLIENT_ID,
            client_secret=settings.CANVAS_OAUTH_CLIENT_SECRET,
            redirect_uri='/oauth/oauth-callback'
        )
        with self.assertRaises(InvalidOAuthReturnError):
            get_access_token(**params)

        mock_post.assert_called_with(self.get_token_url(), params)
