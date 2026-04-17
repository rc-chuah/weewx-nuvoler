# weewx extension for nuvoler
# Copyright © 2026 RC Chuah (Based on weewx-windy by Matthew Wall and Jacques Terrettaz)
# Distributed under the terms of the GNU General Public License (GPLv3)

"""
This is a weewx extension that uploads data to Nuvoler.

https://www.nuvoler.com/

The protocol is described here:

https://www.nuvoler.com/documentation.php

The Nuvoler API expects GET requests with the following parameters:
- station_id: Your station ID
- station_pass: Your station password
- temperature: Temperature in Celsius
- rh: Relative Humidity (%)
- mslp: Mean Sea Level Pressure (hPa)
- wind_dir: Wind Direction (0-360 degrees)
- wind_avg: Average Wind Speed (km/h)
- wind_min: Minimum Wind Speed (km/h)
- wind_max: Maximum Wind Speed (km/h)
- precip: Precipitation (mm)
- uv: UV Index
- dewpoint: Dew Point (Celsius)

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
    DEFAULT_URL = 'https://nuvoler.com/data/recibir.php'

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
        
        Converts record to metric units and builds query parameters
        """
        url = self.server_url
        if weewx.debug >= 2:
            logdbg("url: %s" % url)

        # Convert to metric units (SI) - Nuvoler expects metric
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
            # barometer in metric_record is in hectopascals (hPa)
            parts['mslp'] = round(metric_record['barometer'], 1)

        # Wind Direction (0-360 degrees)
        if 'windDir' in metric_record and metric_record['windDir'] is not None:
            parts['wind_dir'] = int(metric_record['windDir'])

        # Wind Speed (km/h) - Average
        if 'windSpeed' in metric_record and metric_record['windSpeed'] is not None:
            parts['wind_avg'] = round(metric_record['windSpeed'], 1)

        # Wind Gust (km/h) - Maximum
        if 'windGust' in metric_record and metric_record['windGust'] is not None:
            parts['wind_max'] = round(metric_record['windGust'], 1)

        # Wind minimum - WeeWX may not have this, use windSpeed as fallback
        if 'windSpeed' in metric_record and metric_record['windSpeed'] is not None:
            parts['wind_min'] = round(metric_record['windSpeed'], 1)

        # Precipitation (mm)
        if 'rain' in metric_record and metric_record['rain'] is not None:
            parts['precip'] = round(metric_record['rain'], 1)

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
    
    # Test with US units (Fahrenheit)
    r_us = {
        'dateTime': int(time.time() + 0.5),
        'usUnits': weewx.US,
        'outTemp': 72.5,
        'outHumidity': 65,
        'windSpeed': 5.6,
        'windGust': 8.9,
        'windDir': 180,
        'barometer': 1013.25,
        'rain': 2.4,
        'UV': 5,
        'dewpoint': 14.2
    }
    
    print("Test 1 - US Units:")
    url_us = t.format_url(r_us)
    print(url_us)
    print()
    
    # Test with metric units (Celsius)
    r_metric = {
        'dateTime': int(time.time() + 0.5),
        'usUnits': weewx.METRIC,
        'outTemp': 22.5,
        'outHumidity': 65,
        'windSpeed': 12.5,
        'windGust': 16.0,
        'windDir': 180,
        'barometer': 1013.2,
        'rain': 2.4,
        'UV': 5,
        'dewpoint': 14.2
    }
    
    print("Test 2 - Metric Units:")
    url_metric = t.format_url(r_metric)
    print(url_metric)
