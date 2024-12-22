# HomeAssistant Integration of BBQ Guru Cyberq Cloud and Cyberq WiFi

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

![Project Maintenance][maintenance-shield]

[![Discord][discord-shield]][discord]
[![Community Forum][forum-shield]][forum]

_Integration to integrate with [BBQ Guru CyberQ Cloud and WiFi][ha_cyberq]._

**This integration will set up the following platforms.**

Platform | Description
-- | --
`binary_sensor` | Show something `True` or `False`.
`number` | Foo.
`sensor` | Show info from blueprint API.
`select` | Foo.
`switch` | Switch something `True` or `False`.
`text` | Foo.

## Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
1. If you do not have a `custom_components` directory (folder) there, you need to create it.
1. In the `custom_components` directory (folder) create a new folder called `ha_cyberq`.
1. Download _all_ the files from the `custom_components/ha_cyberq/` directory (folder) in this repository.
1. Place the files you downloaded in the new directory (folder) you created.
1. Restart Home Assistant
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Integration blueprint"

## Configuration is done in the UI

<!---->

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***

[ha_cyberq]: https://github.com/jchonig/ha_cyberq
[commits-shield]: https://img.shields.io/github/commit-activity/y/jchonig/ha_cyberq.svg?style=for-the-badge
[commits]: https://github.com/jchonig/ha_cyberq/commits/main
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
[exampleimg]: example.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/jchonig/ha_cyberq.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Joakim%20Sørensen%20%40jchonig-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/jchonig/ha_cyberq.svg?style=for-the-badge
[releases]: https://github.com/jchonig/ha_cyberq/releases
