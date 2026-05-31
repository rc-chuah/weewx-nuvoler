# weewx-nuvoler

A WeeWX extension that uploads weather data to [Nuvoler.com](https://www.nuvoler.com/)

![License](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Python](https://img.shields.io/badge/Python-2.7%2B%20%7C%203.x-blue.svg)
![WeeWX](https://img.shields.io/badge/WeeWX-3.8.0%2B-blue.svg)

## Overview

**weewx-nuvoler** is a WeeWX extension that automatically uploads your weather station's data to Nuvoler.com, a weather data collection service supporting comprehensive meteorological parameters.

## Features

- ✅ Automatic unit conversion to metric (SI units) with wind in knots
- ✅ Uploads all major weather parameters (temperature, humidity, pressure, wind, rain, UV, dewpoint)
- ✅ Lightweight with zero external dependencies
- ✅ Compatible with Python 2.7+ and Python 3.x
- ✅ Works with WeeWX v3.8.0 and later
- ✅ Support for both WeeWX v4 and v5 installers
- ✅ Simple configuration via weewx.conf

## Requirements

- **Python:** 2.7+ or 3.x
- **WeeWX:** v3.8.0 or later
- **Credentials:** Station ID and password from Nuvoler.com
- **External Libraries:** None (uses only Python standard library)

## Installation

### Step 1: Get Credentials

Visit [Sign Up - Join Nuvoler](https://www.nuvoler.com/signup.php) to register your weather station and obtain station ID and password.

### Step 2: Download the Extension

```bash
wget -O weewx-nuvoler.zip https://github.com/rc-chuah/weewx-nuvoler/archive/main.zip
```

### Step 3: Install the Extension

**For WeeWX v4 and earlier:**
```bash
wee_extension --install weewx-nuvoler.zip
```

**For WeeWX v5:**
```bash
weectl extension install weewx-nuvoler.zip
```

### Step 4: Configure

Edit `/etc/weewx/weewx.conf` and add the following section:

```ini
[StdRESTful]
    [[Nuvoler]]
        station_id = YOUR_STATION_ID
        station_pass = YOUR_STATION_PASSWORD
```

Optional configuration:

```ini
[StdRESTful]
    [[Nuvoler]]
        # Station credentials (required)
        station_id = YOUR_STATION_ID
        station_pass = YOUR_STATION_PASSWORD
        
        # Enable or disable uploads (default: true)
        enabled = true
        
        # Server URL (default: https://www.nuvoler.com/data/recibir.php)
        server_url = https://www.nuvoler.com/data/recibir.php
```

### Step 5: Restart WeeWX

```bash
sudo systemctl restart weewx
```

## How It Works

The extension performs the following tasks:

1. **Monitors** archive records from your WeeWX weather station
2. **Extracts** weather data (temperature, humidity, pressure, wind, rain, UV, dewpoint)
3. **Converts** all values to metric units (Celsius, mbar/hPa, mm (L/m²), knots for wind, etc.)
4. **Uploads** the data to Nuvoler via HTTP GET for each new archive record

## Supported Parameters

| Parameter | Unit | WeeWX Field | Description |
|-----------|------|-------------|-------------|
| temperature | °C | outTemp | Outdoor temperature |
| rh | % | outHumidity | Relative humidity |
| mslp | mbar/hPa | barometer | Mean sea level pressure |
| wind_dir | ° | windDir | Wind direction |
| wind_avg | knots | windSpeed | Average wind speed |
| wind_min | knots | windSpeed | Minimum wind speed (estimated from windSpeed and windGust) |
| wind_max | knots | windGust | Maximum wind speed/gust |
| precip | mm (L/m²) | hourRain | Hourly precipitation |
| uv | Index | UV | UV index |
| dewpoint | °C | dewpoint | Dew point |

## Upload Method

This extension uses HTTP GET to upload data to Nuvoler with the following format:

```
GET /data/recibir.php?station_id=50&station_pass=12345&temperature=22.5&rh=65&mslp=1013.2&wind_dir=180&wind_avg=12.5&wind_min=8.0&wind_max=16.0&precip=2.4&uv=5&dewpoint=14.2 HTTP/1.1
Host: www.nuvoler.com
```

## Unit Conversion Details

The extension converts your station's native units to the following for Nuvoler:

- **Temperature:** Converted to Celsius (°C)
- **Pressure:** Converted to millibars/hectopascals (mbar/hPa)
- **Precipitation:** Converted to millimeters/litres per square meter (mm (L/m²))
- **Wind Speed:** Converted to knots (from m/s internally)
- **Other Parameters:** Humidity (%), UV index (unitless), Wind direction (°)

This ensures consistent data format regardless of your station's configured unit system (US, Metric, or MetricWX).

## Troubleshooting

### Check WeeWX Logs

```bash
tail -f /var/log/syslog | grep nuvoler
```

### Enable Debug Logging

Add to `/etc/weewx/weewx.conf`:

```ini
debug = 2
```

Then restart WeeWX:

```bash
sudo systemctl restart weewx
```

### Test the Extension Manually

```bash
cd /usr/share/weewx
PYTHONPATH=bin python bin/user/nuvoler.py
```

Expected output will show the constructed URL with test data in multiple unit systems (US, Metric, and MetricWX).

Expected output:
```
================================================================================
Test 1 - Purely US Units (weewx.US)
Input: US units (°F, mph, inHg, inches)
================================================================================
https://www.nuvoler.com/data/recibir.php?station_id=50&station_pass=12345&temperature=22.5&rh=65&mslp=1013.2&wind_dir=180&wind_avg=9.5&wind_max=15.3&wind_min=4.2&precip=2.4&uv=5&dewpoint=14.2

================================================================================
Test 2 - Purely Metric Units (weewx.METRIC)
Input: Metric units (°C, km/h, mbar/hPa, cm)
================================================================================
https://www.nuvoler.com/data/recibir.php?station_id=50&station_pass=12345&temperature=22.5&rh=65&mslp=1013.2&wind_dir=180&wind_avg=9.4&wind_max=15.1&wind_min=4.1&precip=2.4&uv=5&dewpoint=14.2

================================================================================
Test 3 - Purely MetricWX Units (weewx.METRICWX)
Input: MetricWX units (°C, m/s, mbar/hPa, mm (L/m²)
================================================================================
https://www.nuvoler.com/data/recibir.php?station_id=50&station_pass=12345&temperature=22.5&rh=65&mslp=1013.2&wind_dir=180&wind_avg=9.4&wind_max=15.1&wind_min=4.1&precip=2.4&uv=5&dewpoint=14.2

================================================================================
3-PARAMETER WEIBULL ESTIMATION ANALYSIS
================================================================================

Test Case: wind_avg=4.86 m/s (~9.45 knots), wind_max=7.78 m/s (~15.1 knots)

================================================================================
METHOD 1: 3-Parameter Weibull Distribution
================================================================================
Estimated parameters:
  θ (location) = 1.458 m/s (minimum threshold)
  k (shape)    = 2.000 (distribution curvature)
  λ (scale)    = 2.946 m/s (spread parameter)

  5% percentile (wind_min): 2.125 m/s (4.13 knots)
  10% percentile (wind_min): 2.414 m/s (4.69 knots)
  25% percentile (wind_min): 3.038 m/s (5.91 knots)
  50% percentile (wind_min): 3.911 m/s (7.60 knots)

Theoretical statistics:
  Mean = 4.069 m/s (observed avg: 4.86 m/s)
  Std Dev = 1.365 m/s

  Estimated minimum (5th percentile): 2.125 m/s (4.13 knots)

================================================================================
COMPARISON: All Available Methods
================================================================================
3-Parameter Weibull (PRIMARY):  2.125 m/s (4.13 knots)
2-Parameter Weibull (FALLBACK): 3.871 m/s (7.53 knots)
Climatological Ratio (FALLBACK):2.945 m/s (5.73 knots)
Extreme Value Theory (FALLBACK):3.112 m/s (6.05 knots)
Auto-selected method:           2.125 m/s (4.13 knots)

================================================================================
EXPECTED OUTPUTS (for all three unit tests - should be identical):
================================================================================
temperature=22.5 (°C)
rh=65 (%)
mslp=1013.2 (mbar/hPa)
wind_dir=180 (°)
wind_avg=9.4 or 9.5 (knots)
wind_max=15.1 or 15.3 (knots)
wind_min≈4.1 to 7.5 (knots from advanced estimation)
precip=2.4 (mm (L/m²))
uv=5 (index)
dewpoint=14.2 (°C)
================================================================================
```

### Common Issues

| Issue | Solution |
|-------|----------|
| No data uploading | Verify station_id and station_pass in weewx.conf |
| Connection errors | Check internet connectivity and Nuvoler server status |
| Missing parameters | Ensure your weather station supports all sensor types |
| Incorrect values | Verify your station's unit system setting; extension handles all unit conversions |

### Test Manually with curl

```bash
curl "https://www.nuvoler.com/data/recibir.php?station_id=YOUR_STATION_ID&station_pass=YOUR_STATION_PASSWORD&temperature=22.5&rh=65&mslp=1013.2&wind_dir=180&wind_avg=12.5&wind_min=8.0&wind_max=16.0&precip=2.4&uv=5&dewpoint=14.2"
```

## Dependencies

This extension uses **only Python's standard library**. The following modules are utilized:

- `Queue` (Python 2) / `queue` (Python 3)
- `urllib` / `urllib.parse` (Python 3)
- `sys`
- `time`
- `math`
- `logging` / `syslog`

**No external pip packages are required.**

## License

Copyright © 2026 RC Chuah

Distributed under the terms of the [GNU General Public License (GPLv3)](LICENSE.md)

## Credits

- **Original Concept:** Based on [weewx-windy](https://github.com/Jterrettaz/weewx-windy) by Matthew Wall and Jacques Terrettaz
- **Modified for Nuvoler:** RC Chuah

## Links

- **WeeWX:** https://www.weewx.com/
- **Nuvoler:** https://www.nuvoler.com/
- **WeeWX Documentation:** https://www.weewx.com/docs/
- **Nuvoler Documentation:** https://www.nuvoler.com/documentation.php
- **weewx-windy:** https://github.com/Jterrettaz/weewx-windy
- **WMO Wind Standards:** https://library.wmo.int/
- **Weibull Distribution:** https://en.wikipedia.org/wiki/Weibull_distribution
- **Rayleigh Distribution:** https://en.wikipedia.org/wiki/Rayleigh_distribution
- **Gumbel Distribution:** https://en.wikipedia.org/wiki/Gumbel_distribution
- **Lanczos Approximation:** https://en.wikipedia.org/wiki/Lanczos_approximation
- **Extreme Value Theory:** https://en.wikipedia.org/wiki/Extreme_value_theory
