"""Cyberq implementation of temperature probes as number devices."""

from __future__ import annotations

import logging

from homeassistant.components.number import NumberDeviceClass, NumberEntity
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfTemperature,
    UnitOfTime,
)
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
            CyberqNumber(
                coordinator,
                translation_key="cook_propband",
                icon="mdi:thermometer-lines",
                cyberq_name_key="COOK_PROPBAND",
                step=1,
                device_class=NumberDeviceClass.TEMPERATURE,
                unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
                disabled=True,
            ),
            CyberqNumber(
                coordinator,
                translation_key="cook_cyctime",
                icon="mdi:fan-clock",
                cyberq_name_key="COOK_CYCTIME",
                step=1,
                unit_of_measurement=UnitOfTime.SECONDS,
                disabled=True,
            ),
            CyberqNumber(
                coordinator,
                translation_key="alarmdev",
                icon="mdi:thermometer-alert",
                cyberq_name_key="ALARMDEV",
                step=1,
                device_class=NumberDeviceClass.TEMPERATURE,
                unit_of_measurement=UnitOfTime.SECONDS,
                disabled=True,
            ),
            CyberqNumber(
                coordinator,
                translation_key="lcd_backlight",
                icon="mdi:brightness-5",
                cyberq_name_key="LCD_BACKLIGHT",
                step=1,
                unit_of_measurement=PERCENTAGE,
                disabled=True,
            ),
            CyberqNumber(
                coordinator,
                translation_key="lcd_contrast",
                icon="mdi:brightness-6",
                cyberq_name_key="LCD_CONTRAST",
                step=1,
                unit_of_measurement=PERCENTAGE,
                disabled=True,
            ),
            CyberqNumber(
                coordinator,
                translation_key="cook_hold",
                icon="mdi:thermometer",
                cyberq_name_key="COOKHOLD",
                step=0.1,
                device_class=NumberDeviceClass.TEMPERATURE,
                unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
                disabled=True,
            ),
        ]
    )


class CyberqNumber(CoordinatorEntity[CyberqDataUpdateCoordinator], NumberEntity):
    """Representation of a Cyberq temperature probe as a thermostat ."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: CyberqDataUpdateCoordinator,
        *,
        icon: str,
        cyberq_name_key: str,
        step: float,
        unit_of_measurement: str,
        disabled: bool = False,
        device_class: NumberDeviceClass | None = None,
        translation_key: str | None = None,
    ) -> None:
        """Initialize the number device."""
        super().__init__(coordinator)
        self._attr_device_info = coordinator.device_info

        self._cyberq_name_key = cyberq_name_key
        self._attr_device_class = device_class
        self._attr_translation_key = translation_key
        self._attr_icon = icon
        self._attr_native_min_value = CYBERQ_SENSORS[self._cyberq_name_key].min
        self._attr_native_max_value = CYBERQ_SENSORS[self._cyberq_name_key].max
        self._attr_native_step = step
        self._attr_native_unit_of_measurement = unit_of_measurement
        self._attr_entity_registry_enabled_default = not disabled

        try:
            self._attr_native_value = getattr(
                self.coordinator.data, self._cyberq_name_key
            ).value
        except AttributeError:
            self._attr_native_value = None
        self._attr_unique_id = (
            f"{self.coordinator.device_info['serial_number']}_{translation_key}"
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator.."""
        try:
            self._attr_native_value = getattr(
                self.coordinator.data, self._cyberq_name_key
            ).value
        except AttributeError:
            self._attr_native_value = None
        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        """Set new target temperature."""
        await self.coordinator.cyberq.async_set(self._cyberq_name_key, value)
        await self.coordinator.async_request_refresh()
        self.async_write_ha_state()
