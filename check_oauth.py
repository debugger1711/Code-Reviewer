import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'codereviewer.settings')
django.setup()

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

print("=" * 60)
print("CHECKING GOOGLE OAUTH SETUP")
print("=" * 60)

# Check environment variables
print("\n1. ENVIRONMENT VARIABLES:")
google_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "")
google_secret = os.environ.get("GOOGLE_OAUTH_SECRET", "")
print(f"   GOOGLE_OAUTH_CLIENT_ID: {'✓ SET' if google_id else '✗ NOT SET'}")
print(f"   GOOGLE_OAUTH_SECRET: {'✓ SET' if google_secret else '✗ NOT SET'}")

# Check Site configuration
print("\n2. DJANGO SITES:")
sites = Site.objects.all()
print(f"   Total Sites: {sites.count()}")
for site in sites:
    print(f"   - ID: {site.id}, Domain: {site.domain}, Name: {site.name}")

# Check SocialApp configuration
print("\n3. SOCIAL APPS CONFIGURED:")
apps = SocialApp.objects.all()
print(f"   Total Social Apps: {apps.count()}")

if apps.count() == 0:
    print("\n   ⚠️  NO SOCIAL APPS FOUND!")
    print("   You need to create a SocialApp for Google OAuth in Django Admin.")
    print("\n   Steps to Fix:")
    print("   1. Go to http://localhost:8000/admin/")
    print("   2. Go to Social Applications")
    print("   3. Click 'Add Social Application'")
    print("   4. Fill in:")
    print(f"      - Provider: Google")
    print(f"      - Name: Google OAuth")
    print(f"      - Client ID: {google_id[:40]}...")
    print(f"      - Secret Key: {google_secret[:40]}...")
    print(f"      - Sites: Select your site ({sites.first().domain if sites else '127.0.0.1:8000'})")
    print("   5. Save")
else:
    for app in apps:
        print(f"\n   ✓ {app.provider.upper()}: {app.name}")
        print(f"     Client ID: {app.client_id[:40]}...")
        print(f"     Sites: {', '.join([s.domain for s in app.sites.all()])}")

print("\n" + "=" * 60)
