import fnmatch
import json
import re
from datetime import date, datetime, timedelta
from itertools import chain

from dateutil import rrule
from dateutil.easter import easter

from . import exceptions, timezones, utils, config
from .db import client
from .lunar import lunar_phase

logger = utils.logger()


def holidays(settings, co="US", ts=None):
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
        delta = dt - date.today()
        emoji, phase, age = lunar_phase(settings["lunar"], dt)
        print(
            "{:.<{}}{} ({:4} days) [{} {}]".format(
                title, mx, dt.strftime(holiday_fmt), delta.days, emoji, phase
            )
        )


class Formatter:
    def __init__(self, settings, format="default", delta=None):
        self.settings = settings
        self.format = self.settings["formats"]["named"].get(format, format)

        self.c99_specs = [fs[0][1] for fs in config.FORMAT_SPECIFIERS if "+" in fs[-1]]
        self.when_specs = [fs[0][2] for fs in config.FORMAT_SPECIFIERS if "!" == fs[-1]]
        self.cond_specs = [fs[0][2] for fs in config.FORMAT_SPECIFIERS if "!!" == fs[-1]]
        self.delta = delta

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
        value = self.token_replacement(result, value, r"%", self.c99_specs, "c99")
        value = result.dt.strftime(value)
        if self.delta:
            # TODO: td = result.dt - result.zone.now()
            delta = utils.format_timedelta(result.delta, short=self.delta == "short")
            if delta:
                value = f"{value}, {delta}"

        return value

    def when_cond_Z(self, result):
        "If the timezone name is available, render it from the conditional formatting"
        if not result.zone.name:
            return ""

        fmt = self.settings["formats"]["conditional"]["Z"]
        return fmt.format(result.zone.name)

    def when_cond_C(self, result):
        "If the City name is available, render it from the conditional formatting"
        if not result.zone.city:
            return ""

        fmt = self.settings["formats"]["conditional"]["C"]
        return fmt.format(result.zone.city)

    def when_z(self, result):
        "When timezone name: US/New_York"
        return result.zone.name

    def when_c(self, result):
        "City name: Honolulu, HI, US"
        return str(result.zone.city) if result.zone.city else None

    def when_l(self, result):
        "Lunar phase emoji: 🌖"
        emoji, phase, age = lunar_phase(self.settings["lunar"], result.dt)
        return f"{emoji} {phase}"

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
        return f"{result.dt.year % 100:02}"

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
            "utcoffset": [offset // 3600, offset % 3600 // 60],
        }

    def zone_name(self, dt=None):
        return self.name or (self.city and self.city.tz) or self.tz.tzname(dt or self.now())

    def now(self):
        return datetime.now(self.tz).replace(microsecond=0)

    def replace(self, dt):
        return dt.replace(tzinfo=self.tz)

    def __str__(self):
        return self.name

    def __repr__(self):
        bits = [f"tz={self.tz}"]
        if self.name:
            bits.append(f"name='{self.name}'")

        if self.city:
            bits.append(f"city='{self.city}'")

        return f"<TimeZoneDetail({', '.join(bits)})>"


class Result:
    def __init__(self, dt, zone, source=None, offset=None):
        self.dt = dt
        self.zone = zone
        self.source = source
        self.offset = offset
        if offset:
            self.dt += offset

    def to_dict(self, settings):
        emoji, phase, age = lunar_phase(settings["lunar"], self.dt)
        return {
            "iso": self.dt.isoformat(),
            "lunar": {"emoji": emoji, "phase": phase, "age": round(age, 5)},
            "zone": self.zone.to_dict(self.dt),
            "source": self.source.to_dict(settings) if self.source else None,
            "offset": utils.format_timedelta(self.offset, short=True) if self.offset else None,
        }

    def convert(self, tz):
        return Result(self.dt.astimezone(tz.tz), tz, self)

    def __repr__(self):
        return f"<Result(dt={self.dt}, zone={self.zone}, offset={self.offset})>"


class When:
    def __init__(self, settings=None, local_zone=None, db=None):
        self.settings = settings or config.Settings()
        self.db = db or client.DB()
        self.tz_dict = {z: z for z in utils.all_zones()}
        for key in list(self.tz_dict):
            self.tz_dict[key.lower()] = self.tz_dict[key]

        self.tz_keys = list(self.tz_dict)
        self.local_zone = local_zone or TimeZoneDetail()

    def formatter(self, format="default", delta=None):
        return Formatter(self.settings, format=format, delta=delta)

    def get_tz(self, name):
        value = self.tz_dict[name]
        return (utils.gettz(value), name)

    def find_zones(self, objs, exact=False):
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

            for tz, name in timezones.zones.get(o):
                tzs.setdefault(name, []).append(TimeZoneDetail(tz, name))

            try:
                results = self.db.search(o, exact)
            except exceptions.DBError as err:
                raise exceptions.WhenError("Missing DB", str(err))

            for c in results:
                tz, name = self.get_tz(c.tz)
                tzs.setdefault(None, []).append(TimeZoneDetail(tz, name, c))

        zones = list(chain.from_iterable(tzs.values()))
        if not zones:
            raise exceptions.UnknownSourceError(
                f"Could not find matching resource: {', '.join(objs)}"
            )

        return zones

    def convert(self, timestr, sources=None, targets=None, offset=None, exact=False):
        """
        +================================================================+
        |                  Without a given timestr                       |
        +================================================================+
        | targets? | sources? | result                                   |
        +----------+----------+------------------------------------------+
        |    N     |    N     | Show current local time info             |
        +----------+----------+------------------------------------------+
        |    Y     |    N     |                                          |
        +----------+----------+ Show current times for targets / sources +
        |    N     |    Y     |                                          |
        +----------+----------+------------------------------------------+
        |    Y     |    Y     | Show sources current time for targets    |
        +================================================================+
        |                  With a given timestr                          |
        +================================================================+
        +----------+----------+------------------------------------------+
        | targets? | sources? | result                                   |
        +----------+----------+------------------------------------------+
        |    N     |    N     | Show time info for given timestr         |
        +----------+----------+------------------------------------------+
        |    Y     |    N     | Convert local timestr to targets         |
        +----------+----------+------------------------------------------+
        |    N     |    Y     | Convert sources timestr to local         |
        +----------+----------+------------------------------------------+
        |    Y     |    Y     | Convert sources timestr to targets       |
        +----------+----------+------------------------------------------+
        """
        logger.debug("GOT ts %s, targets %s, sources: %s", timestr or '""', targets, sources)
        local = self.local_zone
        if not any([timestr, sources, targets]):
            return [Result(local.now(), local, offset=offset)]

        target_zones = self.find_zones(targets, exact) if targets else [local]
        source_zones = self.find_zones(sources, exact) if sources else [local]

        if timestr:
            dt = utils.parse_timestamp(timestr).replace(microsecond=0)
            if not (sources or targets):
                return [Result(local.replace(dt), local, offset=offset)]
            else:
                srcs = [Result(src.replace(dt), src, offset=offset) for src in source_zones]
                return [sz.convert(tz) for sz in srcs for tz in target_zones]

        if sources and targets:
            srcs = [Result(src.now(), src, offset=offset) for src in source_zones]
            return [sz.convert(tz) for sz in srcs for tz in target_zones]

        items = source_zones if sources else target_zones
        return [Result(i.now(), i, offset=offset) for i in items]

    def results(self, timestamp="", sources=None, targets=None, offset=None, exact=False):
        return self.convert(utils.parse_source_input(timestamp), sources, targets, offset, exact)

    def as_json(
        self, timestamp="", sources=None, targets=None, offset=None, exact=False, **json_kwargs
    ):
        converts = self.results(timestamp, sources, targets, offset, exact)
        return json.dumps([convert.to_dict(self.settings) for convert in converts], **json_kwargs)

    def grouped(self, results, offset=None):
        groups = {}
        keys = {}
        for r in results:
            if not r.source:
                groups.setdefault(None, []).append(r)
            else:
                key = (r.dt, r.zone.name, r.zone.city)
                if key not in keys:
                    keys[key] = Result(r.dt, r.zone, offset=offset)

                groups.setdefault(keys[key], []).append(r.source)

        return groups
