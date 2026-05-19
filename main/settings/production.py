from .base import *
DEBUG = False

ALLOWED_HOSTS = config('ALLOWED_HOSTS').split(',')

# Seguridad extra (MUY IMPORTANTE)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

SECURE_SSL_REDIRECT = True

# Para plataformas cloud
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
