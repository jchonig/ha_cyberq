# HomeAssistant Integration for BBQ Guru Cyberq Cloud and Cyberq WiFi

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

![Project Maintenance][maintenance-shield]

[![Community Forum][forum-shield]][forum]

The [ha_cyberq] {% term integration %} is used to integrate the [BBQ
Guru][bbq_guru] CyberQ Cloud and CyberQ WiFi automatic BBQ temperature controllers.

The BBQ Guru CyberQ Cloud and WiFi are discontinued products.
Information about these controllers can be found on the [BBQ Guru Support Pages][bbq_guru_support]

**This integration will set up the following platforms.**

| Platform        | CyberQ sensors supported                                                                                 |
|-----------------|----------------------------------------------------------------------------------------------------------|
| `binary_sensor` | `FAN_SHORTED`                                                                                            |
| `climate`       | `COOK_TEMP`, `COOK_SET`, `FOOD1_TEMP`, `FOOD1_SET`, `FOOD2_TEMP`, `FOOD2_SET`, `FOOD3_TEMP`, `FOOD3_SET` |
| `number`        | `COOK_PROPBAND`, `COOK_CYCTIME`, `ALARMDEV`, `LCD_BACKLIGHT`, `LCD_CONTRAST`, `COOKHOLD`                 |
| `select`        | `COOK_RAMP`, `DEG_UNITS`, `ALARM_BEEPS`, `TIMEOUT_ACTION`                                                |
| `sensor`        | `FAN_SPEED`, `COOK_STATUS`, `FOOD1_STATUS`, `FOOD2_STATUS`, `FOOD3_STATUS`, `TIMER_STATUS`, `TIMER_CURR` |
| `switch`        | `OPENDETECT`, `MENU_SCROLLING`, `KEY_BEEPS`                                                              |
| `text`          | `COOK_NAME`, `FOOD1_NAME`, `FOOD2_NAME`, `FOOD3_NAME`                                                    |

## Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
1. If you do not have a `custom_components` directory (folder) there, you need to create it.
1. In the `custom_components` directory (folder) create a new folder called `ha_cyberq`.
1. Download _all_ the files from the `custom_components/ha_cyberq/` directory (folder) in this repository.
1. Place the files you downloaded in the new directory (folder) you created.
1. Restart Home Assistant
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "CyberQ"

## Prerequisites

1. Follow the instructions for your device found on the [BBQ Guru
Support Pages][bbq_guru_support] to connect your device to your WiFi
network in Infrastructure Mode.
1. Make note of the IP address and port number (defaults to 80) of
   your CyberQ.
   
{% include integrations/config_flow.md %}

## Removing the integration

This integration follows standard integration removal. No extra steps are required.

{% include integrations/remove_device_service.md %}

After deleting the integration, go to the app of the manufacturer and remove the Home Assistant integration from there as well.

<!---->

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***

[bbq_guru]: https://www.bbqguru.com
[bbq_guru_support]: https://www.bbqguru.com/support/
[ha_cyberq]: https://github.com/jchonig/ha_cyberq
[commits-shield]: https://img.shields.io/github/commit-activity/y/jchonig/ha_cyberq?style=for-the-badge
[commits]: https://github.com/jchonig/ha_cyberq/commits/main
[exampleimg]: example.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/jchonig/ha_cyberq.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Jeffrey%20Honig%20%40jchonig-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/jchonig/ha_cyberq.svg?style=for-the-badge
[releases]: https://github.com/jchonig/ha_cyberq/releases
