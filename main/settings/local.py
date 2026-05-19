
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

INSTALLED_APPS += ["django_tailwind_cli"]

STATICFILES_DIRS = [BASE_DIR / "assets"]

TAILWIND_CLI_OUTPUT_DIR = "assets"   # por defecto ya es 'assets'

# Forzar la ubicación real de manage.py (raíz del proyecto)
TAILWIND_CLI_MANAGE_PY = BASE_DIR / "manage.py"