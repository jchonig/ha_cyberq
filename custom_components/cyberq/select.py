"""Cyberq implementation of temperature probes as number devices."""

from __future__ import annotations

import logging
from collections.abc import Mapping

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import CyberqConfigEntry, CyberqDataUpdateCoordinator
from .cyberq import CYBERQ_SENSORS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CyberqConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the demo number platform."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            CyberqSelect(
                coordinator,
                key="Ramp Probe",
                translation_key="ramp_probe",
                icon="mdi:thermometer-lines",
                cyberq_name_key="COOK_RAMP",
                options=CYBERQ_SENSORS["COOK_RAMP"].values,
            ),
            CyberqSelect(
                coordinator,
                key="Display degree units",
                translation_key="display_degree_units",
                icon="mdi:thermometer",
                cyberq_name_key="DEG_UNITS",
                options=CYBERQ_SENSORS["DEG_UNITS"].values,
                disabled=True,
            ),
            CyberqSelect(
                coordinator,
                key="Alarm beeps",
                translation_key="alarm_beeps",
                icon="mdi:alert",
                cyberq_name_key="ALARM_BEEPS",
                options=CYBERQ_SENSORS["ALARM_BEEPS"].values,
                disabled=True,
            ),
            CyberqSelect(
                coordinator,
                key="Timeout action",
                translation_key="timeout_action",
                icon="mdi:clock",
                cyberq_name_key="TIMEOUT_ACTION",
                options=CYBERQ_SENSORS["TIMEOUT_ACTION"].values,
                disabled=True,
            ),
        ]
    )


class CyberqSelect(CoordinatorEntity[CyberqDataUpdateCoordinator], SelectEntity):
    """Representation of a Cyberq temperature probe as a thermostat ."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: CyberqDataUpdateCoordinator,
        *,
        cyberq_name_key: str,
        icon: str,
        key: str,
        translation_key: str,
        options: list[str],
        translation_placeholders: Mapping[str, str] | None = None,
        disabled: bool = False,
    ) -> None:
        """Initialize the selection device."""
        super().__init__(coordinator)
        self._attr_device_info = coordinator.device_info

        self._cyberq_name_key = cyberq_name_key
        self._attr_name = key
        self._attr_translation_key = translation_key
        if translation_placeholders is not None:
            self._attr_translation_placeholders = translation_placeholders
        self._attr_icon = icon
        self._attr_options = options
        self._attr_entity_registry_enabled_default = not disabled

        try:
            self._attr_current_option = getattr(
                self.coordinator.data, self._cyberq_name_key
            ).value
        except AttributeError:
            self._attr_current_option = None
        self._attr_unique_id = (
            f"{self.coordinator.device_info['name']}_{self.translation_key}"
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator.."""
        try:
            self._attr_current_option = getattr(
                self.coordinator.data, self._cyberq_name_key
            ).value
        except AttributeError:
            self._attr_current_option = None
        self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Set new target temperature."""
        await self.coordinator.cyberq.async_set(self._cyberq_name_key, option)
        await self.coordinator.async_request_refresh()
        self.async_write_ha_state()
