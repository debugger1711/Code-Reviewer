import os
import site
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application

vendor_dir = Path(__file__).resolve().parent.parent / ".vendor"
if vendor_dir.exists():
    sys.path.insert(0, str(vendor_dir))

user_site = site.getusersitepackages()
if user_site and user_site not in sys.path:
    sys.path.append(user_site)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "codereviewer.settings")

application = get_wsgi_application()
