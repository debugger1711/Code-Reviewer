from __future__ import annotations

from django.conf import settings
from django.db import OperationalError, ProgrammingError

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialApp

from .models import UserProfile


class CodeReviewerSocialAccountAdapter(DefaultSocialAccountAdapter):
    def list_apps(self, request, provider=None, client_id=None):
        configured_apps = []
        provider_names = [provider] if provider else list(settings.SOCIALACCOUNT_PROVIDERS.keys())

        for provider_name in provider_names:
            provider_config = settings.SOCIALACCOUNT_PROVIDERS.get(provider_name, {})
            app_configs = provider_config.get("APPS") or []
            for app_config in app_configs:
                if client_id and app_config.get("client_id") != client_id:
                    continue
                app = SocialApp(provider=provider_name)
                app.name = app_config.get("name", f"{provider_name.title()} OAuth")
                app.client_id = app_config.get("client_id", "")
                app.secret = app_config.get("secret", "")
                app.key = app_config.get("key", "")
                configured_apps.append(app)

        if configured_apps:
            return configured_apps
        return super().list_apps(request, provider=provider, client_id=client_id)

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form=form)
        self._sync_profile(user, sociallogin)
        return user

    def pre_social_login(self, request, sociallogin):
        super().pre_social_login(request, sociallogin)
        if sociallogin.is_existing:
            self._sync_profile(sociallogin.user, sociallogin)

    def _sync_profile(self, user, sociallogin) -> None:
        extra_data = sociallogin.account.extra_data or {}
        defaults = {
            "profile_picture": extra_data.get("picture") or extra_data.get("avatar_url"),
        }
        if sociallogin.account.provider == "google":
            defaults["google_id"] = sociallogin.account.uid
        try:
            UserProfile.objects.update_or_create(user=user, defaults=defaults)
        except (OperationalError, ProgrammingError):
            return
