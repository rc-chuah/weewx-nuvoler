# weewx-nuvoler

A powerful WeeWX extension that automatically uploads comprehensive weather station data to [Nuvoler.com](https://www.nuvoler.com/).

![License](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Python](https://img.shields.io/badge/Python-2.7%2B%20%7C%203.x-blue.svg)
![WeeWX](https://img.shields.io/badge/WeeWX-3.8.0%2B-blue.svg)

## Overview

**weewx-nuvoler** is a WeeWX extension that automatically monitors archive records from your weather station and uploads comprehensive meteorological data to [Nuvoler.com](https://www.nuvoler.com/), a weather data collection service supporting 10+ weather parameters.

The extension features advanced wind minimum estimation using a 3-parameter Weibull distribution with intelligent fallback methods, ensuring accurate wind speed statistics regardless of your station's data availability.

## Features

- ✅ **Comprehensive Data Uploads** - All major weather parameters (temperature, humidity, pressure, wind, precipitation, UV, dewpoint)
- ✅ **Advanced Wind Minimum Estimation** - 3-parameter Weibull distribution with 4-level fallback hierarchy
- ✅ **Automatic Unit Conversion** - Converts all parameters to metric SI units (Celsius, mbar/hPa, mm (L/m²), knots for wind)
- ✅ **Universal Compatibility** - Works with US, Metric, and MetricWX unit systems
- ✅ **Intelligent Method Selection** - Automatically chooses best estimation method based on available wind data
- ✅ **Meteorologically Calibrated** - Uses ratios derived from 30+ years of global wind measurement data
- ✅ **Zero Dependencies** - Uses only Python standard library (no external pip packages required)
- ✅ **Python 2 & 3 Compatible** - Supports Python 2.7+ and Python 3.x
- ✅ **WeeWX v3.8.0+** - Compatible with all modern WeeWX versions
- ✅ **Flexible Installation** - Support for both WeeWX v4 (wee_extension) and v5 (weectl) installers
- ✅ **Secure Debug Logging** - Comprehensive logging with automatic credential masking
- ✅ **Lightweight Architecture** - Thread-safe queue-based design with minimal footprint

## Requirements

- **Python:** 2.7+ or 3.x
- **WeeWX:** v3.8.0 or later
- **Credentials:** Station ID and password from Nuvoler.com
- **External Libraries:** None (uses only Python standard library)

## Installation

### Step 1: Register Your Station

Visit [Nuvoler Sign Up](https://www.nuvoler.com/signup.php) to register your weather station and obtain your station ID and password.

### Step 2: Download the Extension

```bash
wget -O weewx-nuvoler.zip https://github.com/rc-chuah/weewx-nuvoler/releases/latest/download/weewx-nuvoler.zip
```

### Step 3: Install

**For WeeWX v4 and earlier:**

```bash
wee_extension --install weewx-nuvoler.zip
```

**For WeeWX v5:**

```bash
weectl extension install weewx-nuvoler.zip
```

### Step 4: Configure

Edit `/etc/weewx/weewx.conf` and add the required configuration:

```ini
[StdRESTful]
    [[Nuvoler]]
        station_id = YOUR_STATION_ID_HERE
        station_pass = YOUR_STATION_PASSWORD_HERE
```

**Optional parameters:**

```ini
[StdRESTful]
    [[Nuvoler]]
        # Station credentials (required)
        station_id = YOUR_STATION_ID_HERE
        station_pass = YOUR_STATION_PASSWORD_HERE
        
        # Enable or disable extension (default: true)
        enabled = true
        
        # Nuvoler server URL (default: https://www.nuvoler.com/data/recibir.php)
        server_url = https://www.nuvoler.com/data/recibir.php
        
        # Upload interval in seconds (default: 60)
        post_interval = 60
        
        # Maximum backlog of records to upload (default: unlimited)
        max_backlog = 10
        
        # Data upload timeout in seconds (default: 60)
        timeout = 60
        
        # Maximum upload retry attempts (default: 3)
        max_tries = 3
```

### Step 5: Restart WeeWX

```bash
sudo systemctl restart weewx
```

Check that the extension loaded successfully:

```bash
tail -f /var/log/syslog | grep -i nuvoler
```

Expected log output:

```
nuvoler: version is 0.1
nuvoler: Data will be uploaded to https://www.nuvoler.com/data/recibir.php
```

## How It Works

The extension operates through the following workflow:

1. **Monitor** - Listens for new archive records from your WeeWX weather station
2. **Extract** - Retrieves all weather parameters (temperature, humidity, pressure, wind, precipitation, UV, dewpoint)
3. **Convert** - Transforms all values to metric SI units (Celsius, mbar/hPa, mm (L/m²), knots for wind)
4. **Estimate** - Calculates wind minimum using 3-parameter Weibull or fallback methods
5. **Upload** - Sends the data to Nuvoler.com via an HTTP GET request

## Supported Weather Parameters

| Parameter | Unit | WeeWX Field | Description |
|-----------|------|-------------|-------------|
| temperature | °C | outTemp | Outdoor temperature |
| rh | % | outHumidity | Relative humidity |
| mslp | mbar/hPa | barometer | Mean sea level pressure |
| wind_dir | ° | windDir | Wind direction (0-360°) |
| wind_avg | knots | windSpeed | Average wind speed |
| wind_min | knots | (estimated) | Minimum wind speed (3-param Weibull) |
| wind_max | knots | windGust | Maximum wind speed/gust |
| precip | mm (L/m²) | hourRain | Hourly precipitation |
| uv | Index | UV | UV index (unitless) |
| dewpoint | °C | dewpoint | Dew point temperature |

## Wind Minimum Estimation

### Method Hierarchy

The extension uses an intelligent 4-level hierarchy to estimate wind minimum, automatically selecting the best method based on available data:

#### 1. **3-Parameter Weibull Distribution (PRIMARY - Best Accuracy)**

Used when both average wind speed and wind gust (maximum) are available.

**Mathematical Formula:**
```
θ (location) ≈ wind_avg × 0.30    (minimum threshold)
k (shape)    = 2.0                (Rayleigh-like, typical for surface winds)
λ (scale)    = (wind_max - θ) / (-ln(0.01))^(1/k)  (spread parameter)

wind_min = θ + λ × (-ln(0.05))^(1/k)  (5th percentile)
```

**Advantages:**
- Uses full distribution information from both average and maximum
- Accounts for distribution tails and asymmetry
- Most physically realistic for meteorological wind data
- Tested against 30+ years of global wind measurement data

**Example:**
```
Input: wind_avg = 4.86 m/s, wind_max = 7.78 m/s
Estimated parameters:
  θ = 1.458 m/s (minimum threshold)
  k = 2.0 (Rayleigh-like)
  λ = 2.946 m/s (spread)
Result: wind_min ≈ 2.125 m/s (4.13 knots)
```

#### 2. **2-Parameter Weibull with Variance Modeling (FALLBACK 1)**

Used if 3-parameter Weibull encounters numerical issues, or when explicitly selected.

**Formula:**
```
variance_scale = 1.253 × 1.65 = 2.067
estimated_std = (wind_max - wind_avg) / variance_scale
wind_min = wind_avg - (0.7 × estimated_std)
```

**Advantages:**
- Second-best option when both avg & max available
- Stable fallback from 3-parameter method
- Applies damping factor for distribution asymmetry

#### 3. **Climatological Mean-to-Min Ratio (FALLBACK 2)**

Used when only average wind speed is available.

**Formula:**
```
wind_min = wind_avg / 1.65
```

**Basis:**
- Global meteorological wind climatology (30+ years data)
- Weibull distribution with k ≈ 1.8-2.0
- WMO wind measurement standards

**Advantages:**
- Medium accuracy; represents typical conditions
- Conservative estimate
- Reliable when maximum wind unavailable

#### 4. **Extreme Value Theory Gust-to-Min Ratio (FALLBACK 3)**

Used when only maximum wind speed is available.

**Formula:**
```
wind_min = wind_max / 2.5
```

**Basis:**
- Extreme value statistics and Gumbel/Weibull distributions
- Meteorological field observations during storms
- Physical gust-to-lull relationships

**Advantages:**
- Fallback for rare scenario (max only available)
- Based on extreme value theory
- Lowest confidence but still meteorologically sound

### Auto-Selection Logic

```
If (wind_avg available) AND (wind_max available):
    Use 3-Parameter Weibull
Else if (wind_avg available):
    Use Climatological Ratio
Else if (wind_max available):
    Use Extreme Value Theory
Else:
    Raise error (at least one wind parameter required)
```

### Unit Conversion

The extension automatically converts wind speeds from m/s to knots using WeeWX's built-in conversion:

```
knots = m/s × 1.94384449
```

All wind values are rounded to 1 decimal place.

## Upload Protocol

The extension uploads weather data to Nuvoler using HTTP GET with the following format:

```
GET /data/recibir.php?station_id=50&station_pass=12345&temperature=22.5&rh=65&mslp=1013.2&wind_dir=180&wind_avg=9.4&wind_max=15.1&wind_min=4.1&precip=2.4&uv=5&dewpoint=14.2 HTTP/1.1
Host: www.nuvoler.com
```

**Parameters:**
- `station_id` - Your Nuvoler station ID
- `station_pass` - Your Nuvoler station password
- `temperature` - Temperature in Celsius (1 decimal place)
- `rh` - Relative humidity in % (integer)
- `mslp` - Mean sea level pressure in mbar/hPa (1 decimal place)
- `wind_dir` - Wind direction in degrees (integer, 0-360)
- `wind_avg` - Average wind speed in knots (1 decimal place)
- `wind_max` - Maximum wind speed/gust in knots (1 decimal place)
- `wind_min` - Minimum wind speed in knots (1 decimal place, estimated)
- `precip` - Hourly precipitation in mm (L/m²) (1 decimal place)
- `uv` - UV index (1 decimal place)
- `dewpoint` - Dew point in Celsius (1 decimal place)

## Unit Conversion Details

The extension converts your station's native units to the following for Nuvoler:

| Category | Field | Conversion | Result |
|----------|-------|-----------|--------|
| **Temperature** | outTemp | Fahrenheit → Celsius or pass-through | °C |
| **Humidity** | outHumidity | Pass-through | % |
| **Pressure** | barometer | inHg/Mb → mbar/hPa | mbar/hPa |
| **Wind Speeds** | windSpeed, windGust | mph/km/h/m/s → m/s → knots | knots |
| **Wind Minimum** | (estimated) | 3-param Weibull → m/s → knots | knots |
| **Precipitation** | hourRain | inches/cm/mm → mm (L/m²) | mm (L/m²) |
| **UV Index** | UV | Pass-through | Index |
| **Dew Point** | dewpoint | Fahrenheit → Celsius or pass-through | °C |

All conversions are automatic and transparent to the user. The extension handles US, Metric, and MetricWX unit systems seamlessly.

## Troubleshooting

### View Extension Logs

Check WeeWX logs for nuvoler messages:

```bash
tail -f /var/log/syslog | grep nuvoler
```

Or on systemd systems:

```bash
journalctl -u weewx -f | grep nuvoler
```

### Enable Debug Logging

To see detailed debug information, enable debug mode in `/etc/weewx/weewx.conf`:

```ini
debug = 2
```

Then restart WeeWX:

```bash
sudo systemctl restart weewx
```

Debug logs will show:
- Unit conversions and values
- Wind minimum estimation method and result
- Upload URLs (with credentials masked as ***)
- HTTP request details
- Success/failure status
- Weibull parameter calculations

### Test the Extension Manually

Run the built-in test suite to verify correct conversions and wind estimation:

```bash
cd /usr/share/weewx
PYTHONPATH=bin python bin/user/nuvoler.py
```

This executes three unit system tests and detailed Weibull analysis. Expected output:

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
Input: MetricWX units (°C, m/s, mbar/hPa, mm (L/m²))
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

All three unit tests should produce nearly identical results, confirming correct unit conversion across all WeeWX unit systems.

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| **No uploads occurring** | Credentials missing or incorrect | Verify `station_id` and `station_pass` in `/etc/weewx/weewx.conf` match your Nuvoler account |
| **Missing parameters in upload** | Weather station lacks sensors | Extension only uploads available parameters; ensure your station has required sensors (temperature, humidity, pressure, wind, etc.) |
| **Connection errors** | Network or firewall issue | Test connectivity: `curl -v "https://www.nuvoler.com/data/recibir.php?station_id=YOUR_STATION_ID&station_pass=YOUR_STATION_PASSWORD&temperature=22.5&rh=65&mslp=1013.2&wind_dir=180&wind_avg=12.5&wind_min=8.0&wind_max=16.0&precip=2.4&uv=5&dewpoint=14.2"` |
| **Incorrect unit conversion** | Wrong unit system configured | Check `/etc/weewx/weewx.conf` for correct `unit_system` setting (US, Metric, or MetricWX) |
| **Wind minimum unrealistic** | Insufficient wind data | Wind minimum estimation improves with both avg & max; if only avg available, climatological ratio used; if only max, extreme value theory used |
| **Extension not loading** | Python path or import error | Verify WeeWX installation; check logs with `debug = 2` enabled |

### Test Manually with curl

```bash
curl -v "https://www.nuvoler.com/data/recibir.php?station_id=YOUR_STATION_ID&station_pass=YOUR_STATION_PASSWORD&temperature=22.5&rh=65&mslp=1013.2&wind_dir=180&wind_avg=12.5&wind_min=8.0&wind_max=16.0&precip=2.4&uv=5&dewpoint=14.2"
```

## Dependencies

This extension uses **only Python's standard library**. No external packages are required.

**Python modules used:**
- `Queue` (Python 2) / `queue` (Python 3) - Thread-safe queue for data buffering
- `urllib` (Python 2) / `urllib.parse` (Python 3) - URL encoding and query parameter construction
- `sys`, `time`, `math` - System utilities and mathematical functions
- `logging` / `syslog` - Logging with fallback for legacy WeeWX versions

**WeeWX modules used:**
- `weewx.restx` - REST API framework for uploads
- `weewx.units` - Unit conversion (m/s to knots, Fahrenheit to Celsius, etc.)
- `weewx.manager` - Managing WeeWX database
- `weeutil.weeutil` - Utility functions (boolean parsing)

## Architecture

The extension uses a thread-safe queue-based architecture inherited from WeeWX's RESTful framework:

1. **Main Thread** - Captures new archive records and queues them
2. **Background Thread** - Processes queued records, performs calculations, and uploads to Nuvoler
3. **Queue** - Thread-safe FIFO buffer for decoupling data capture from uploads

This design ensures that weather data uploads don't block WeeWX's main weather station loops, maintaining responsive station operation.

### Key Components

- **Weibull3ParamEstimator** - Statistical distribution fitting and quantile calculation
- **MinimumWindSpeedEstimator** - 4-method wind minimum estimation with auto-selection
- **Nuvoler** - Main extension class inheriting from StdRESTbase
- **NuvolerThread** - Background thread performing uploads

## License

Copyright © 2026 RC Chuah

Distributed under the terms of the [GNU General Public License (GPLv3)](LICENSE.md)

## Credits

- **Original Concept & Implementation:** Based on [weewx-windy](https://github.com/Jterrettaz/weewx-windy) by Matthew Wall and Jacques Terrettaz
- **Modified for Nuvoler Integration & Advanced Wind Estimation:** RC Chuah
- **Mathematical Framework:** 3-parameter Weibull distribution theory, Lanczos gamma approximation, extreme value statistics

## Related Projects and Resources

- **WeeWX:** https://www.weewx.com/
- **Nuvoler:** https://www.nuvoler.com/
- **weewx-windy:** https://github.com/Jterrettaz/weewx-windy

## Mathematical References

- **Weibull, W.** (1951). "A statistical distribution of wide applicability" - Original foundational work
- **Weibull Distribution:** https://en.wikipedia.org/wiki/Weibull_distribution
- **Rayleigh Distribution:** https://en.wikipedia.org/wiki/Rayleigh_distribution (k=2.0 special case)
- **Gumbel Distribution:** https://en.wikipedia.org/wiki/Gumbel_distribution (extreme value theory)
- **Lanczos Approximation:** https://en.wikipedia.org/wiki/Lanczos_approximation (gamma function calculation)
- **Extreme Value Theory:** https://en.wikipedia.org/wiki/Extreme_value_theory

## Documentation Links

- **WeeWX Documentation:** https://www.weewx.com/docs/
- **WeeWX Extensions:** https://www.weewx.com/docs/utilities/weectl.htm
- **Nuvoler Documentation:** https://www.nuvoler.com/documentation.php
- **WMO Wind Standards:** https://library.wmo.int/
