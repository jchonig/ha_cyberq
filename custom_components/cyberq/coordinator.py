"""Coordinator for CyberQ integration."""

import logging
from asyncio import timeout
from xml.parsers.expat import ExpatError

from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, UPDATE_INTERVAL
from .cyberq import CyberqDevice, CyberqSensors

_LOGGER = logging.getLogger(__name__)


class CyberqDataUpdateCoordinator(DataUpdateCoordinator[CyberqSensors]):
    """Class to manage fetching Cyberq data from the controller."""

    device_info: DeviceInfo

    def __init__(self, hass: HomeAssistant, cyberq: CyberqDevice) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
            always_update=False,
        )
        self._device = cyberq
        self.cyberq = cyberq

    async def _async_update_data(self) -> CyberqSensors:
        """Update data via library."""
        try:
            async with timeout(20):
                data = await self._device.async_update()
                _LOGGER.debug(str(data))
        except (ExpatError, ConnectionError) as error:
            raise UpdateFailed(error) from error
        return data
