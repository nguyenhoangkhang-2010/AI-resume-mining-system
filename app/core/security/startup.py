from loguru import logger

from app.core.config.settings import Settings
from app.core.security.api_keys import ApiKeyStore


def validate_security_settings(config: Settings) -> None:
    """
    Fails fast, before any model is loaded, when authentication is required
    but no usable key is configured.
    """

    if not config.AUTH_ENABLED:
        logger.warning(
            "AUTH_ENABLED is false: every endpoint is open to anyone who can "
            "reach the API. Use this only on a private development machine."
        )
        return

    try:
        store = ApiKeyStore.parse(config.API_KEYS)
    except ValueError as exc:
        raise RuntimeError(f"Invalid API_KEYS: {exc}") from exc

    if len(store) == 0:
        raise RuntimeError(
            "AUTH_ENABLED is true but API_KEYS is empty. Set API_KEYS to "
            "role:key pairs (generate a key with: python -c \"import secrets; "
            "print(secrets.token_urlsafe(32))\"), or set AUTH_ENABLED=false "
            "for local development."
        )

    logger.info("API key authentication enabled ({} key(s)).", len(store))
