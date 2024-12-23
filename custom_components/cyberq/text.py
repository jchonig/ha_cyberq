"""Cyberq implementation of temperature probes as Text devices."""

from __future__ import annotations

from collections.abc import Mapping
import logging

from homeassistant.components.text import ENTITY_ID_FORMAT, TextEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import CyberqConfigEntry, CyberqDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CyberqConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the demo text platform."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            Cyberqtext(
                coordinator,
                cyberq_name_key="COOK_NAME",
                icon="mdi:fire",
                prefix="cook",
                entity_category=EntityCategory.CONFIG,
                translation_key="probe",
                translation_placeholders={"probe_name": "Cook"},
            ),
            Cyberqtext(
                coordinator,
                cyberq_name_key="FOOD1_NAME",
                prefix="probe1",
                translation_key="probe",
                translation_placeholders={"probe_name": "Probe 1"},
                entity_category=EntityCategory.CONFIG,
            ),
            Cyberqtext(
                coordinator,
                cyberq_name_key="FOOD2_NAME",
                prefix="probe2",
                translation_key="probe",
                translation_placeholders={"probe_name": "Probe 2"},
                entity_category=EntityCategory.CONFIG,
            ),
            Cyberqtext(
                coordinator,
                cyberq_name_key="FOOD3_NAME",
                prefix="probe3",
                translation_key="probe",
                translation_placeholders={"probe_name": "Probe 3"},
                entity_category=EntityCategory.CONFIG,
            ),
        ]
    )


class Cyberqtext(CoordinatorEntity[CyberqDataUpdateCoordinator], TextEntity):
    """Representation of a Cyberq temperature probe as a thermostat ."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: CyberqDataUpdateCoordinator,
        cyberq_name_key: str,
        prefix: str | None = None,
        icon: str = "mdi:thermometer",
        pattern: str = r"^\w[\w +]+$",
        min_length: int = 1,
        max_length: int = 20,
        translation_key: str | None = None,
        translation_placeholders: Mapping[str, str] | None = None,
        entity_category: EntityCategory | None = None,
    ) -> None:
        """Initialize the text device."""
        super().__init__(coordinator)
        self._attr_device_info = coordinator.device_info

        self._cyberq_name_key = cyberq_name_key
        self._attr_translation_key = translation_key
        if translation_placeholders is not None:
            self._attr_translation_placeholders = translation_placeholders
        self._attr_icon = icon
        self._attr_pattern = pattern
        self._attr_native_min = min_length
        self._attr_native_max = max_length
        self._attr_entity_category = entity_category

        self._attr_native_value = getattr(
            self.coordinator.data, self._cyberq_name_key
        ).value
        self._attr_unique_id = f"{self.coordinator.device_info['name']}_{prefix}_name"
        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, self.unique_id, hass=coordinator.hass
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator.."""
        self._attr_native_value = getattr(
            self.coordinator.data, self._cyberq_name_key
        ).value
        self.async_write_ha_state()

    async def async_set_value(self, value: str) -> None:
        """Set new target temperature."""
        await self.coordinator.cyberq.async_set(self._cyberq_name_key, value)
        await self.coordinator.async_request_refresh()
        self.async_write_ha_state()
