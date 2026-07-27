"""
Diagnostics support for CyberQ.

MIT License

Copyright (c) 2024 Jeffrey C Honig

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

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
