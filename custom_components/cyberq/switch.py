"""
Support for the Cyberq service.

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
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import CyberqConfigEntry, CyberqDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CyberqConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add Cyberq entities from a config_entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            CyberqSwitch(
                coordinator,
                translation_key="opendetect",
                key="Open Detect",
                icon="mdi:valve-open",
                cyberq_name_key="OPENDETECT",
                entity_category=EntityCategory.CONFIG,
                disabled=True,
            ),
            CyberqSwitch(
                coordinator,
                translation_key="menu_scrolling",
                key="Menu Scrolling",
                icon="mdi:script-text",
                cyberq_name_key="MENU_SCROLLING",
                entity_category=EntityCategory.CONFIG,
                disabled=True,
            ),
            CyberqSwitch(
                coordinator,
                translation_key="key_beeps",
                key="Key Beeps",
                icon="mdi:keyboard",
                cyberq_name_key="KEY_BEEPS",
                entity_category=EntityCategory.CONFIG,
                disabled=True,
            ),
        ]
    )


class CyberqSwitch(CoordinatorEntity[CyberqDataUpdateCoordinator], SwitchEntity):
    """Define an Cyberq binary sensor."""

    _attr_has_entity_name = True
    _attr_native_value: bool

    def __init__(
        self,
        coordinator: CyberqDataUpdateCoordinator,
        *,
        key: str,
        icon: str,
        cyberq_name_key: str,
        entity_category: EntityCategory,
        disabled: bool = False,
        translation_key: str | None = None,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_device_info = coordinator.device_info

        self._attr_translation_key = translation_key
        self._attr_icon = icon
        self._attr_unique_id = f"{coordinator.device_info['name']}_{key}"
        self._cyberq_name_key = cyberq_name_key
        self._attr_entity_category = entity_category
        self._attr_available = hasattr(self.coordinator.data, self._cyberq_name_key)
        self._attr_entity_registry_enabled_default = not disabled

    @property
    def is_on(self) -> bool:
        """Return the state of the sensor."""
        return self._attr_native_value

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.coordinator.cyberq.async_set(self._cyberq_name_key, 1)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.coordinator.cyberq.async_set(self._cyberq_name_key, 0)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_available = hasattr(self.coordinator.data, self._cyberq_name_key)
        if not self._attr_available:
            return
        self._attr_native_value = getattr(
            self.coordinator.data, self._cyberq_name_key
        ).value
        self.async_write_ha_state()
