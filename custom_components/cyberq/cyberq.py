"""
Monitor BBQ Guru CyberQ.

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

import asyncio
import copy
import datetime
import logging
import re
import sys
import urllib.parse
from enum import StrEnum
from typing import Any, Final, Self

import aiohttp
import xmltodict

_LOGGER = logging.getLogger(__name__)

CYBERQ_TEMPERATURE_MIN: Final = 32
CYBERQ_TEMPERATURE_MAX: Final = 475
CYBERQ_PROPBAND_MIN: Final = 5
CYBERQ_PROPBAND_MAX: Final = 100
CYBERQ_CYCLETIME_MIN: Final = 1
CYBERQ_CYCLETIME_MAX: Final = 30
CYBERQ_ALARMDEV_MIN: Final = 10
CYBERQ_ALARMDEV_MAX: Final = 100
CYBERQ_LCD_MIN: Final = 0
CYBERQ_LCD_MAX: Final = 100


class Page(StrEnum):
    """Description of a CyberQ page."""

    INDEX = "index.htm"
    CONTROL = "control.htm"
    SYSTEM = "system.htm"
    WIFI = "wifi.htm"


class CyberqSensor:
    """Description of a CyberQ sensor."""

    _value: Any
    values: Any
    min_value: Any
    max_value: Any

    def __init__(
        self,
        name: str,
        *,
        alias: str | None = None,
        read_only: bool = False,
        page: Page | None = None,
    ) -> None:
        """Init a CyberQ value."""
        self.name = name
        if alias is not None:
            self._alias = alias
        self.read_only = read_only
        if page is not None:
            self._page = page

    def __str__(self) -> str:
        """Return a string representation of the sensor."""
        return f"Name: {self.name} Type: {type(self).__name__} Value: {self.value}"

    def __eq__(self, other: object) -> bool:
        """Compare."""
        if isinstance(other, CyberqSensor):
            return type(self) is type(other) and self.value == other.value
        return False

    @property
    def alias(self) -> str | None:
        """Return the alias."""
        if hasattr(self, "_alias"):
            return self._alias

        return None

    @property
    def page(self) -> str:
        """Return the page."""
        if hasattr(self, "_page"):
            return self._page

        raise ValueError(f"Page not defined for {self.name}")

    @property
    def value(self) -> Any:
        """Return the value of the sensor."""
        return self._value


class CyberqSensorBoolean(CyberqSensor):
    """Description of a CyberQ boolean sensor."""

    _value: bool

    def accept(self, value: Any) -> Self:
        """Import a value from device."""
        self._value = bool(int(value))
        return self

    def export(self, value: Any) -> Any:
        """Prep the value for setting on the device."""
        if self.read_only:
            raise ValueError(f"Read only value for {self.name}")

        return value


class CyberqSensorList(CyberqSensor):
    """Description of a CyberQ list sensor."""

    index: int
    values: list[str]

    def __init__(
        self,
        name: str,
        *,
        values: list[str],
        alias: str | None = None,
        read_only: bool = False,
        page: Page | None = None,
    ) -> None:
        """Init a CyberQ list value."""
        super().__init__(name=name, alias=alias, read_only=read_only, page=page)
        self.values = values

    def accept(self, value: Any) -> Self:
        """Import a value from device."""
        index = int(value)
        if index > len(self.values):
            raise ValueError(f"Invalid import value for {self.name}: {self.value}")
        self.index = index
        return self

    def export(self, value: Any) -> Any:
        """Prep the value for setting on the device."""
        if self.read_only:
            raise ValueError(f"Read only value for {self.name}")

        return self.values.index(value)

    def __str__(self) -> str:
        """Return a string representation of the sensor."""
        return (
            f"Name: {self.name} Type: {type(self).__name__} "
            r"Value: {self.value} Index: {self.index}"
        )

    @property
    def value(self) -> str:
        """Return the value of the sensor."""
        return self.values[int(self.index)]


class CyberqSensorNumber(CyberqSensor):
    """Description of a CyberQ number sensor."""

    _value: float

    def __init__(
        self,
        name: str,
        *,
        min_value: float,
        max_value: float,
        alias: str | None = None,
        read_only: bool = False,
        page: Page | None = None,
    ) -> None:
        """Init a CyberQ number value."""
        super().__init__(name=name, alias=alias, read_only=read_only, page=page)
        self.min_value = min_value
        self.max_value = max_value

    def accept(self, value: Any) -> Self:
        """Import a value from device."""
        self._value = int(value)
        return self

    def export(self, value: Any) -> Any:
        """Prep the value for setting on the device."""
        if self.read_only:
            raise ValueError(f"Read only value for {self.name}")

        if value < self.min_value or value > self.max_value:
            raise ValueError(f"Invalid value for {self.name}: {value}")
        return value


class CyberqSensorString(CyberqSensor):
    """Description of a CyberQ string sensor."""

    _value: str

    def accept(self, value: Any) -> Self:
        """Import a value from device."""
        self._value = value
        return self

    def export(self, value: Any) -> Any:
        """Prep the value for setting on the device."""
        if self.read_only:
            raise ValueError(f"Read only value for {self.name}")

        return value


class CyberqSensorTimer(CyberqSensor):
    """Description of a CyberQ timer sensor."""

    _TIMER_RE = re.compile(r"^(?P<hours>\d{2}):(?P<minutes>\d{2}):(?P<seconds>\d{2})$")

    _value: str

    def accept(self, value: Any) -> Self:
        """Import a value from device."""
        match = self._TIMER_RE.match(value)
        if not match:
            raise ValueError(f"Invalid timer value for {self.name}: {value}")
        self._value = value
        return self

    def export(self, value: Any) -> Any:
        """Prep the value for setting on the device."""
        if self.read_only:
            raise ValueError(f"Read only value for {self.name}")

        return value


class CyberqSensorTemperature(CyberqSensor):
    """Description of a CyberQ temperature sensor."""

    _value: float
    min_value = CYBERQ_TEMPERATURE_MIN
    max_value = CYBERQ_TEMPERATURE_MAX

    def accept(self, value: Any) -> Self:
        """Import a value from device."""
        try:
            self._value = float(value) / 10.0
        except ValueError:
            self._value = value
        return self

    def export(self, value: Any) -> Any:
        """Prep the value for setting on the device."""
        if self.read_only:
            raise ValueError(f"Read only value for {self.name}")

        if value < self.min_value or value > self.max_value:
            raise ValueError(f"Invalid value for {self.name}: {value}")
        return int(value)


_STATUS_VALUES: Final = [
    "ok",
    "high",
    "low",
    "done",
    "error",
    "hold",
    "alarm",
    "shutdown",
]

CYBERQ_SENSORS: Final = {
    "ALARM_BEEPS": CyberqSensorList(
        "ALARM_BEEPS", page=Page.SYSTEM, values=["0", "1", "2", "3", "4", "5"]
    ),
    "ALARMDEV": CyberqSensorNumber(
        "ALARMDEV",
        page=Page.CONTROL,
        min_value=CYBERQ_ALARMDEV_MIN,
        max_value=CYBERQ_ALARMDEV_MAX,
    ),
    "COOK_CYCTIME": CyberqSensorNumber(
        "COOK_CYCTIME",
        alias="CYCTIME",
        page=Page.INDEX,
        min_value=CYBERQ_CYCLETIME_MIN,
        max_value=CYBERQ_CYCLETIME_MAX,
    ),
    "COOK_NAME": CyberqSensorString("COOK_NAME", page=Page.INDEX),
    "COOK_PROPBAND": CyberqSensorNumber(
        "COOK_PROPBAND",
        alias="PROPBAND",
        page=Page.INDEX,
        min_value=CYBERQ_PROPBAND_MIN,
        max_value=CYBERQ_PROPBAND_MAX,
    ),
    "COOK_RAMP": CyberqSensorList(
        "COOK_RAMP",
        page=Page.CONTROL,
        values=["None", "Food 1", "Food 2", "Food 3"],
    ),
    "COOK_SET": CyberqSensorTemperature("COOK_SET", page=Page.INDEX),
    "COOK_STATUS": CyberqSensorList(
        "COOK_STATUS", values=_STATUS_VALUES, read_only=True
    ),
    "COOK_TEMP": CyberqSensorTemperature("COOK_TEMP", read_only=True),
    "COOKHOLD": CyberqSensorTemperature("COOKHOLD", page=Page.CONTROL),
    "DEG_UNITS": CyberqSensorList(
        "DEG_UNITS", page=Page.SYSTEM, values=["Celsius", "Fahrenheit"]
    ),
    "FAN_SHORTED": CyberqSensorBoolean("FAN_SHORTED", read_only=True),
    "FOOD1_NAME": CyberqSensorString("FOOD1_NAME", page=Page.INDEX),
    "FOOD1_SET": CyberqSensorTemperature("FOOD1_SET", page=Page.INDEX),
    "FOOD1_STATUS": CyberqSensorList(
        "FOOD1_STATUS", values=_STATUS_VALUES, read_only=True
    ),
    "FOOD1_TEMP": CyberqSensorTemperature("FOOD1_TEMP", read_only=True),
    "FOOD2_NAME": CyberqSensorString("FOOD2_NAME", page=Page.INDEX),
    "FOOD2_SET": CyberqSensorTemperature("FOOD2_SET", page=Page.INDEX),
    "FOOD2_STATUS": CyberqSensorList(
        "FOOD2_STATUS", values=_STATUS_VALUES, read_only=True
    ),
    "FOOD2_TEMP": CyberqSensorTemperature("FOOD2_TEMP", read_only=True),
    "FOOD3_NAME": CyberqSensorString("FOOD3_NAME", page=Page.INDEX),
    "FOOD3_SET": CyberqSensorTemperature("FOOD3_SET", page=Page.INDEX),
    "FOOD3_STATUS": CyberqSensorList(
        "FOOD3_STATUS", values=_STATUS_VALUES, read_only=True
    ),
    "FOOD3_TEMP": CyberqSensorTemperature("FOOD3_TEMP", read_only=True),
    "KEY_BEEPS": CyberqSensorBoolean("KEY_BEEPS", page=Page.SYSTEM),
    "LCD_BACKLIGHT": CyberqSensorNumber(
        "LCD_BACKLIGHT",
        page=Page.SYSTEM,
        min_value=CYBERQ_LCD_MIN,
        max_value=CYBERQ_LCD_MAX,
    ),
    "LCD_CONTRAST": CyberqSensorNumber(
        "LCD_CONTRAST",
        page=Page.SYSTEM,
        min_value=CYBERQ_LCD_MIN,
        max_value=CYBERQ_LCD_MAX,
    ),
    "MENU_SCROLLING": CyberqSensorBoolean("MENU_SCROLLING", page=Page.SYSTEM),
    "OPENDETECT": CyberqSensorBoolean("OPENDETECT", page=Page.CONTROL),
    "OUTPUT_PERCENT": CyberqSensorNumber(
        "OUTPUT_PERCENT", min_value=0, max_value=100, read_only=True
    ),
    "TIMEOUT_ACTION": CyberqSensorList(
        "TIMEOUT_ACTION",
        page=Page.CONTROL,
        values=["No Action", "Hold", "Alarm", "Shutdown"],
    ),
    "TIMER_CURR": CyberqSensorTimer("TIMER_CURR", read_only=True),
    "TIMER_STATUS": CyberqSensorList(
        "TIMER_STATUS", values=_STATUS_VALUES, read_only=True
    ),
}


class CyberqSensors:
    """Sensor data."""

    _NAME_RE = re.compile(r"(COOK|FOOD[123])_NAME$")
    _TEMP_RE = re.compile(r"(COOK|FOOD[123])_(SET|TEMP)$")
    _STATUS_RE = re.compile(r"(COOK|FOOD[123]|TIMER)_STATUS$")
    _STATUS = ("OK", "HIGH", "LOW", "DONE", "ERROR", "HOLD", "ALARM", "SHUTDOWN")
    _TIMER_RE = re.compile(r"^(?P<hours>\d{2}):(?P<minutes>\d{2}):(?P<seconds>\d{2})$")

    def __init__(self) -> None:
        """Init sensors."""
        self._sensors: dict[str, Any] = {}

    def __deepcopy__(self, memo: Any) -> Any:
        """
        Deep copy.

        Prevents __getattr__ from recursing as new struct is created.
        """
        new = CyberqSensors()
        new._sensors = copy.deepcopy(self._sensors)
        return new

    def __eq__(self, other: object) -> bool:
        """Compare."""
        if not isinstance(other, CyberqSensors):
            return False

        return self._sensors == other._sensors

    def __getattr__(self, key: str) -> Any:
        """Retrieve a sensor value."""
        if key in self._sensors:
            return self._sensors[key]
        raise AttributeError(f"CyberqSensor: Invalid key: {key}")

    def accept(self, key: str, value: str) -> None:
        """Set a value read from device, convert as needed."""
        if key not in CYBERQ_SENSORS:
            for sensor in CYBERQ_SENSORS.values():
                if sensor.alias == key:
                    key = sensor.name
                    break
            else:
                raise AttributeError(f"CyberqSensor.accept: Invalid key: {key}")

        sensor = copy.deepcopy(CYBERQ_SENSORS[key])
        self._sensors[sensor.name] = sensor.accept(value)  # type: ignore[attr-defined]

    def __str__(self) -> str:
        """Return a string representation of the sensors."""
        return "\n\t".join(
            [f"{key}={value}" for key, value in sorted(self._sensors.items())]
        )

    @property
    def sensors(self) -> dict[str, Any]:
        """Return the sensors."""
        return self._sensors


class CyberqDevice:
    """Monitor a BBQ Guru CyberQ."""

    _PARSE_VALUE_RE = re.compile(
        r"\s*document\.mainForm\.(?P<key>[A-Z1-3]+(_[A-Z]+)?)\.(selectedIndex|value)"
        r" = (?P<value>[^;]+);$"
    )
    _PARSE_TEMP_RE = re.compile(
        r"\s*document\.mainForm\._(?P<key>[A-Z1-3]+_SET|COOKHOLD)\.value"
        r" = TempPICToHTML\((?P<value>\d+),0\);}?$"
    )
    _MAC_RE = re.compile(r"\b(?P<mac>([A-Z0-9]{2}:){5}[A-Z0-9]{2})\b")
    _VERSIONS_RE = re.compile(
        r"FW Version<.*>(?P<sw_version>[0-9\.]+),\s*(?P<hw_version>[0-9\.]+)<"
    )
    _NAME_RE = re.compile(r"^[\w ]+$")

    mac: str = ""
    serial_number: str = ""
    sw_version: str = ""
    hw_version: str = ""
    manufacturer: str = "BBQ Guru"
    _sensors: CyberqSensors = CyberqSensors()
    cyberq_cloud: bool = False

    def __init__(
        self, host: str, session: aiohttp.ClientSession, port: int = 80
    ) -> None:
        """Init the CyberQ."""
        self._session = session
        self.host = host
        self.port = port
        self._base_url = f"http://{host}:{port}"
        self._last_config: datetime.datetime | None = None

        self._index_url = urllib.parse.urljoin(self._base_url, "index.htm")
        self._status_url = urllib.parse.urljoin(self._base_url, "status.xml")
        self._config_xml = urllib.parse.urljoin(self._base_url, "config.xml")
        self._wifi_url = urllib.parse.urljoin(self._base_url, "wifi.htm")

    async def _post(self, url: str, data: dict) -> str:
        """Update a value."""
        async with self._session.post(url, data=data) as response:
            response.raise_for_status()
            return await response.text()

    async def _get(self, url: str) -> str:
        """Get a response data."""
        async with self._session.get(url) as response:
            response.raise_for_status()
            return await response.text()

    async def _wifi(self) -> None:
        """Read WiFi config page."""
        text = await self._get(self._wifi_url)
        for line in text.split("\r\n"):
            match = self._MAC_RE.search(line)
            if match:
                self.mac = match.group("mac")
                self.serial_number = "".join(self.mac.split(":")[4:6])
                continue
            match = self._VERSIONS_RE.search(line)
            if match:
                self.sw_version = match.group("sw_version")
                self.hw_version = match.group("hw_version")

    def _parse_html(self, response: str) -> None:
        """Parse the HTML response."""
        _LOGGER.debug("Cyberq._parse_html")
        for line in response.split("\r\n"):
            match = self._PARSE_VALUE_RE.match(line)
            if match:
                if match.group("value").startswith("TempHTMLToPIC"):
                    continue
                self._sensors.accept(
                    match.group("key"), match.group("value").strip('"')
                )
                _LOGGER.debug(
                    "Cyberq._parse_html %s=%s",
                    match.group("key"),
                    match.group("value").strip('"'),
                )
                continue
            match = self._PARSE_TEMP_RE.match(line)
            if match:
                self._sensors.accept(match.group("key"), match.group("value"))
        _LOGGER.debug("Cyberq._parse_html done")

    async def _config(self, response: str | None = None) -> None:
        """Read config data."""
        xml_config = None
        if self.mac == "":
            try:
                xml_config = await self._get(self._config_xml)
            except aiohttp.client_exceptions.ClientResponseError:
                self.cyberq_cloud = True
                await self._wifi()

        if not self.cyberq_cloud:
            if not xml_config:
                xml_config = await self._get(self._config_xml)
            for key, value in xmltodict.parse(xml_config)["nutcallstatus"].items():
                if key in ["COOK", "FOOD1", "FOOD2", "FOOD3"]:
                    for value_key in (f"{key}_NAME", f"{key}_SET"):
                        self._sensors.accept(value_key, value[value_key])
                    continue
                if key == "WIFI":
                    self.mac = value["MAC"]
                    self.serial_number = "".join(self.mac.split(":")[4:6])
                    continue
                if key == "FWVER":
                    self.sw_version = value
                    continue
                if key == "CONTROL":
                    for value_key in (
                        "TIMEOUT_ACTION",
                        "COOKHOLD",
                        "ALARMDEV",
                        "OPENDETECT",
                    ):
                        self._sensors.accept(value_key, value[value_key])
                    continue
                if key == "SYSTEM":
                    for value_key in (
                        "MENU_SCROLLING",
                        "LCD_BACKLIGHT",
                        "LCD_CONTRAST",
                        "ALARM_BEEPS",
                        "KEY_BEEPS",
                    ):
                        self._sensors.accept(value_key, value[value_key])
                    continue
            return

        if response is None:
            _LOGGER.debug("%s _config", self.serial_number)
            for page in ("control.htm", "index.htm", "system.htm"):
                _LOGGER.debug(
                    "Cyberq._config: reading %s (%s)",
                    page,
                    urllib.parse.urljoin(self._base_url, page),
                )
                self._parse_html(
                    await self._get(urllib.parse.urljoin(self._base_url, page))
                )
                _LOGGER.debug("Cyberq._config: done %s", page)
        else:
            # Response was provided
            _LOGGER.debug("%s _config w/response", self.serial_number)
            self._parse_html(response)

        self._last_config = datetime.datetime.now(tz=datetime.UTC)

    async def async_set(self, key: str, value: Any) -> bool:
        """Set a value from user input."""
        _LOGGER.debug("Setting %s %s", key, value)
        sensor = getattr(self._sensors, key)
        _value = sensor.export(value)
        _key = sensor.alias if self.cyberq_cloud and sensor.alias is not None else key

        _LOGGER.warning("Cyberq.async_set(%s, %s)", _key, _value)

        response = await self._post(
            urllib.parse.urljoin(self._base_url, sensor.page), data={_key: _value}
        )
        await self._config(response)

        return True

    async def async_update(self) -> CyberqSensors:
        """Refresh the data."""
        self._sensors = copy.deepcopy(self._sensors)

        # Read config every 10 minutes
        if self._last_config is None or self._last_config + datetime.timedelta(
            minutes=10
        ) < datetime.datetime.now(tz=datetime.UTC):
            await self._config()

        response = await self._get(self._status_url)

        for key, value in xmltodict.parse(response)["nutcstatus"].items():
            if key == "comment":
                continue
            self._sensors.accept(key, value)

        return self._sensors

    def _valid_name(self, name: str) -> bool:
        match = self._NAME_RE.match(name)
        return match is not None

    def _valid_temp(self, temp: str) -> bool:
        try:
            itemp = float(temp)
        except ValueError:
            return False
        return CYBERQ_TEMPERATURE_MIN <= itemp <= CYBERQ_TEMPERATURE_MAX

    @property
    def sensors(self) -> CyberqSensors:
        """Return the sensors."""
        return self._sensors

    @property
    def model(self) -> str:
        """Return the model."""
        return "CyberQ Cloud" if self.cyberq_cloud else "CyberQ WiFi"

    @property
    def name(self) -> str:
        """Return the name of the device."""
        return f"CyberQ {self.serial_number}"

    def __str__(self) -> str:
        """Return a string representation of the CyberQ."""
        return f"Cyberq {self._base_url}: serial {self.serial_number} MAC: {self.mac}"


if __name__ == "__main__":
    import argparse

    def parse_args() -> argparse.Namespace:
        """Parse command line arguments."""
        parser = argparse.ArgumentParser(description="Send pushbullet messages")

        # Debugging
        group = parser.add_argument_group("Debugging options")
        group.add_argument(
            "-d",
            "--debug",
            dest="debug",
            default=False,
            action="store_true",
            help="print debugging messages",
        )
        group.add_argument(
            "--nodebug",
            dest="debug",
            action="store_false",
            help="print debugging messages",
        )
        group.add_argument(
            "-v",
            "--verbose",
            dest="verbose",
            default=False,
            action="store_true",
            help="print verbose messages",
        )
        group.add_argument(
            "-n",
            "--noop",
            dest="noop",
            default=False,
            action="store_true",
            help="Don't send notifications, just list what we are going to do",
        )

        group = parser.add_argument_group("Ooptions")
        group.add_argument(
            "--host",
            "-H",
            dest="host",
            required=True,
            help="Address of cyberq controller",
        )
        group.add_argument(
            "--port",
            "-p",
            dest="port",
            type=int,
            default=80,
            help="Port the controller is listening on",
        )
        group.add_argument(
            "settings",
            default=[],
            nargs="*",
            help="Settings in the form of COOK_SET=300, COOK_NAME='Smoked Turkey'",
        )

        # Parse args
        options = parser.parse_args()

        # --test implies --verbose
        if options.noop:
            options.debug = True

        # Init _LOGGER
        init_logging(options)

        return options

    def init_logging(options: argparse.Namespace) -> None:
        """Set up logging, based on command line options."""
        _LOGGER.handlers = []
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s %(levelname)-8s %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        _LOGGER.addHandler(handler)
        if options.debug:
            _LOGGER.setLevel("DEBUG")
        elif options.verbose:
            _LOGGER.setLevel("INFO")
        else:
            _LOGGER.setLevel("WARNING")

    async def main() -> None:
        """Test function."""
        options = parse_args()

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10)
        ) as session:
            cyberq = CyberqDevice(options.host, port=options.port, session=session)
            await cyberq.async_update()

            if options.settings:
                for setting in options.settings:
                    await cyberq.async_set(*setting.split("=", 2))

            while True:
                sleep = 1.0
                try:
                    sensors = await cyberq.async_update()
                    logging.info("%s: %s", cyberq.serial_number, str(sensors))
                except TimeoutError:
                    logging.warning("Timeout")
                    sleep = 0
                except (
                    aiohttp.client_exceptions.ClientConnectorError,
                    aiohttp.client_exceptions.ClientResponseError,
                ) as error:
                    logging.warning(error)
                    sleep = 10.0
                await asyncio.sleep(sleep)

    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print()  # noqa: T201
        sys.exit(1)
