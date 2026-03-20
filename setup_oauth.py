import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'codereviewer.settings')
django.setup()

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

# Get or create Site
site, created = Site.objects.get_or_create(
    id=1,
    defaults={
        'domain': '127.0.0.1:8000',
        'name': 'Code Reviewer'
    }
)

print(f"Site: {site.domain} (name: {site.name})")

# Check if Google app exists
google_app = SocialApp.objects.filter(provider='google').first()

if not google_app:
    print("\n❌ Google OAuth app not found. Creating...")
    
    # Get credentials from environment
    client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', '')
    secret = os.environ.get('GOOGLE_OAUTH_SECRET', '')
    
    if not client_id or not secret:
        print("ERROR: GOOGLE_OAUTH_CLIENT_ID or GOOGLE_OAUTH_SECRET not set in .env")
        exit(1)
    
    # Create Google SocialApp
    google_app = SocialApp.objects.create(
        provider='google',
        name='Google OAuth',
        client_id=client_id,
        secret=secret,
    )
    
    # Add site to the app
    google_app.sites.add(site)
    
    print(f"✓ Created Google OAuth SocialApp")
    print(f"  Client ID: {client_id[:40]}...")
    print(f"  Site: {site.domain}")
else:
    print(f"\n✓ Google OAuth app already exists")
    print(f"  Name: {google_app.name}")
    print(f"  Client ID: {google_app.client_id[:40]}...")
    print(f"  Sites: {', '.join([s.domain for s in google_app.sites.all()])}")

print("\n✓ Google OAuth setup complete!")
