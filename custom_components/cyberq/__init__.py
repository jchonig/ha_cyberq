"""
The BBQ Guru CyberQ Integration integration.

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

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo

from .const import DOMAIN
from .coordinator import CyberqDataUpdateCoordinator
from .cyberq import CyberqDevice

_LOGGER = logging.getLogger(__name__)


PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.CLIMATE,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.TEXT,
]

type CyberqConfigEntry = ConfigEntry[CyberqDataUpdateCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: CyberqConfigEntry) -> bool:
    """Set up BBQ Guru CyberQ Integration from a config entry."""
    coordinator = CyberqDataUpdateCoordinator(
        hass,
        CyberqDevice(
            host=entry.data[CONF_HOST],
            port=entry.data[CONF_PORT],
            session=async_get_clientsession(hass),
        ),
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    coordinator.device_info = DeviceInfo(
        configuration_url=f"http://{coordinator.cyberq.host}/",
        identifiers={(DOMAIN, coordinator.cyberq.serial_number)},
        connections={(CONNECTION_NETWORK_MAC, coordinator.cyberq.mac)},
        serial_number=coordinator.cyberq.serial_number,
        manufacturer=coordinator.cyberq.manufacturer,
        model=coordinator.cyberq.model,
        name=f"{coordinator.cyberq.name}",
        hw_version=coordinator.cyberq.hw_version,
        sw_version=coordinator.cyberq.sw_version,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: CyberqConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
