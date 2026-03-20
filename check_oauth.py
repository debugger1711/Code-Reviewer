import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "codereviewer.settings")
django.setup()

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site


def main() -> None:
    print("=" * 60)
    print("CHECKING GOOGLE OAUTH SETUP")
    print("=" * 60)

    print("\n1. ENVIRONMENT VARIABLES:")
    google_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "")
    google_secret = os.environ.get("GOOGLE_OAUTH_SECRET", "")
    print(f"   GOOGLE_OAUTH_CLIENT_ID: {'SET' if google_id else 'NOT SET'}")
    print(f"   GOOGLE_OAUTH_SECRET: {'SET' if google_secret else 'NOT SET'}")

    print("\n2. DJANGO SITES:")
    sites = Site.objects.all()
    print(f"   Total Sites: {sites.count()}")
    for site in sites:
        print(f"   - ID: {site.id}, Domain: {site.domain}, Name: {site.name}")

    print("\n3. SOCIAL APPS CONFIGURED:")
    apps = SocialApp.objects.all()
    print(f"   Total Social Apps: {apps.count()}")

    if apps.count() == 0:
        print("\n   NO SOCIAL APPS FOUND")
        print("   Run setup_oauth.py or create one Google SocialApp in Django admin.")
    else:
        for app in apps:
            print(f"\n   {app.provider.upper()}: {app.name}")
            print(f"     ID: {app.id}")
            print(f"     Client ID: {app.client_id[:40]}...")
            print(f"     Sites: {', '.join(site.domain for site in app.sites.all())}")

    google_apps = apps.filter(provider="google").order_by("id")
    if google_apps.count() > 1:
        print("\n   MULTIPLE GOOGLE SOCIAL APPS FOUND")
        print("   django-allauth expects exactly one Google SocialApp per site.")
        print("   Remove the duplicates so only one Google SocialApp remains.")
        for app in google_apps:
            print(f"   - ID: {app.id}, Name: {app.name}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
