import io
import re
import fnmatch
import logging
from pathlib import Path
from itertools import chain
from datetime import date, datetime, timedelta

from dateutil import rrule
from dateutil.easter import easter
from dateutil.tz import gettz

import toml

from . import utils
from .db import client
from .timezones import zones

logger = logging.getLogger(__name__)

DEFAULT_FORMAT = "%Y-%m-%d %H:%M:%S%z (%Z) %jd%Ww (%C) [%O]"
DEFAULT_TOML = f"""\
[calendar]
months = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

[holidays.US]
# Relative to Easter
"Easter" = "Easter +0"
"Ash Wednesday" = "Easter -46"
"Mardi Gras" = "Easter -47"
"Palm Sunday" = "Easter -7"
"Good Friday" = "Easter -2"

# Floating holidays
"Memorial Day" = "Last Mon in May"
"MLK Day" = "3rd Mon in Jan"
"Presidents' Day" = "3rd Mon in Feb"
"Mother's Day" = "2nd Sun in May"
"Father's Day" = "3rd Sun in Jun"
"Labor" = "1st Mon in Sep"
"Columbus Day" = "2nd Mon in Oct"
"Thanksgiving" = "4th Thr in Nov"

# Fixed holidays
"New Year's Day" = "Jan 1"
"Valentine's Day" = "Feb 14"
"St. Patrick's Day" = "Mar 17"
"Juneteenth" = "Jun 19"
"Independence Day" = "Jul 4"
"Halloween" = "Oct 31"
"Veterans Day" = "Nov 11"
"Christmas" = "Dec 25"

[lunar]
phases = [
    "New Moon",
    "Waxing Crescent",
    "First Quarter",
    "Waxing Gibbous",
    "Full Moon",
    "Waning Gibbous",
    "Last Quarter",
    "Waning Crescent",
]

[formats]
default = "{DEFAULT_FORMAT}"
"""

class WhenError(Exception):
    pass


class UnknownSourceError(WhenError):
    pass


class Settings:
    def __init__(self):
        self.defaults = toml.loads(DEFAULT_TOML)
        self.data = self.defaults.copy()
        name = ".whenrc.toml"
        self.read_from = self.read(Path.cwd() / name, Path.home() / name)

    def __getitem__(self, key):
        return self.data[key]

    def read(self, *paths):
        found = []
        for path in paths:
            try:
                data = toml.load(path)
            except FileNotFoundError:
                pass
            else:
                found.append(path)
                self.data.update(data)
        return found

    def write_text(self):
        from pprint import pprint
        pprint(self.data)
        print("-" * 40)
        text = f"# Read from {''.join(self.read_from)}\n" if self.read_from else ""
        return f"{text}{toml.dumps(self.data)}"


settings = Settings()

class LunarPhase:
    JULIAN_OFFSET = 1721424.5
    LUNAR_CYCLE = 29.53
    KNOWN_NEW_MOON = 2451549.5
    EMOJIS = "🌑🌒🌓🌔🌕🌖🌗🌘"
    NAMES = settings["lunar"]["phases"]

    def __init__(self, dt=None, dt_fmt="%a, %b %d %Y"):
        self.dt = dt or datetime.now()
        self.dt_fmt = dt_fmt

        self.julian = dt.toordinal() + self.JULIAN_OFFSET
        new_moons = (self.julian - self.KNOWN_NEW_MOON) / self.LUNAR_CYCLE
        self.age = (new_moons - int(new_moons)) * self.LUNAR_CYCLE
        self.index = int(self.age / (self.LUNAR_CYCLE / 8))
        self.emoji = self.EMOJIS[self.index]
        self.name = self.NAMES[self.index]

    @property
    def description(self):
        return f"{self.emoji} {self.name}"

    def __str__(self):
        dt_fmt = self.dt.strftime(self.dt_fmt)
        return f"{dt_fmt} {self.description}"


def holidays(co="US", ts=None):
    year = datetime(int(ts) if ts else datetime.now().year, 1, 1)
    holiday_fmt = "%a, %b %d %Y"
    wkds = "(mon|tue|wed|thr|fri|sat|sun)"
    mos = [
        "jan",
        "feb",
        "mar",
        "apr",
        "may",
        "jun",
        "jul",
        "aug",
        "sep",
        "oct",
        "nov",
        "dec",
    ]
    mos_pat = "|".join(mos)

    def easter_offset(m):
        return easter(year.year) + timedelta(days=int(m.group(1)))

    def fixed(m):
        mo, day = m.groups()
        return date(year.year, mos.index(mo.lower()) + 1, int(day))

    def floating(m):
        ordinal, day, mo = m.groups()
        ordinal = -1 if ordinal.lower() == "la" else int(ordinal)
        wkd = getattr(rrule, day[:2].upper())(ordinal)
        mo = mos.index(mo.lower()) + 1
        rule = rrule.rrule(
            rrule.YEARLY, count=1, byweekday=wkd, bymonth=mo, dtstart=year
        )
        res = list(rule)[0]
        return res.date() if res else ""

    strategies = [
        (re.compile(r"^easter ([+-]\d+)", re.I), easter_offset),
        (
            re.compile(rf"^(la|\d)(?:st|rd|th|nd) {wkds} in ({mos_pat})$", re.I),
            floating,
        ),
        (re.compile(rf"^({mos_pat}) (\d\d?)$", re.I), fixed),
    ]

    results = []
    for title, expr in settings["holidays"][co].items():
        for regex, callback in strategies:
            m = regex.match(expr)
            if m:
                results.append([title, callback(m)])
                break

    mx = 2 + max(len(t[0]) for t in results)
    for title, dt in sorted(results, key=lambda o: o[1]):
        print(
            "{:.<{}}{} [{}]".format(
                title, mx, dt.strftime(holiday_fmt), LunarPhase(dt).description
            )
        )


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

    @staticmethod
    def render_extras(zone):
        extra = f" ({zone.name})"
        if zone.city:
            extra = f" ({zone.city})"

        return extra

    def default_format(self, result, format):
        zone = result.zone
        fmt = format.replace("%C", f"{zone.city}" if zone.city else "")

        if "%Z" in fmt:
            fmt = fmt.replace("%Z", result.zone.zone_name(result.dt))

        if "%O" in fmt:
            lp = LunarPhase(result.dt)
            fmt = fmt.replace("%O", f"{lp.description}")

        return result.dt.strftime(fmt).strip()

    def rfc2822_format(self, result):
        dt = result.dt
        tt = dt.timetuple()
        mo = settings["calendar"]["months"][tt[1] - 1]
        weekday = settings["calendar"]["days"][tt[6]]

        return (
            f"{weekday}, {tt[2]:02} {mo} {tt[0]:04} {tt[3]:02}:{tt[4]:02}:{tt[5]:02} "
            f"{dt.strftime('%z')}{self.render_extras(result.zone)}"
        )

    def iso_format(self, result):
        return f"{result.dt.isoformat()}{self.render_extras(result.zone)}"

    def __call__(self, result):
        if self.format == "iso":
            return self.iso_format(result)
        elif self.format == "rfc2822":
            return self.rfc2822_format(result)

        return self.default_format(result, self.format)


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
        self.tz_dict = {}
        for z in utils.all_zones():
            self.tz_dict[z] = z
            self.tz_dict[z.lower()] = z

        self.tz_keys = list(self.tz_dict) + list(self.aliases)
        self.local_zone = local_zone or TimeZoneDetail()

    def get_tz(self, name):
        value = self.aliases.get(name, None)
        if not value:
            value = self.tz_dict[name]

        return (gettz(value), name)

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

    def parse_source_timestamp(self, ts, source_zones=None):
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
                raise UnknownSourceError(
                    f"Could not find sources: {', '.join(sources)}"
                )

        if targets:
            target_zones = self.find_zones(targets)
        else:
            if sources and ts:
                target_zones = self.find_zones()

        results = self.parse_source_timestamp(ts, source_zones)
        logger.debug("WHEN: %s", results)

        if target_zones:
            results = [result.convert(tz) for result in results for tz in target_zones]

        return results
