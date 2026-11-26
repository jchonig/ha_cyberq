"""
Serve the CyberQ dashboard strategy to the Home Assistant frontend.

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

from pathlib import Path
from typing import TYPE_CHECKING

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.loader import async_get_integration

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

STRATEGY_FILE = Path(__file__).parent / "www" / "cyberq_strategy.js"
STRATEGY_URL = f"/{DOMAIN}_frontend/cyberq_strategy.js"


async def async_register_frontend(hass: HomeAssistant) -> None:
    """
    Serve the dashboard strategy and load it on every frontend.

    The integration version is added to the URL so browsers and the
    companion app fetch the new file after an upgrade.
    """
    integration = await async_get_integration(hass, DOMAIN)
    await hass.http.async_register_static_paths(
        [StaticPathConfig(STRATEGY_URL, str(STRATEGY_FILE), cache_headers=True)]
    )
    add_extra_js_url(hass, f"{STRATEGY_URL}?v={integration.version}")
