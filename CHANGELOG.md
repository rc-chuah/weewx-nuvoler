# weewx-nuvoler v0.1 - 4 June 2026
* Initial release based on weewx-windy template
* Supports Nuvoler API (https://www.nuvoler.com/documentation.php)
* Automatic weather data conversion to metric/SI units (temperature in °C, pressure in mbar/hPa, precipitation in mm (L/m²))
* Wind speeds converted to knots for Nuvoler API compatibility
* Compatible with weewx V3.8.0 and later
* Support for both weewx V4 (wee_extension) and V5 (weectl) installers
* Uses only Python standard library - no external dependencies required
* Support for both Python 2.7+ and Python 3.x
* Simplified implementation with only format_url() override
* Supports all major weather parameters: temperature, humidity, pressure, wind (direction, speed, gust), hourly precipitation, UV index, and dew point
* Based on weewx-windy by Matthew Wall and Jacques Terrettaz
