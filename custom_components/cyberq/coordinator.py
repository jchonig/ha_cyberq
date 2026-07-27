"""
Coordinator for CyberQ integration.

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

import logging
from asyncio import timeout
from xml.parsers.expat import ExpatError

import aiohttp
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
        except (
            TimeoutError,
            ExpatError,
            ConnectionError,
            aiohttp.ClientError,
        ) as error:
            raise UpdateFailed(error) from error
        return data
