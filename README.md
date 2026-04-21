# weewx-nuvoler

A WeeWX extension that uploads weather data to [Nuvoler.com](https://www.nuvoler.com/)

## Overview

**weewx-nuvoler** is a WeeWX extension that automatically uploads your weather station's data to Nuvoler.com, a weather data collection service supporting comprehensive meteorological parameters.

## Features

- ✅ Automatic unit conversion to metric (SI units)
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

Visit [Nuvoler.com](https://www.nuvoler.com/) to register your weather station and obtain station ID and password.

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
        
        # Server URL (default: https://nuvoler.com/data/recibir.php)
        server_url = https://nuvoler.com/data/recibir.php
```

### Step 5: Restart WeeWX

```bash
sudo systemctl restart weewx
```

## How It Works

The extension performs the following tasks:

1. **Monitors** archive records from your WeeWX weather station
2. **Extracts** weather data (temperature, humidity, pressure, wind, rain, UV, dewpoint)
3. **Converts** all values to metric units (Celsius, m/s, hPa, etc.)
4. **Uploads** the data to Nuvoler via HTTP GET for each new archive record

## Supported Parameters

| Parameter | Unit | WeeWX Field | Description |
|-----------|------|-------------|-------------|
| temperature | °C | outTemp | Outdoor temperature |
| rh | % | outHumidity | Relative humidity |
| mslp | hPa | barometer | Mean sea level pressure |
| wind_dir | ° | windDir | Wind direction |
| wind_avg | m/s | windSpeed | Average wind speed |
| wind_min | m/s | windSpeed | Minimum wind speed (estimated) |
| wind_max | m/s | windGust | Maximum wind speed/gust |
| precip | mm | hourRain | Hourly precipitation |
| uv | Index | UV | UV index |
| dewpoint | °C | dewpoint | Dew point |

## Upload Method

This extension uses HTTP GET to upload data to Nuvoler with the following format:

```
GET /data/recibir.php?station_id=50&station_pass=12345&temperature=22.5&rh=65&... HTTP/1.1
Host: nuvoler.com
```

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

Expected output will show the constructed URL with test data.

### Common Issues

| Issue | Solution |
|-------|----------|
| No data uploading | Verify station_id and station_pass in weewx.conf |
| Connection errors | Check internet connectivity and Nuvoler server status |
| Missing parameters | Ensure your weather station supports all sensor types |
| Wrong units | Verify your station's unit system setting |

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
