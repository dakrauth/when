import os
import re
import sys
import logging

from datetime import datetime
from dateutil.parser import parse
import pytz


logger = logging.getLogger(__name__)
tz_regex = re.compile(
    '({})'.format('|'.join([re.escape(a) for a in pytz.all_timezones]))
)

DEFAULT_FORMAT = '%Y-%m-%d %H:%M:%S%z (%Z) %jd%Ww %K'
ALIASES = {
    'PST': 'US/Pacific',
    'MST': 'US/Mountain',
    'CST': 'US/Central',
}


class Formatter:
    format = '%Y-%m-%d %H:%M:%S%z (%Z) %jd%Ww %K'

    def __init__(self, format=None):
        self.format = format or DEFAULT_FORMAT

    def __call__(self, dt):
        format = self.format.replace('%K', dt.tzinfo.zone if dt.tzinfo else 'N/A')
        return dt.strftime(format)


class When:

    def __init__(self, tz_aliases=None, formatter=None, local_zone=None):
        self.formatter = formatter
        if isinstance(formatter, (str, type(None))):
            self.formatter = Formatter(formatter)

        aliases = ALIASES.copy()
        if tz_aliases:
            aliases.update(tz_aliases)

        tzs = {z: pytz.timezone(z) for z in pytz.all_timezones}
        tzs.update({
            k: pytz.timezone(aliases[k])
            for k in aliases
        })
        self.tzinfos = tzs

        if local_zone is None:
            link = os.readlink("/etc/localtime")
            tzname = link[link.rfind("zoneinfo/") + 9:]
            local_zone = pytz.timezone(tzname)
        self.local_zone = local_zone

    def extract_tz(self, ts_str):
        m = tz_regex.search(ts_str)
        if m:
            tz_name = ts_str[slice(*m.span())]
            ts_str = ts_str.replace(tz_name, '').strip()
            tz = pytz.timezone(tz_name)
        else:
            tz = None

        return ts_str, tz

    def parse(self, ts_str):
        return parse(ts_str, tzinfos=self.tzinfos)

    def get_tzs(self, obj):
        if not obj:
            return [self.local_zone]

        if isinstance(obj, str):
            obj = obj.split(',')

        return [self.tzinfos[o] for o in obj]

    def results(self, dt, tzs):
        return [dt.astimezone(tz) for tz in tzs]

    def convert(self, ts_str=None, as_tzs=None):
        logger.info('GOT string {}, zones: {}'.format(ts_str, as_tzs))
        as_tzs = self.get_tzs(as_tzs)

        if not ts_str:
            now = datetime.now(self.local_zone)
            if as_tzs:
                return self.results(now, as_tzs)

            return [now]

        ts_str, ex_tz = self.extract_tz(ts_str)

        result = self.parse(ts_str)
        logger.info('WHEN 1: %s', self.formatter(result))

        if ex_tz:
            result = ex_tz.localize(result)
        else:
            if not result.tzinfo:
                result = self.local_zone.localize(result)

        logger.info('WHEN 2: %s', self.formatter(result))

        return self.results(result, as_tzs)
