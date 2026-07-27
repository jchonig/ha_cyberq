"""
Constants for the BBQ Guru CyberQ Integration integration.

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

from datetime import timedelta
from typing import Final

DOMAIN: Final = "cyberq"

UPDATE_INTERVAL: Final = timedelta(seconds=5)


STATUS_ICONS: Final = {
    0: "mdi:fire",
    1: "mdi:thermometer-high",
    2: "mdi:thermometer-low",
    3: "mdi:check-circle",
    4: "mdi:thermometer-alert",
    5: "mdi:pause-circle",
    6: "mdi:bell-ring",
    7: "mdi:power",
}

TIMERACTION_ICONS: Final = {
    "No Action": "mdi:timer-off",
    "Hold": "mdi:pause-circle",
    "Alarm": "mdi:bell-ring",
    "Shutdown": "mdi:power",
}
