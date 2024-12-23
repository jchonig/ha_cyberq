"""Cyberq implementation of temperature probes as climate devices."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ENTITY_ID_FORMAT,
    PRECISION_TENTHS,
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import CyberqConfigEntry, CyberqDataUpdateCoordinator
from .const import STATUS_ICONS
from .cyberq import CYBERQ_SENSORS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CyberqConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the demo climate platform."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            CyberqClimate(
                coordinator,
                cyberq_name_key="COOK_NAME",
                cyberq_temp_key="COOK_TEMP",
                cyberq_setpoint_key="COOK_SET",
                cyberq_status_key="COOK_STATUS",
                prefix="pit",
                translation_placeholders={"cook_name": "Pit"},
            ),
            CyberqClimate(
                coordinator,
                cyberq_name_key="FOOD1_NAME",
                cyberq_temp_key="FOOD1_TEMP",
                cyberq_setpoint_key="FOOD1_SET",
                cyberq_status_key="FOOD1_STATUS",
                prefix="food1",
                translation_placeholders={"cook_name": "Food 1"},
            ),
            CyberqClimate(
                coordinator,
                cyberq_name_key="FOOD3_NAME",
                cyberq_temp_key="FOOD3_TEMP",
                cyberq_setpoint_key="FOOD3_SET",
                cyberq_status_key="FOOD3_STATUS",
                prefix="food2",
                translation_placeholders={"cook_name": "Food 2"},
            ),
            CyberqClimate(
                coordinator,
                cyberq_name_key="FOOD3_NAME",
                cyberq_temp_key="FOOD3_TEMP",
                cyberq_setpoint_key="FOOD3_SET",
                cyberq_status_key="FOOD3_STATUS",
                prefix="food3",
                translation_placeholders={"cook_name": "Food 3"},
            ),
        ]
    )


class CyberqClimate(CoordinatorEntity[CyberqDataUpdateCoordinator], ClimateEntity):
    """Representation of a Cyberq temperature probe as a thermostat ."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_hvac_action = None
    _attr_hvac_mode = HVACMode.HEAT
    _attr_hvac_modes = [HVACMode.HEAT]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_prescision = PRECISION_TENTHS
    _attr_temperature_unit = UnitOfTemperature.FAHRENHEIT

    def __init__(
        self,
        coordinator: CyberqDataUpdateCoordinator,
        prefix: str,
        translation_placeholders: dict[str, str],
        cyberq_name_key: str,
        cyberq_temp_key: str,
        cyberq_setpoint_key: str,
        cyberq_status_key: str,
    ) -> None:
        """Initialize the climate device."""
        super().__init__(coordinator)
        self._attr_device_info = coordinator.device_info
        self._cyberq_name_key = cyberq_name_key
        self._cyberq_temp_key = cyberq_temp_key
        self._cyberq_setpoint_key = cyberq_setpoint_key
        self._cyberq_status_key = cyberq_status_key
        self._attr_translation_key = "probe"
        self._attr_translation_placeholders = translation_placeholders
        self._attr_max_temp = float(str(CYBERQ_SENSORS[self._cyberq_setpoint_key].max))
        self._attr_min_temp = float(str(CYBERQ_SENSORS[self._cyberq_setpoint_key].min))

        self._update_sub()
        self._attr_unique_id = f"{self.coordinator.device_info['name']}_{prefix}_probe"
        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT, self.unique_id, hass=coordinator.hass
        )

    def _update_sub(self) -> None:
        self._attr_target_temperature = float(
            getattr(self.coordinator.data, self._cyberq_setpoint_key).value
        )

        try:
            self._attr_current_temperature = float(
                getattr(self.coordinator.data, self._cyberq_temp_key).value
            )
        except ValueError:
            self._attr_current_temperature = None
        if self._attr_target_temperature == self._attr_min_temp or getattr(
            self.coordinator.data, self._cyberq_status_key
        ).value in ("error", "shutdown"):
            self._attr_hvac_mode = HVACMode.OFF
        self._attr_icon = STATUS_ICONS[
            getattr(self.coordinator.data, self._cyberq_status_key).index
        ]

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator.."""
        self._update_sub()
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwags: Any) -> None:
        """Set new target temperature."""
        await self.coordinator.cyberq.async_set(
            self._cyberq_setpoint_key, kwags["temperature"]
        )
        await self.coordinator.async_request_refresh()
        self.async_write_ha_state()
