from .base import *
DEBUG = False

ALLOWED_HOSTS = config('ALLOWED_HOSTS').split(',')

# Seguridad extra (MUY IMPORTANTE)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
#cambiar seguro en produccion con ssl
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False

SECURE_SSL_REDIRECT = False

# Para plataformas cloud
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
