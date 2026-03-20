import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'codereviewer.settings')
django.setup()

from django.contrib.sites.models import Site

# Update the default site
site = Site.objects.get(id=1)
print(f"Current Site Domain: {site.domain}")

# Update for local development
site.domain = '127.0.0.1:8000'
site.name = 'Code Reviewer'
site.save()

print(f"Updated Site Domain: {site.domain}")
print(f"Site saved successfully!")

# Print info for next steps
print(f"\n✓ OAuth is now configured!")
print(f"✓ You can now login with Google at: http://127.0.0.1:8000/accounts/google/login/")
