"""Constants for the BBQ Guru CyberQ Integration integration."""

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
