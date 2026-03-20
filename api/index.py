import os
from django.core.wsgi import get_wsgi_application

# Ensure this points to your project's settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "codereviewer.settings")

# Vercel requires the variable to be named 'app'
app = get_wsgi_application()