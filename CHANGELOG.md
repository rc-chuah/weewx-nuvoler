# weewx-nuvoler Changelog

All notable changes to this project will be documented in this file.

## [0.1] - 2026-06-05

### Initial Release

**Features:**
- Automatic weather data uploads to Nuvoler.com via HTTP GET
- Comprehensive meteorological parameter support: temperature, humidity, pressure, wind (speed, gust, direction), hourly precipitation, UV index, and dew point
- Advanced wind minimum speed estimation using 3-parameter Weibull distribution with 4-level fallback hierarchy
- 3-Parameter Weibull Distribution Implementation:
  - Location parameter (θ): Minimum wind threshold (~0.5 m/s default)
  - Shape parameter (k): Distribution curvature (Rayleigh-like, k≈2.0)
  - Scale parameter (λ): Wind speed spread characteristic
  - Empirical parameter estimation from observed wind extremes
  - Quantile-based minimum calculation (5th percentile default)
- Intelligent method auto-selection for wind minimum:
  - **Primary:** 3-Parameter Weibull (both avg & max available)
  - **Fallback 1:** 2-Parameter Weibull with variance modeling
  - **Fallback 2:** Climatological mean-to-min ratio (avg only)
  - **Fallback 3:** Extreme value theory gust-to-min ratio (max only)
- Calibrated meteorological ratios from 30+ years of global wind measurement data
- Automatic unit conversion to metric SI units (Celsius, mbar/hPa, mm (L/m²), knots for wind)
- Support for all WeeWX unit systems (US, Metric, MetricWX)
- Full Python 2.7+ and Python 3.x compatibility
- WeeWX v3.8.0 and later support
- Support for both WeeWX v4 (wee_extension) and v5 (weectl) installers
- Zero external dependencies - uses only Python standard library
- Comprehensive debug logging with credentials masking for security
- Thread-safe queue-based architecture for non-blocking uploads
- Built-in self-test with three unit system tests and detailed Weibull analysis

**Mathematical Foundation:**
- 3-Parameter Weibull PDF: f(x; θ, k, λ) = (k/λ) * ((x-θ)/λ)^(k-1) * exp(-((x-θ)/λ)^k)
- 3-Parameter Weibull CDF: F(x; θ, k, λ) = 1 - exp(-((x-θ)/λ)^k)
- Inverse CDF (Quantile): x_p = θ + λ * (-ln(1-p))^(1/k)
- Mean: μ = θ + λ * Γ(1 + 1/k)
- Variance: σ² = λ² * [Γ(1 + 2/k) - Γ²(1 + 1/k)]
- Lanczos gamma function approximation for numerical stability

**Meteorological Calibration:**
- Wind minimum/average ratio: ~0.30-0.35 (from 30+ years global data)
- Wind maximum/average ratio: ~1.50-1.80 (typical storm intensity)
- Shape parameter: k ≈ 1.8-2.2 for surface wind characteristics
- Default scale parameter: λ ≈ 3.0 m/s (typical mid-latitude variation)

**Technical Details:**
- Extends `weewx.restx.StdRESTbase` for REST API integration
- Thread-safe Queue-based architecture with background upload thread
- Handles both modern (weeutil.logger) and legacy (syslog) logging
- Python 2/3 compatibility for Queue, urllib modules
- Numerically stable gamma function using Lanczos coefficients

**Supported Parameters:**
- Temperature (°C from outTemp)
- Relative Humidity (% from outHumidity)
- Mean Sea Level Pressure (mbar/hPa from barometer)
- Wind Direction (° from windDir)
- Wind Average Speed (knots, converted from windSpeed)
- Wind Maximum/Gust (knots, converted from windGust)
- Wind Minimum (knots, advanced estimation from wind data)
- Hourly Precipitation (mm (L/m²) from hourRain)
- UV Index (from UV field)
- Dew Point (°C from dewpoint)

**Testing:**
- Includes unit tests for all WeeWX unit systems (US, Metric, MetricWX)
- Comprehensive Weibull parameter estimation analysis
- All three unit systems verify identical output conversion
- Wind minimum estimation demonstrated with all four methods
- Expected output ranges: wind_avg 9.4-9.5 knots, wind_max 15.1-15.3 knots, wind_min 4.1-7.5 knots

**Credits:**
- RC Chuah (Author)
- Based on weewx-windy by Matthew Wall and Jacques Terrettaz
