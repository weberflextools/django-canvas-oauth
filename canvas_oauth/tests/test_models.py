from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
import datetime
import random
import string

from canvas_oauth.models import CanvasOAuth2Token


def randomstr(size):
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return ''.join(random.choices(chars, k=size))


class TestCanvasOAuth2Token(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='jsmith',
            email='jsmith@localhost.localdomain',
            password='supersecret',
        )

    def tearDown(self):
        self.user.delete()

    def test_create_oauth2token(self):
        access_token, refresh_token = randomstr(64), randomstr(64)
        seconds_to_expire = 3600
        expires = timezone.now() + datetime.timedelta(seconds=seconds_to_expire)

        oauth2token = CanvasOAuth2Token(
            user=self.user,
            access_token=access_token,
            refresh_token=refresh_token,
            expires=expires,
        )
        oauth2token.save()

        self.assertEqual(self.user.pk, oauth2token.user.pk)
        self.assertEqual(access_token, oauth2token.access_token)
        self.assertEqual(refresh_token, oauth2token.refresh_token)
        self.assertEqual(expires, oauth2token.expires)

    def test_token_expires_within_time_period(self):
        expires_in_seconds = 15
        expires = timezone.now() + datetime.timedelta(seconds=expires_in_seconds)
        oauth2token = CanvasOAuth2Token(
            user=self.user,
            access_token=randomstr(64),
            refresh_token=randomstr(64),
            expires=expires,
        )
        oauth2token.save()

        # assert that the token is soon to be expired (within the given time frame) and should be refreshed
        delta = datetime.timedelta(expires_in_seconds)
        requires_refresh = oauth2token.expires_within(delta)
        self.assertTrue(requires_refresh)

    def test_token_does_not_expire_within_time_period(self):
        expires_in_seconds = 60
        expires = timezone.now() + datetime.timedelta(seconds=expires_in_seconds)
        oauth2token = CanvasOAuth2Token(
            user=self.user,
            access_token=randomstr(64),
            refresh_token=randomstr(64),
            expires=expires,
        )
        oauth2token.save()

        # assert that the token is NOT close to expiring, and does NOT require refreshing
        delta = datetime.timedelta(0)
        requires_refresh = oauth2token.expires_within(delta)
        self.assertFalse(requires_refresh)
