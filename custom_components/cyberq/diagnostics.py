"""Diagnostics support for CyberQ."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import CyberqConfigEntry
from .cyberq import CyberqSensor

TO_REDACT = {
    "serial_number",
    "hostname",
    "macaddress",
    "username",
    "password",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    config_entry: CyberqConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""

    cyberq = config_entry.runtime_data.cyberq

    _excluded_keys = set(CyberqSensor.__dict__.keys())

    sensors = {
        sensor_name: {
            key: value
            for (key, value) in sensor.__dict__.items()
            if key not in _excluded_keys
        }
        for sensor_name, sensor in cyberq.sensors.sensors.items()
    }

    data = {
        "hostname": cyberq.host,
        "hw_version": cyberq.hw_version,
        "macaddress": cyberq.mac,
        "manufacturer": cyberq.manufacturer,
        "model": cyberq.model,
        "port": cyberq.port,
        "sensors": sensors,
        "serial_number": cyberq.serial_number,
        "sw_version": cyberq.sw_version,
    }

    return async_redact_data(data, TO_REDACT)
