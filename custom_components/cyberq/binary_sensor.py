"""Support for the Cyberq service."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    ENTITY_ID_FORMAT,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import CyberqConfigEntry, CyberqDataUpdateCoordinator
from .cyberq import CyberqSensors

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class CyberqBinarySensorEntityDescription(BinarySensorEntityDescription):
    """A class that describes binary sensor entities."""

    exists_fn: Callable[[CyberqSensors], bool] = lambda _: True
    value_fn: Callable[[CyberqSensors], bool | None]


BINARY_SENSORS: tuple[CyberqBinarySensorEntityDescription, ...] = (
    CyberqBinarySensorEntityDescription(
        key="fan_shorted",
        translation_key="fan_shorted",
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:fan-alert",
        value_fn=lambda data: data.FAN_SHORTED.value,
        exists_fn=lambda data: hasattr(data, "FAN_SHORTED"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CyberqConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add Cyberq entities from a config_entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        CyberqBinarySensor(coordinator, description)
        for description in BINARY_SENSORS
        if description.exists_fn(coordinator.data)
    )


class CyberqBinarySensor(
    CoordinatorEntity[CyberqDataUpdateCoordinator], BinarySensorEntity
):
    """Define an Cyberq binary sensor."""

    _attr_has_entity_name = True
    entity_description: CyberqBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: CyberqDataUpdateCoordinator,
        description: CyberqBinarySensorEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_device_info = coordinator.device_info
        self._attr_native_value = description.value_fn(coordinator.data)
        self._attr_icon = description.icon
        self._attr_unique_id = (
            f"{coordinator.device_info['serial_number']}_{description.key}"
        )
        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, self.unique_id, hass=coordinator.hass
        )
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.entity_description.value_fn(
            self.coordinator.data
        )
        self.async_write_ha_state()
