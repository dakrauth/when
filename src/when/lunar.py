import re
from datetime import datetime, timedelta

import fullmoon

from .exceptions import WhenError


JULIAN_OFFSET = 1721424.5
KNOWN_NEW_MOON = 2451549.5
SYNMONTH = 29.53050000
YEAR_MONTH_RE = re.compile(r"^\d\d\d\d-\d\d?$")


def lunar_phase(settings, dt=None, dt_fmt=None):
    dt = dt or datetime.now()
    dt_fmt = dt_fmt or settings["format"]

    julian = dt.toordinal() + JULIAN_OFFSET
    new_moons = (julian - KNOWN_NEW_MOON) / SYNMONTH
    age = (new_moons - int(new_moons)) * SYNMONTH
    index = int(age / (SYNMONTH / 8))

    emoji = settings["emojis"][index]
    name = settings["phases"][index]
    return emoji, name, age


def full_moon_iterator(dt=None):
    n = fullmoon.NextFullMoon()
    if dt:
        n.set_origin_datetime(dt)

    while True:
        yield n.next_full_moon().date()


def full_moons_for_year(year):
    dt = datetime(year - 1, 12, 31)
    nfm = full_moon_iterator(dt)
    dates = []
    while True:
        dt = next(nfm)
        if dt.year > year:
            break

        dates.append(dt)

    return dates


def full_moon(arg=None):
    match arg:
        case "next":
            return [next(full_moon_iterator())]
        case "last" | "prev":
            return [next(full_moon_iterator(datetime.now() - timedelta(days=SYNMONTH)))]
        case arg if isinstance(arg, int):
            return full_moons_for_year(arg)
        case arg if isinstance(arg, str) and arg.isdigit():
            return full_moons_for_year(int(arg))
        case arg if isinstance(arg, str) and YEAR_MONTH_RE.match(arg):
            y, m = [int(i) for i in arg.split("-")]
            it = full_moon_iterator(datetime(y, m, 1))
            dates = []
            while True:
                dt = next(it)
                if dt.month != m:
                    break

                dates.append(dt)
            return dates
        case None | "":
            return full_moons_for_year(int(datetime.now().year))

    raise WhenError(f"Unknown arg for full_moon: {arg}")
