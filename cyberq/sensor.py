"""Support for the Cyberq service."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
import logging

from homeassistant.components.sensor import (
    ENTITY_ID_FORMAT,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import CyberqConfigEntry, CyberqDataUpdateCoordinator
from .const import STATUS_ICONS
from .cyberq import CYBERQ_SENSORS, CyberqSensors

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class CyberqSensorEntityDescription(SensorEntityDescription):
    """A class that describes sensor entities."""

    value: Callable[[CyberqSensors], StateType | datetime]
    icon_fn: Callable[[CyberqSensors], str | None] | None = None


SENSOR_TYPES: tuple[CyberqSensorEntityDescription, ...] = (
    CyberqSensorEntityDescription(
        key="fan_speed",
        translation_key="fan_speed",
        value=lambda data: data.OUTPUT_PERCENT.value,
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:fan",
    ),
    CyberqSensorEntityDescription(
        key="pit_status",
        translation_key="cook_status",
        translation_placeholders={"cook_name": "Pit"},
        value=lambda data: data.COOK_STATUS.value,
        device_class=SensorDeviceClass.ENUM,
        options=CYBERQ_SENSORS["COOK_STATUS"].values,
        icon_fn=lambda data: STATUS_ICONS.get(data.COOK_STATUS.index),
    ),
    CyberqSensorEntityDescription(
        key="probe1_status",
        translation_key="cook_status",
        translation_placeholders={"cook_name": "Probe 1"},
        value=lambda data: data.FOOD1_STATUS.value,
        icon_fn=lambda data: STATUS_ICONS.get(data.FOOD1_STATUS.index),
        device_class=SensorDeviceClass.ENUM,
        options=CYBERQ_SENSORS["FOOD1_STATUS"].values,
    ),
    CyberqSensorEntityDescription(
        key="probe2_status",
        translation_key="cook_status",
        translation_placeholders={"cook_name": "Probe 2"},
        value=lambda data: data.FOOD2_STATUS.value,
        icon_fn=lambda data: STATUS_ICONS.get(data.FOOD3_STATUS.index),
        device_class=SensorDeviceClass.ENUM,
        options=CYBERQ_SENSORS["FOOD2_STATUS"].values,
    ),
    CyberqSensorEntityDescription(
        key="probe3_status",
        translation_key="cook_status",
        value=lambda data: data.FOOD3_STATUS.value,
        icon_fn=lambda data: STATUS_ICONS.get(data.FOOD3_STATUS.index),
        translation_placeholders={"cook_name": "Probe 3"},
        device_class=SensorDeviceClass.ENUM,
        options=CYBERQ_SENSORS["FOOD3_STATUS"].values,
    ),
    CyberqSensorEntityDescription(
        key="timer_status",
        translation_key="timer_status",
        value=lambda data: data.TIMER_STATUS.value,
        device_class=SensorDeviceClass.ENUM,
        options=CYBERQ_SENSORS["TIMER_STATUS"].values,
        entity_registry_enabled_default=False,
    ),
    CyberqSensorEntityDescription(
        key="timer_curr",
        translation_key="timer_curr",
        value=lambda data: data.TIMER_CURR.value,
        icon="mdi:timer",
        entity_registry_enabled_default=False,
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
        CyberqSensor(coordinator, description)
        for description in SENSOR_TYPES
        if description.value(coordinator.data) is not None
    )


class CyberqSensor(CoordinatorEntity[CyberqDataUpdateCoordinator], SensorEntity):
    """Define an Cyberq sensor."""

    _attr_has_entity_name = True
    entity_description: CyberqSensorEntityDescription

    def __init__(
        self,
        coordinator: CyberqDataUpdateCoordinator,
        description: CyberqSensorEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_device_info = coordinator.device_info
        self._attr_native_value = description.value(coordinator.data)
        self._attr_icon = description.icon
        self._attr_unique_id = f"{coordinator.device_info['name']}_{description.key}"
        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, self.unique_id, hass=coordinator.hass
        )
        self.entity_description = description

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.entity_description.value(self.coordinator.data)
        if self.entity_description.icon_fn is not None:
            self._attr_icon = self.entity_description.icon_fn(self.coordinator.data)
        self.async_write_ha_state()
