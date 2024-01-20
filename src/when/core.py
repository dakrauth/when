import re
import json
import fnmatch
import logging
from itertools import chain
from datetime import date, datetime, timedelta

from dateutil import rrule
from dateutil.easter import easter

from . import utils
from .db import client
from .timezones import zones
from .config import settings, DEFAULT_FORMAT, FORMAT_SPECIFIERS

logger = logging.getLogger(__name__)


class WhenError(Exception):
    pass


class UnknownSourceError(WhenError):
    pass


class LunarPhase:
    JULIAN_OFFSET = 1721424.5
    LUNAR_CYCLE = 29.53
    KNOWN_NEW_MOON = 2451549.5
    NAMES = settings["lunar"]["phases"]
    EMOJIS = settings["lunar"]["emojis"]

    def __init__(self, dt=None, dt_fmt=None):
        self.dt = dt or datetime.now()
        self.dt_fmt = dt_fmt or settings["lunar"]["format"]

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
    holiday_fmt = settings["holidays"]["format"]
    wkds = "({})".format("|".join(day.lower() for day in settings["calendar"]["days"]))
    mos = [mo.lower() for mo in settings["calendar"]["months"]]
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
        rule = rrule.rrule(rrule.YEARLY, count=1, byweekday=wkd, bymonth=mo, dtstart=year)
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
            "{:.<{}}{} [{}]".format(title, mx, dt.strftime(holiday_fmt), LunarPhase(dt).description)
        )


class TimeZoneDetail:
    def __init__(self, tz=None, name=None, city=None):
        self.tz = tz or utils.gettz()
        self.city = city
        self.name = name
        if self.name is None:
            self.name = utils.get_timezone_db_name(self.tz)

    def to_dict(self, dt=None):
        dt = dt or self.now()
        offset = int(self.tz.utcoffset(dt).total_seconds())
        return {
            "name": self.name or self.zone_name(dt),
            "city": self.city.to_dict() if self.city else None,
            "utcoffset": [offset // 3600, offset % 3600 // 60, offset % 60],
        }

    def zone_name(self, dt=None):
        return self.name or (self.city and self.city.tz) or self.tz.tzname(dt or self.now())

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
    def __init__(self, format=DEFAULT_FORMAT):
        format = format or "default"
        self.format = settings["formats"]["named"].get(format, format)

        self.c99_specs = [fs[0][1] for fs in FORMAT_SPECIFIERS if "+" in fs[-1]]
        self.when_specs = [fs[0][2] for fs in FORMAT_SPECIFIERS if "!" == fs[-1]]
        self.cond_specs = [fs[0][2] for fs in FORMAT_SPECIFIERS if "!!" == fs[-1]]

    def token_replacement(self, result, value, pattern, specs, prefix):
        regex = "{}({})".format(pattern, "|".join(specs))
        tokens = re.findall(regex, value)
        for token in tokens:
            fn = getattr(self, f"{prefix}_{token}", None)
            if fn:
                repl = fn(result) or ""
                value = value.replace(f"{pattern}{token}", repl)

        return value

    def __call__(self, result):
        value = self.format
        value = self.token_replacement(result, value, r"%!", self.cond_specs, "when_cond")
        value = self.token_replacement(result, value, r"%!", self.when_specs, "when")

        value = result.dt.strftime(value)
        value = self.token_replacement(result, value, r"%", self.c99_specs, "c99")
        return value

    def when_cond_Z(self, result):
        "If the timezone name is available, render it from the conditional formatting"
        if not result.zone.name:
            return ""

        fmt = settings["formats"]["conditional"]["Z"]
        return fmt.format(result.zone.name)

    def when_cond_C(self, result):
        "If the City name is available, render it from the conditional formatting"
        if not result.zone.city:
            return ""

        fmt = settings["formats"]["conditional"]["C"]
        return fmt.format(result.zone.city)

    def when_z(self, result):
        "When timezone name: US/New_York"
        return result.zone.name

    def when_c(self, result):
        "City name: Honolulu, HI, US"
        return str(result.zone.city) if result.zone.city else None

    def when_l(self, result):
        "Lunar phase emoji: 🌖"
        return LunarPhase(result.dt).description

    def c99_C(self, result):
        "Year divided by 100 and truncated to integer (00-99): 20"
        return f"{result.dt.year // 100}"

    def c99_D(self, result):
        "Short MM/DD/YY date, equivalent to %m/%d/%y: 08/23/01"
        return result.dt.strftime("%m/%d/%y")

    def c99_e(self, result):
        "Day of the month, space-padded ( 1-31): 23"
        return f"{result.dt.day:>2}"

    def c99_F(self, result):
        "Short YYYY-MM-DD date, equivalent to %Y-%m-%d: 2001-08-23"
        return result.dt.strftime("%Y-%m-%d")

    def c99_g(self, result):
        "Week-based year, last two digits (00-99): 01"
        return f"{result.dt.year%100:02}"

    def c99_G(self, result):
        "Week-based year: 2001"
        return f"{result.dt.year:04}"

    def c99_h(self, result):
        "Abbreviated month name (same as %b): Aug"
        return result.dt.strftime("%b")

    def c99_n(self, result):
        "New-line character ('\\n'):"
        return "\n"

    def c99_r(self, result):
        "12-hour clock time: 02:55"
        return result.dt.strftime("%I:%M:%S %p")

    def c99_R(self, result):
        "24-hour HH:MM time, equivalent to %H:%M: 14:55"
        return result.dt.strftime("%H:%M")

    def c99_t(self, result):
        "Horizontal-tab character ('\\t'):"
        return "\t"

    def c99_T(self, result):
        "ISO 8601 time format (HH:MM:SS), equivalent to %H:%M:%S: 14:55:02"
        return result.dt.strftime("%H:%M:%S")

    def c99_u(self, result):
        "ISO 8601 weekday as number with Monday as 1 (1-7): 4"
        return str(result.dt.isoweekday())

    def c99_V(self, result):
        "ISO 8601 week number (01-53): 34"
        return f"{result.dt.isocalendar().week:02}"


class Result:
    def __init__(self, dt, zone, source=None):
        self.dt = dt
        self.zone = zone
        self.source = source

    def to_dict(self):
        return {
            "iso": self.dt.isoformat(),
            "zone": self.zone.to_dict(self.dt),
            "source": self.source.to_dict() if self.source else None,
        }

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

        return (utils.gettz(value), name)

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
                raise UnknownSourceError(f"Could not find sources: {', '.join(sources)}")

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

    def as_json(self, timestamp="", sources=None, targets=None, **json_kwargs):
        return json.dumps(
            [
                result.to_dict()
                for result in self.convert(utils.parse_source_input(timestamp), sources, targets)
            ],
            **json_kwargs,
        )

    def format_results(self, formatter, timestamp="", sources=None, targets=None):
        for result in self.convert(utils.parse_source_input(timestamp), sources, targets):
            yield formatter(result)
