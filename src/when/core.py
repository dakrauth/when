import fnmatch
import logging
from itertools import chain

from datetime import datetime
from dateutil.tz import gettz

from . import utils
from .db import client
from .timezones import zones

logger = logging.getLogger(__name__)

DEFAULT_FORMAT = "%Y-%m-%d %H:%M:%S%z (%Z) %jd%Ww %C %O"


class TimeZoneDetail:
    def __init__(self, tz=None, name=None, city=None):
        self.tz = tz or gettz()
        self.name = name
        self.city = city

    def zone_name(self, dt):
        tzname = self.tz.tzname(dt)
        return self.name or (self.city and self.city.tz) or tzname

    def now(self):
        return datetime.now(self.tz)

    def replace(self, dt):
        return dt.replace(tzinfo=self.tz)

    def __repr__(self):
        bits = [f"tz={self.tz}"]
        if self.name:
            bits.append(f"name='{self.name}'")

        if self.city:
            bits.append(f"city='{self.city}'")

        return f"<TimeZoneDetail({', '.join(bits)})>"


class Formatter:
    def __init__(self, format=None):
        self.format = format or DEFAULT_FORMAT

    def __call__(self, result):
        if self.format == "iso":
            return utils.iso_format(result)
        elif self.format == "rfc2822":
            return utils.rfc2822_format(result)

        return utils.default_format(result, self.format)


class Result:
    def __init__(self, dt, zone, source=None):
        self.dt = dt
        self.zone = zone
        self.source = source

    def convert(self, tz):
        return Result(self.dt.astimezone(tz.tz), tz, self)

    def __repr__(self):
        return f"<Result(dt={self.dt}, zone={self.zone})>"


class When:
    def __init__(self, tz_aliases=None, formatter=None, local_zone=None, db=None):
        self.db = db or client.DB()
        self.aliases = tz_aliases if tz_aliases else {}
        self.tz_keys = utils.all_zones() + list(self.aliases)
        self.local_zone = local_zone or TimeZoneDetail()

    def get_tz(self, name):
        name = self.aliases.get(name, name)
        return (gettz(name), name)

    def find_zones(self, objs=None):
        if not objs:
            return [self.local_zone]

        if isinstance(objs, str):
            objs = [objs]

        tzs = {}
        for o in objs:
            matches = fnmatch.filter(self.tz_keys, o)
            if matches:
                for m in matches:
                    tz, name = self.get_tz(m)
                    if name not in tzs:
                        tzs.setdefault(name, []).append(TimeZoneDetail(tz, name))

            for tz, name in zones.get(o):
                tzs.setdefault(name, []).append(TimeZoneDetail(tz, name))

            results = self.db.search(o)
            for c in results:
                tz, name = self.get_tz(c.tz)
                tzs.setdefault(None, []).append(TimeZoneDetail(tz, name, c))

        return list(chain.from_iterable(tzs.values()))

    def parse_source(self, ts, source_zones=None):
        source_zones = source_zones or [self.local_zone]
        if ts:
            result = utils.parse(ts)
            return [Result(tz.replace(result), tz) for tz in source_zones]

        return [Result(tz.now(), tz) for tz in source_zones]

    def convert(self, ts, sources=None, targets=None):
        logger.debug("GOT ts %s, targets %s, sources: %s", ts, targets, sources)
        target_zones = None
        source_zones = None
        if sources:
            source_zones = self.find_zones(sources)
            if not source_zones:
                raise ValueError(f"Could not find sources: {sources}")

        if targets:
            target_zones = self.find_zones(targets)
        else:
            if sources and ts:
                target_zones = self.find_zones()

        results = self.parse_source(ts, source_zones)
        logger.debug("WHEN: %s", results)

        if target_zones:
            results = [result.convert(tz) for result in results for tz in target_zones]

        return results
