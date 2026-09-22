"""Feature flags: environment override, then platform row, then family row, then default."""

import os

DEFAULTS = {
    "ai_copilot": False,
    "billing_checkout": True,
    "cookie_banner": True,
    "whatsapp_bot": False,
    "telegram_bot": False,
}


def is_enabled(key: str, *, family=None) -> bool:
    env_name = f"FEATURE_{key.upper()}"
    if env_name in os.environ:
        return os.environ[env_name].lower() in {"1", "true", "yes", "on"}
    from apps.flags.models import PlatformFlag

    platform = PlatformFlag.objects.filter(key=key).first()
    if platform is not None:
        return platform.enabled
    if family is not None:
        from apps.administration.models import FeatureFlag

        family_flag = FeatureFlag.objects.filter(family=family, key=key).first()
        if family_flag is not None:
            return family_flag.enabled
    return DEFAULTS.get(key, False)
