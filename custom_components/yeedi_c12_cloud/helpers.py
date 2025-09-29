"""Helpers for configuring Yeedi-specific API endpoints."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Optional

from aiohttp import ClientSession

from deebot_client.authentication import RestConfiguration, create_rest_config


@dataclass(frozen=True, slots=True)
class YeediApiConfig:
    """Container for the API configuration pieces we care about."""

    rest: RestConfiguration
    mqtt_override: Optional[str] = None


def create_yeedi_api_config(
    session: ClientSession,
    *,
    device_id: str,
    alpha_2_country: str,
) -> YeediApiConfig:
    """Return a Yeedi-specific REST configuration and MQTT override (if any).

    We leverage :func:`deebot_client.authentication.create_rest_config` to build
    a base `RestConfiguration` and immediately swap the login URLs to point at
    the Yeedi-branded hosts.  Yeedi's cloud still routes MQTT traffic through
    the Ecovacs-operated ``mq*.ecouser.net`` brokers, so no override is required
    for MQTT today; keeping the default documents that behaviour for future
    maintainers.
    """

    base = create_rest_config(
        session,
        device_id=device_id,
        alpha_2_country=alpha_2_country,
    )
    country_slug = base.country.lower()
    tld = "cn" if alpha_2_country.upper() == "CN" else "com"
    login_url = f"https://gl-{country_slug}-api.yeedi.{tld}"
    auth_code_url = f"https://gl-{country_slug}-openapi.yeedi.{tld}"

    rest = replace(base, login_url=login_url, auth_code_url=auth_code_url)
    return YeediApiConfig(rest=rest, mqtt_override=None)
