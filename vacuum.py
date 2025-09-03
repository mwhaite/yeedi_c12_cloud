
from __future__ import annotations
import time
from typing import Any, Optional

from homeassistant.components.vacuum import StateVacuumEntity, VacuumEntityFeature
from homeassistant.const import STATE_CLEANING, STATE_DOCKED, STATE_IDLE, STATE_RETURNING, STATE_PAUSED
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers import entity_platform
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_ACCOUNT, CONF_PASSWORD, CONF_COUNTRY, CONF_DEVICE_ID, CONF_DEVICE_NAME

from deebot_client.authentication import Authenticator, create_rest_config
from deebot_client.api_client import ApiClient
from deebot_client.util import md5
from deebot_client.mqtt_client import MqttClient, create_mqtt_config
from deebot_client.device import Device as DeebotDevice
from deebot_client.events import (
    BatteryEvent, CleanStateEvent, ErrorEvent, BinFullEvent, ChargeStateEvent
)
# Optional events and commands (guarded)
try:
    from deebot_client.events import FanSpeedEvent, WaterLevelEvent
except Exception:
    FanSpeedEvent = None
    WaterLevelEvent = None

from deebot_client.commands.json.clean import Clean, CleanAction
from deebot_client.commands.json.charge import Charge
from deebot_client.commands.json.locate import PlaySound
try:
    from deebot_client.commands.json.fan import SetFanSpeed
except Exception:
    SetFanSpeed = None
try:
    from deebot_client.commands.json.water import SetWaterLevel
except Exception:
    SetWaterLevel = None

import aiohttp

SUPPORTED_FEATURES = (
    VacuumEntityFeature.STATE
    | VacuumEntityFeature.START
    | VacuumEntityFeature.PAUSE
    | VacuumEntityFeature.STOP
    | VacuumEntityFeature.RETURN_HOME
    | VacuumEntityFeature.LOCATE
    | VacuumEntityFeature.SEND_COMMAND
    | VacuumEntityFeature.BATTERY
    | VacuumEntityFeature.FAN_SPEED
)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    entity = YeediCloudVacuum(hass, entry)
    async_add_entities([entity], True)

    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service("set_fan_speed", {"fan_speed": str}, "async_set_fan_speed")
    platform.async_register_entity_service("set_water_level", {"level": int}, "async_set_water_level")
    platform.async_register_entity_service("set_clean_mode", {"mode": str}, "async_set_clean_mode")
    platform.async_register_entity_service("clean_rooms", {"rooms": list}, "async_clean_rooms")
    platform.async_register_entity_service("clean_areas", {"areas": list}, "async_clean_areas")
    platform.async_register_entity_service("empty_bin", {}, "async_empty_bin")
    platform.async_register_entity_service("set_dnd", {"enabled": bool, "start": str | None, "end": str | None}, "async_set_dnd")

class YeediCloudVacuum(StateVacuumEntity):
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self.entry = entry
        self._name = entry.data.get(CONF_DEVICE_NAME) or "Yeedi C12"
        self._unique = f"{DOMAIN}:{entry.data[CONF_DEVICE_ID]}"
        self._attr_name = self._name
        self._attr_unique_id = self._unique
        self._attr_supported_features = SUPPORTED_FEATURES
        self._fan_speed: Optional[str] = None
        self._water_level: Optional[int] = None

        self._state: Optional[str] = None
        self._battery: Optional[int] = None
        self._bin_full: Optional[bool] = None
        self._error: Optional[str] = None

        self._mqtt: Optional[MqttClient] = None
        self._bot: Optional[DeebotDevice] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._auth: Optional[Authenticator] = None

    @property
    def battery_level(self) -> int | None:
        return self._battery

    @property
    def fan_speed(self) -> str | None:
        return self._fan_speed

    @property
    def fan_speed_list(self) -> list[str]:
        return ["silent", "standard", "max", "turbo"]

    @property
    def state(self) -> str | None:
        return self._state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        out = {}
        if self._bin_full is not None:
            out["bin_full"] = self._bin_full
        if self._error:
            out["error"] = self._error
        if self._water_level is not None:
            out["water_level"] = self._water_level
        return out

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._unique)},
            name=self._name,
            manufacturer="Yeedi / Ecovacs",
            model="C12 (cloud)",
        )

    async def async_added_to_hass(self) -> None:
        await self._ensure_connected()

    async def async_will_remove_from_hass(self) -> None:
        try:
            if self._mqtt:
                await self._mqtt.close()
            if self._session:
                await self._session.close()
        except Exception:
            pass

    async def _ensure_connected(self):
        if self._mqtt and self._bot:
            return
        data = self.entry.data
        account = data[CONF_ACCOUNT]
        password = data[CONF_PASSWORD]
        country = data[CONF_COUNTRY]
        did = data[CONF_DEVICE_ID]
        device_id = md5(str(time.time()))

        self._session = aiohttp.ClientSession()
        rest = create_rest_config(self._session, device_id=device_id, alpha_2_country=country)
        self._auth = Authenticator(rest, account, md5(password))
        api = ApiClient(self._auth)
        devices = await api.get_devices()

        target = None
        for d in devices.mqtt:
            if getattr(d, "did", None) == did or getattr(d, "id", None) == did:
                target = d
                break
        if not target and devices.mqtt:
            target = devices.mqtt[0]
        self._bot = DeebotDevice(target, self._auth)

        self._mqtt = MqttClient(create_mqtt_config(device_id=device_id, country=country), self._auth)
        await self._bot.initialize(self._mqtt)

        self._bot.events.subscribe(BatteryEvent, self._on_battery)
        self._bot.events.subscribe(CleanStateEvent, self._on_clean_state)
        self._bot.events.subscribe(ChargeStateEvent, self._on_charge_state)
        self._bot.events.subscribe(ErrorEvent, self._on_error)
        self._bot.events.subscribe(BinFullEvent, self._on_binfull)
        if FanSpeedEvent:
            self._bot.events.subscribe(FanSpeedEvent, self._on_fan_speed)
        if WaterLevelEvent:
            self._bot.events.subscribe(WaterLevelEvent, self._on_water_level)

    async def _on_battery(self, event: BatteryEvent):
        self._battery = int(event.value) if event.value is not None else None
        self.async_write_ha_state()

    async def _on_binfull(self, event: BinFullEvent):
        self._bin_full = bool(event.value)
        self.async_write_ha_state()

    async def _on_error(self, event: ErrorEvent):
        self._error = event.value or ""
        self.async_write_ha_state()

    async def _on_fan_speed(self, event):
        self._fan_speed = str(event.value).lower()
        self.async_write_ha_state()

    async def _on_water_level(self, event):
        try:
            self._water_level = int(event.value)
        except Exception:
            self._water_level = None
        self.async_write_ha_state()

    async def _on_clean_state(self, event: CleanStateEvent):
        val = (str(event.value) if event.value is not None else "").lower()
        if any(k in val for k in ["clean", "working", "sweep", "mop"]):
            self._state = STATE_CLEANING
        elif "pause" in val:
            self._state = STATE_PAUSED
        elif any(k in val for k in ["idle", "stop", "standby"]):
            self._state = STATE_IDLE
        self.async_write_ha_state()

    async def _on_charge_state(self, event: ChargeStateEvent):
        val = (str(event.value) if event.value is not None else "").lower()
        if any(k in val for k in ["charging", "return"]):
            self._state = STATE_RETURNING
        elif "docked" in val or "station" in val:
            self._state = STATE_DOCKED
        self.async_write_ha_state()

    # ---- Core commands ----
    async def async_start(self):
        await self._ensure_connected()
        await self._bot.execute_command(Clean(CleanAction.START))

    async def async_stop(self):
        await self._ensure_connected()
        await self._bot.execute_command(Clean(CleanAction.STOP))

    async def async_pause(self):
        await self._ensure_connected()
        await self._bot.execute_command(Clean(CleanAction.PAUSE))

    async def async_return_to_base(self):
        await self._ensure_connected()
        await self._bot.execute_command(Charge())

    async def async_locate(self):
        await self._ensure_connected()
        await self._bot.execute_command(PlaySound())

    async def async_send_command(self, command: str, params: dict | list | None = None):
        await self._ensure_connected()
        cmd = (command or "").lower()
        if cmd in ("start", "clean", "auto"):
            return await self.async_start()
        if cmd in ("pause",):
            return await self.async_pause()
        if cmd in ("stop", "idle"):
            return await self.async_stop()
        if cmd in ("return_to_base", "charge", "dock"):
            return await self.async_return_to_base()
        if cmd in ("locate", "beep"):
            return await self.async_locate()
        # otherwise no-op

    # ---- Extended services ----
    async def async_set_fan_speed(self, fan_speed: str):
        await self._ensure_connected()
        if SetFanSpeed is not None:
            await self._bot.execute_command(SetFanSpeed(fan_speed))
        else:
            await self._bot.execute_command(Clean(CleanAction.START, options={"fanSpeed": fan_speed}))

    async def async_set_water_level(self, level: int):
        await self._ensure_connected()
        if SetWaterLevel is not None:
            await self._bot.execute_command(SetWaterLevel(int(level)))
        else:
            await self._bot.execute_command(Clean(CleanAction.START, options={"waterLevel": int(level)}))

    async def async_set_clean_mode(self, mode: str):
        await self._ensure_connected()
        m = (mode or "").lower()
        if m in ("auto", "standard"):
            await self._bot.execute_command(Clean(CleanAction.START, options={"type": "auto"}))
        elif m == "edge":
            await self._bot.execute_command(Clean(CleanAction.START, options={"type": "edge"}))
        elif m in ("spot", "area"):
            await self._bot.execute_command(Clean(CleanAction.START, options={"type": "spot"}))
        else:
            await self._bot.execute_command(Clean(CleanAction.START))

    async def async_clean_rooms(self, rooms: list):
        await self._ensure_connected()
        await self._bot.execute_command(Clean(CleanAction.START, options={"type": "rooms", "rooms": rooms}))

    async def async_clean_areas(self, areas: list):
        await self._ensure_connected()
        await self._bot.execute_command(Clean(CleanAction.START, options={"type": "areas", "areas": areas}))

    async def async_empty_bin(self):
        await self._ensure_connected()
        await self._bot.execute_command(Charge(options={"emptyDustBox": True}))

    async def async_set_dnd(self, enabled: bool, start: str | None = None, end: str | None = None):
        await self._ensure_connected()
        opts = {"enabled": bool(enabled)}
        if start:
            opts["start"] = start
        if end:
            opts["end"] = end
        await self._bot.execute_command(Clean(CleanAction.PAUSE, options={"dnd": opts}))
