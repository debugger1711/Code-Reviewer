import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "codereviewer.settings")
django.setup()

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site


def main() -> None:
    site, _ = Site.objects.get_or_create(
        id=1,
        defaults={
            "domain": "127.0.0.1:8000",
            "name": "Code Reviewer",
        },
    )
    print(f"Site: {site.domain} (name: {site.name})")

    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "")
    secret = os.environ.get("GOOGLE_OAUTH_SECRET", "")
    if not client_id or not secret:
        print("ERROR: GOOGLE_OAUTH_CLIENT_ID or GOOGLE_OAUTH_SECRET not set in .env")
        raise SystemExit(1)

    google_apps = SocialApp.objects.filter(provider="google").order_by("id")
    if google_apps.count() > 1:
        print("\nERROR: Multiple Google SocialApps found.")
        print("Delete the duplicates so only one Google SocialApp remains.")
        for app in google_apps:
            domains = ", ".join(site.domain for site in app.sites.all()) or "(no sites)"
            print(f"  - ID {app.id}: {app.name} [{domains}]")
        raise SystemExit(1)

    google_app = google_apps.first()
    if google_app is None:
        print("\nGoogle OAuth app not found. Creating...")
        google_app = SocialApp.objects.create(
            provider="google",
            name="Google OAuth",
            client_id=client_id,
            secret=secret,
        )
    else:
        print("\nGoogle OAuth app already exists. Updating credentials and site mapping...")
        google_app.name = "Google OAuth"
        google_app.client_id = client_id
        google_app.secret = secret
        google_app.save(update_fields=["name", "client_id", "secret"])

    google_app.sites.add(site)

    print("Google OAuth setup complete.")
    print(f"  Name: {google_app.name}")
    print(f"  Client ID: {google_app.client_id[:40]}...")
    print(f"  Sites: {', '.join(site.domain for site in google_app.sites.all())}")


if __name__ == "__main__":
    main()
