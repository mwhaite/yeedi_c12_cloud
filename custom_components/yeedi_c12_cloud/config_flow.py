
from __future__ import annotations
import time

import aiohttp
import voluptuous as vol
from deebot_client.api_client import ApiClient
from deebot_client.authentication import Authenticator
from deebot_client.util import md5
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_ACCOUNT, CONF_PASSWORD, CONF_COUNTRY, CONF_DEVICE_ID, CONF_DEVICE_NAME
from .helpers import create_yeedi_api_config

STEP_USER_SCHEMA = vol.Schema({
    vol.Required(CONF_ACCOUNT): str,
    vol.Required(CONF_PASSWORD): str,
    vol.Required(CONF_COUNTRY, default="US"): str,
})

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input is not None:
            account = user_input[CONF_ACCOUNT].strip()
            password = user_input[CONF_PASSWORD]
            country = user_input[CONF_COUNTRY].strip().upper()

            try:
                device_id = md5(str(time.time()))
                async with aiohttp.ClientSession() as session:
                    yeedi_config = create_yeedi_api_config(
                        session, device_id=device_id, alpha_2_country=country
                    )
                    auth = Authenticator(yeedi_config.rest, account, md5(password))
                    api = ApiClient(auth)
                    devices = await api.get_devices()
                    mqtt_devs = getattr(devices, "mqtt", []) or []
                    if not mqtt_devs:
                        errors["base"] = "no_devices"
                    else:
                        self._account = account
                        self._password = password
                        self._country = country
                        self._mqtt_devs = mqtt_devs
                        return await self.async_step_pick()
            except Exception:
                errors["base"] = "cannot_connect"

        return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors)

    async def async_step_pick(self, user_input=None) -> FlowResult:
        import voluptuous as vol
        if user_input is not None:
            dev_id = user_input[CONF_DEVICE_ID]
            name = user_input.get(CONF_DEVICE_NAME) or dev_id
            await self.async_set_unique_id(f"{DOMAIN}:{dev_id}")
            self._abort_if_unique_id_configured()
            data = {
                CONF_ACCOUNT: self._account,
                CONF_PASSWORD: self._password,
                CONF_COUNTRY: self._country,
                CONF_DEVICE_ID: dev_id,
                CONF_DEVICE_NAME: name,
            }
            return self.async_create_entry(title=name, data=data)

        opts = {}
        for d in self._mqtt_devs:
            did = getattr(d, "did", None) or getattr(d, "id", None) or str(d)
            nick = getattr(d, "nick", None) or getattr(d, "name", None) or did
            opts[did] = f"{nick} ({did})"

        schema = vol.Schema({
            vol.Required(CONF_DEVICE_ID): vol.In(list(opts.keys())),
            vol.Optional(CONF_DEVICE_NAME): str,
        })
        return self.async_show_form(step_id="pick", data_schema=schema)
