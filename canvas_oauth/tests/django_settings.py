import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'fake-key'

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'canvas_oauth.apps.CanvasOAuthConfig'
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
    },
]

ROOT_URLCONF = 'canvas_oauth.urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

CANVAS_OAUTH_CLIENT_ID = 101
CANVAS_OAUTH_CLIENT_SECRET = "fake-secret"
CANVAS_OAUTH_CANVAS_DOMAIN = "canvas.localhost"
