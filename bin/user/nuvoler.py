# weewx extension for nuvoler
# Copyright © 2026 RC Chuah (Based on weewx-windy by Matthew Wall and Jacques Terrettaz)
# Distributed under the terms of the GNU General Public License (GPLv3)

"""
This is a weewx extension that uploads data to Nuvoler.

https://www.nuvoler.com/

The protocol is described here:

https://www.nuvoler.com/documentation.php

Minimal configuration:

[StdRESTful]
    [[Nuvoler]]
        station_id = YOUR_STATION_ID
        station_pass = YOUR_STATION_PASSWORD
"""

# Handle Python 2 vs Python 3 differences
try:
    from Queue import Queue
except ImportError:
    from queue import Queue

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

import sys
import time

import weewx
import weewx.manager
import weewx.restx
import weewx.units
from weeutil.weeutil import to_bool


VERSION = "0.1"


# Logging compatibility
try:
    import weeutil.logger
    import logging

    log = logging.getLogger(__name__)

    def logdbg(msg):
        log.debug(msg)

    def loginf(msg):
        log.info(msg)

    def logerr(msg):
        log.error(msg)

except ImportError:
    # Old-style weewx logging
    import syslog

    def logmsg(level, msg):
        syslog.syslog(level, 'nuvoler: %s' % msg)

    def logdbg(msg):
        logmsg(syslog.LOG_DEBUG, msg)

    def loginf(msg):
        logmsg(syslog.LOG_INFO, msg)

    def logerr(msg):
        logmsg(syslog.LOG_ERR, msg)


class Nuvoler(weewx.restx.StdRESTbase):
    DEFAULT_URL = 'https://www.nuvoler.com/data/recibir.php'

    def __init__(self, engine, cfg_dict):
        super(Nuvoler, self).__init__(engine, cfg_dict)
        loginf("version is %s" % VERSION)
        
        # Get site dictionary with required parameters
        site_dict = weewx.restx.get_site_dict(
            cfg_dict, 'Nuvoler', 'station_id', 'station_pass'
        )
        
        if site_dict is None:
            logerr("station_id and station_pass are required for Nuvoler")
            return
        
        site_dict.setdefault('server_url', Nuvoler.DEFAULT_URL)

        binding = site_dict.pop('binding', 'wx_binding')
        mgr_dict = weewx.manager.get_manager_dict_from_config(cfg_dict, binding)

        self.archive_queue = Queue()
        self.archive_thread = NuvolerThread(
            self.archive_queue,
            manager_dict=mgr_dict,
            **site_dict
        )

        self.archive_thread.start()
        self.bind(weewx.NEW_ARCHIVE_RECORD, self.new_archive_record)
        loginf("Data will be uploaded to %s" % site_dict['server_url'])

    def new_archive_record(self, event):
        self.archive_queue.put(event.record)


class NuvolerThread(weewx.restx.RESTThread):

    def __init__(self, q, station_id, station_pass, 
                 server_url=Nuvoler.DEFAULT_URL,
                 skip_upload=False, manager_dict=None,
                 post_interval=None, max_backlog=sys.maxsize, stale=None,
                 log_success=True, log_failure=True,
                 timeout=60, max_tries=3, retry_wait=5):
        
        super(NuvolerThread, self).__init__(
            q,
            protocol_name='Nuvoler',
            manager_dict=manager_dict,
            post_interval=post_interval,
            max_backlog=max_backlog,
            stale=stale,
            log_success=log_success,
            log_failure=log_failure,
            max_tries=max_tries,
            timeout=timeout,
            retry_wait=retry_wait
        )
        
        self.station_id = station_id
        self.station_pass = station_pass
        self.server_url = server_url
        self.skip_upload = to_bool(skip_upload)

    def format_url(self, record):
        """Build the URL for GET request to Nuvoler API
        
        Converts record to METRICWX units and builds query parameters:
        - All metrics converted to METRICWX standard (SI units)
        - Temperature: Celsius
        - Pressure: hPa
        - Hourly Precipitation: mm
        - Wind speeds (wind_avg, wind_min, wind_max): knots (converted from m/s)
        - UV Index: unitless
        - Dew Point: Celsius
        """
        url = self.server_url
        if weewx.debug >= 2:
            logdbg("url: %s" % url)

        # Convert to METRICWX units (SI base units)
        # METRICWX: temperature=°C, speed=m/s, pressure=hPa, rain=mm
        metric_record = weewx.units.to_METRICWX(record)

        # Build query parameters
        parts = dict()
        parts['station_id'] = self.station_id
        parts['station_pass'] = self.station_pass

        # Temperature (Celsius)
        if 'outTemp' in metric_record and metric_record['outTemp'] is not None:
            parts['temperature'] = round(metric_record['outTemp'], 1)

        # Relative Humidity (%)
        if 'outHumidity' in metric_record and metric_record['outHumidity'] is not None:
            parts['rh'] = int(metric_record['outHumidity'])

        # Mean Sea Level Pressure (hPa)
        if 'barometer' in metric_record and metric_record['barometer'] is not None:
            # barometer in METRICWX is in hectopascals (hPa)
            parts['mslp'] = round(metric_record['barometer'], 1)

        # Wind Direction (0-360 degrees)
        if 'windDir' in metric_record and metric_record['windDir'] is not None:
            parts['wind_dir'] = int(metric_record['windDir'])

        # Wind Speed (knots) - Average
        # METRICWX windSpeed is in m/s, convert to knots using weewx.units.mps_to_knot()
        if 'windSpeed' in metric_record and metric_record['windSpeed'] is not None:
            wind_knots = weewx.units.mps_to_knot(metric_record['windSpeed'])
            parts['wind_avg'] = round(wind_knots, 1)

        # Wind Gust (knots) - Maximum
        # METRICWX windGust is in m/s, convert to knots using weewx.units.mps_to_knot()
        if 'windGust' in metric_record and metric_record['windGust'] is not None:
            gust_knots = weewx.units.mps_to_knot(metric_record['windGust'])
            parts['wind_max'] = round(gust_knots, 1)

        # Wind minimum - WeeWX may not have this, use windSpeed as fallback (in knots)
        if 'windSpeed' in metric_record and metric_record['windSpeed'] is not None:
            wind_knots = weewx.units.mps_to_knot(metric_record['windSpeed'])
            parts['wind_min'] = round(wind_knots, 1)

        # Hourly Precipitation (mm)
        if 'hourRain' in metric_record and metric_record['hourRain'] is not None:
            parts['precip'] = round(metric_record['hourRain'], 1)

        # UV Index
        if 'UV' in metric_record and metric_record['UV'] is not None:
            parts['uv'] = round(metric_record['UV'], 1)

        # Dew Point (Celsius)
        if 'dewpoint' in metric_record and metric_record['dewpoint'] is not None:
            parts['dewpoint'] = round(metric_record['dewpoint'], 1)

        # Build final URL
        url_with_params = "%s?%s" % (url, urlencode(parts))
        
        if weewx.debug >= 2:
            # Log without password
            safe_parts = parts.copy()
            safe_parts['station_pass'] = '***'
            logdbg("URL: %s?%s" % (url, urlencode(safe_parts)))

        return url_with_params


# Test hook: PYTHONPATH=bin python bin/user/nuvoler.py
if __name__ == "__main__":
    class FakeMgr(object):
        table_name = 'fake'

        def getSql(self, query, value):
            return None

    weewx.debug = 2
    queue = Queue()
    t = NuvolerThread(queue, station_id='50', station_pass='12345')
    
    # Test 1: Purely US Units (weewx.US)
    # US: temperature=°F, speed=mph, pressure=inHg, rain=inches
    r_us = {
        'dateTime': int(time.time() + 0.5),
        'usUnits': weewx.US,
        'outTemp': 72.5,               # 72.5°F → 22.5°C
        'outHumidity': 65,             # 65% (unitless)
        'windSpeed': 10.9,             # 10.9 mph → 4.87 m/s → 9.46 knots
        'windGust': 17.6,              # 17.6 mph → 7.87 m/s → 15.28 knots
        'windDir': 180,                # 180° (unitless)
        'barometer': 29.92,            # 29.92 inHg → 1013.2 hPa
        'hourRain': 0.094488,          # 0.094488 inches → 2.4 mm
        'UV': 5,                       # 5 (unitless)
        'dewpoint': 57.56              # 57.56°F → 14.2°C
    }
    
    print("=" * 80)
    print("Test 1 - Purely US Units (weewx.US)")
    print("Input: US units (°F, mph, inHg, inches)")
    print("=" * 80)
    url_us = t.format_url(r_us)
    print(url_us)
    print()
    
    # Test 2: Purely Metric Units (weewx.METRIC)
    # METRIC: temperature=°C, speed=km/h, pressure=mbar, rain=cm
    r_metric = {
        'dateTime': int(time.time() + 0.5),
        'usUnits': weewx.METRIC,
        'outTemp': 22.5,               # 22.5°C → 22.5°C
        'outHumidity': 65,             # 65%
        'windSpeed': 17.5,             # 17.5 km/h → 4.86 m/s → 9.45 knots
        'windGust': 28.0,              # 28.0 km/h → 7.78 m/s → 15.11 knots
        'windDir': 180,                # 180°
        'barometer': 1013.2,           # 1013.2 mbar → 1013.2 hPa
        'hourRain': 0.24,              # 0.24 cm → 2.4 mm
        'UV': 5,                       # 5
        'dewpoint': 14.2               # 14.2°C → 14.2°C
    }
    
    print("=" * 80)
    print("Test 2 - Purely Metric Units (weewx.METRIC)")
    print("Input: Metric units (°C, km/h, mbar, cm)")
    print("=" * 80)
    url_metric = t.format_url(r_metric)
    print(url_metric)
    print()
    
    # Test 3: Purely MetricWX Units (weewx.METRICWX)
    # METRICWX: temperature=°C, speed=m/s, pressure=hPa, rain=mm
    r_metricwx = {
        'dateTime': int(time.time() + 0.5),
        'usUnits': weewx.METRICWX,
        'outTemp': 22.5,               # 22.5°C → 22.5°C
        'outHumidity': 65,             # 65%
        'windSpeed': 4.86,             # 4.86 m/s → 4.86 m/s → 9.44 knots
        'windGust': 7.78,              # 7.78 m/s → 7.78 m/s → 15.10 knots
        'windDir': 180,                # 180°
        'barometer': 1013.2,           # 1013.2 hPa → 1013.2 hPa
        'hourRain': 2.4,               # 2.4 mm → 2.4 mm
        'UV': 5,                       # 5
        'dewpoint': 14.2               # 14.2°C → 14.2°C
    }
    
    print("=" * 80)
    print("Test 3 - Purely MetricWX Units (weewx.METRICWX)")
    print("Input: MetricWX units (°C, m/s, hPa, mm)")
    print("=" * 80)
    url_metricwx = t.format_url(r_metricwx)
    print(url_metricwx)
    print()
    
    print("=" * 80)
    print("Expected Outputs (for all three tests - should be identical):")
    print("=" * 80)
    print("temperature=22.5 (°C)")
    print("rh=65 (%)")
    print("mslp=1013.2 (hPa)")
    print("wind_dir=180 (°)")
    print("wind_avg=9.4 or 9.5 (knots from m/s)")
    print("wind_max=15.1 or 15.2 (knots from m/s)")
    print("wind_min=9.4 or 9.5 (knots from m/s)")
    print("precip=2.4 (mm hourRain)")
    print("uv=5 (index)")
    print("dewpoint=14.2 (°C)")
    print("=" * 80)
