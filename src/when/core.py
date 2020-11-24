import os
import re
import sys
import fnmatch
import logging

from datetime import datetime
from dateutil.parser import parse
from dateutil.tz import gettz

from . import utils

logger = logging.getLogger(__name__)

DEFAULT_FORMAT = '%Y-%m-%d %H:%M:%S%z (%Z) %jd%Ww %K'
ALIASES = dict(
    CEST='CET',
    WEST='WET',
    EEST='EET',
    **{
        f'{i}{j}T': v for i,v in [
            ['P', 'US/Pacific'],
            ['M', 'US/Mountain'],
            ['C', 'US/Central'],
            ['E', 'US/Eastern'],
        ] for j in ['', 'D', 'S']
    }
)


class Formatter:
    format = '%Y-%m-%d %H:%M:%S%z (%Z) %jd%Ww %K'

    def __init__(self, format=None):
        self.format = format or DEFAULT_FORMAT

    def __call__(self, dt):
        tzname = utils.get_timezone_db_name(dt.tzinfo) or '' if dt.tzinfo else ''
        format = self.format.replace('%K', tzname)
        return dt.strftime(format).strip()


class When:

    def __init__(self, tz_aliases=None, formatter=None, local_zone=None):
        self.formatter = formatter
        if isinstance(formatter, (str, type(None))):
            self.formatter = Formatter(formatter)

        offsets = [f'UTC{i}' for i in range(-12, 13) if i]
        self.aliases = ALIASES.copy()
        self.aliases.update({o: o for o in offsets})
        if tz_aliases:
            self.aliases.update(tz_aliases)

        self.tz_keys = utils.all_zones() + list(self.aliases) + offsets
        self.tz_regex = re.compile(
            '({})'.format('|'.join([re.escape(a) for a in self.tz_keys]))
        )

        if local_zone is None and os.path.exists('/etc/localtime'):
            link = os.readlink("/etc/localtime")
            tzname = link[link.rfind("zoneinfo/") + 9:]
            local_zone = gettz(tzname)
        self.local_zone = local_zone

    def normalize_tzname(self, name):
        return self.aliases.get(name, name)

    def get_tz(self, name):
        name = self.normalize_tzname(name)
        return gettz(name)

    def extract_tz(self, ts_str):
        m = self.tz_regex.search(ts_str)
        tz = None
        if not m:
            return ts_str, None

        ts_str = self.tz_regex.sub('', ts_str).strip()
        tz = self.get_tz(m.group())
        return ts_str, tz

    def parse(self, ts_str):
        ts_str, extracted_tz = self.extract_tz(ts_str)
        if ts_str:
            result = parse(ts_str)
        else:
            result = datetime.now()

        logger.info('WHEN 1: %s', self.formatter(result))

        if extracted_tz:
            result = result.replace(tzinfo=extracted_tz)
        else:
            if not result.tzinfo:
                result = result.replace(tzinfo=self.local_zone)

        return result

    def zone_info(self, ts_str):
        dt = self.parse(ts_str)
        tz = dt.tzinfo
        std = tz._ttinfo_std
        hours = std.offset // 3600
        minutes = std.offset % 3600 // 60
        return [
            ('Offset', f'{hours:+03d}:{minutes:02d}'),
            ('Offset (seconds)', std.offset),
            ('Abbreviation', std.abbr or ''),
        ]

    def get_tzs(self, obj):
        if not obj:
            return [self.local_zone]

        if isinstance(obj, str):
            obj = obj.split(',')

        tzs = []
        for o in obj:
            matches = fnmatch.filter(self.tz_keys, o)
            if matches:
                for m in matches:
                    tz = self.get_tz(m)
                    if tz not in tzs:
                        tzs.append(tz)
            else:
                logger.warning('{} time zone subset not found'.format(o))
        return tzs

    def results(self, dt, tzs):
        return [dt.astimezone(tz) for tz in tzs]

    def convert(self, ts_str=None, as_tzs=None):
        logger.info(f'GOT string {ts_str}, zones: {as_tzs}')
        as_tzs = self.get_tzs(as_tzs)

        if not ts_str:
            now = datetime.now(self.local_zone)
            if as_tzs:
                return self.results(now, as_tzs)

            return [now]

        # ts_str, ex_tz = self.extract_tz(ts_str)

        result = self.parse(ts_str)
        logger.info('WHEN 1: %s', self.formatter(result))

        #if ex_tz:
        #    result = result.replace(tzinfo=ex_tz)
        #else:
        #    if not result.tzinfo:
        #        result = result.replace(tzinfo=self.local_zone)

        logger.info('WHEN 2: %s', self.formatter(result))

        return self.results(result, as_tzs)
