"""
Service actions for the BBQ Guru CyberQ Integration.

MIT License

Copyright (c) 2026 Jeffrey C Honig

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

from typing import TYPE_CHECKING, Final

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_DEVICE_ID
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall

    from .coordinator import CyberqDataUpdateCoordinator

SERVICE_RESET_COOK: Final = "reset_cook"

# What reset_cook restores. The CyberQ needs a name of at least one
# character, so names go back to these defaults instead of empty.
RESET_COOK_VALUES: Final = {
    "COOK_NAME": "Cook",
    "FOOD1_NAME": "Food1",
    "FOOD2_NAME": "Food2",
    "FOOD3_NAME": "Food3",
    "COOK_RAMP": "None",
}

RESET_COOK_SCHEMA: Final = vol.Schema({vol.Required(ATTR_DEVICE_ID): cv.string})


def _coordinator(hass: HomeAssistant, device_id: str) -> CyberqDataUpdateCoordinator:
    """Return the coordinator of a loaded CyberQ device."""
    device = dr.async_get(hass).async_get(device_id)
    if device is not None:
        for entry_id in device.config_entries:
            entry = hass.config_entries.async_get_entry(entry_id)
            if entry is None or entry.domain != DOMAIN:
                continue
            if entry.state is not ConfigEntryState.LOADED:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="device_not_loaded",
                    translation_placeholders={"device": device.name or device_id},
                )
            return entry.runtime_data
    raise ServiceValidationError(
        translation_domain=DOMAIN,
        translation_key="device_not_found",
        translation_placeholders={"device_id": device_id},
    )


async def _async_reset_cook(call: ServiceCall) -> None:
    """Reset the cook and probe names and turn off the ramp."""
    coordinator = _coordinator(call.hass, call.data[ATTR_DEVICE_ID])
    try:
        await coordinator.cyberq.async_set_many(RESET_COOK_VALUES)
    except (TimeoutError, aiohttp.ClientError) as error:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="write_failed",
            translation_placeholders={"error": str(error)},
        ) from error
    await coordinator.async_request_refresh()


def async_setup_services(hass: HomeAssistant) -> None:
    """Register the integration's service actions."""
    hass.services.async_register(
        DOMAIN, SERVICE_RESET_COOK, _async_reset_cook, schema=RESET_COOK_SCHEMA
    )
