"""Helper utilities for quick Yeedi cloud login smoke tests."""

from __future__ import annotations

import asyncio
import os
import sys
import time
from dataclasses import dataclass
from typing import Awaitable, Dict, List

import aiohttp
from deebot_client.api_client import ApiClient
from deebot_client.authentication import Authenticator
from deebot_client.util import md5

from custom_components.yeedi_c12_cloud.const import (
    CONF_ACCOUNT,
    CONF_COUNTRY,
    CONF_PASSWORD,
)
from custom_components.yeedi_c12_cloud.helpers import create_yeedi_api_config


@dataclass(slots=True)
class LoginResult:
    """Container describing the outcome of an authentication attempt."""

    success: bool
    message: str
    mqtt_devices: List[str]


async def _perform_login(account: str, password: str, country: str) -> List[str]:
    """Attempt to authenticate and return a list of MQTT device IDs."""

    device_id = md5(str(time.time()))
    async with aiohttp.ClientSession() as session:
        yeedi_config = create_yeedi_api_config(
            session,
            device_id=device_id,
            alpha_2_country=country,
        )
        auth = Authenticator(yeedi_config.rest, account, md5(password))
        api = ApiClient(auth)
        devices = await api.get_devices()

    mqtt_devs = getattr(devices, "mqtt", []) or []
    return [getattr(dev, "did", getattr(dev, "id", str(dev))) for dev in mqtt_devs]


async def validate_login(
    *,
    account: str,
    password: str,
    country: str,
    expect_success: bool,
) -> LoginResult:
    """Run the login routine and check the result against expectations."""

    try:
        mqtt_devices = await _perform_login(account, password, country)
    except Exception as err:  # pragma: no cover - best effort smoke tests
        if expect_success:
            return LoginResult(False, f"Login failed unexpectedly: {err}", [])
        return LoginResult(True, f"Login failed as expected: {err}", [])

    if not mqtt_devices:
        message = "Login succeeded but no MQTT devices were returned."
        return LoginResult(expect_success and False, message, [])

    if expect_success:
        return LoginResult(True, "Login succeeded and devices discovered.", mqtt_devices)
    return LoginResult(
        False,
        "Login succeeded but a failure was expected.",
        mqtt_devices,
    )


def load_from_env(prefix: str = "YEEDI_") -> Dict[str, str]:
    """Load credentials from environment variables with a prefix."""

    mapping: Dict[str, str] = {
        CONF_ACCOUNT: os.getenv(f"{prefix}ACCOUNT", ""),
        CONF_PASSWORD: os.getenv(f"{prefix}PASSWORD", ""),
        CONF_COUNTRY: os.getenv(f"{prefix}COUNTRY", "US"),
    }
    missing = [key for key, value in mapping.items() if not value and key != CONF_COUNTRY]
    if missing:
        joined = ", ".join(missing)
        raise SystemExit(
            f"Missing required environment variables for login test: {joined}."
        )
    return mapping


def run_async(coro: Awaitable[LoginResult]) -> LoginResult:
    """Convenience runner for the async helper from synchronous entry points."""

    return asyncio.run(coro)


def exit_with_result(result: LoginResult) -> None:
    """Print a human-readable summary and exit with an appropriate code."""

    print(result.message)
    if result.mqtt_devices:
        print("Discovered MQTT device IDs:")
        for did in result.mqtt_devices:
            print(f"  - {did}")
    sys.exit(0 if result.success else 1)
