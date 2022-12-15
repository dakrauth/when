import os
import re
import sys
import time
import binascii
from pathlib import Path

import requests
from dateutil.tz import tzfile, tzoffset, gettz
from dateutil.zoneinfo import get_zonefile_instance
from dateutil.parser import parse as dt_parse

from . import timezones
from .lunar import LunarPhase

MONTH_ABBRS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WEEKDAY_ABBRS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

utc_offset_re = re.compile(r"\b(UTC([+-]\d\d?)(?::(\d\d))?)")


def parse(value):
    dt, tokens = dt_parse(value, fuzzy_with_tokens=True)
    return dt


def render_extras(zone):
    extra = f" ({zone.name})"
    if zone.city:
        extra = f" ({zone.city})"

    return extra


def default_format(result, format):
    zone = result.zone
    fmt = format.replace("%C", f" ({zone.city})" if zone.city else "")

    if "%Z" in fmt:
        fmt = fmt.replace("%Z", result.zone.zone_name(result.dt))

    if "%O" in fmt:
        lp = LunarPhase(result.dt)
        fmt = fmt.replace("%O", f"[{lp.description}]")

    return result.dt.strftime(fmt).strip()


def rfc2822_format(result):
    dt = result.dt
    tt = dt.timetuple()
    mo = MONTH_ABBRS[tt[1] - 1]
    weekday = WEEKDAY_ABBRS[tt[6]]

    return (
        f"{weekday}, {tt[2]:02} {mo} {tt[0]:04} {tt[3]:02}:{tt[4]:02}:{tt[5]:02} "
        f"{dt.strftime('%z')}{render_extras(result.zone)}"
    )


def iso_format(result):
    return f"{result.dt.isoformat()}{render_extras(result.zone)}"


def tz_key(tz):
    if isinstance(tz, str):
        tz = tz.encode()

    return binascii.crc32(tz)


def timer(func):
    colorize = "\033[0;37;43m{}\033[0;0m".format

    def inner(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        print(colorize(f"⌛️ {func.__name__}: {duration}"), file=sys.stderr)
        return result

    return inner if os.getenv("WHEN_TIMER") else func


@timer
def fetch(url):
    r = requests.get(url)
    if r.ok:
        return r.content
    else:
        raise RuntimeError(f"{r.status_code}: {url}")


def get_timezone_db_name(tz):
    filename = None
    if isinstance(tz, str):
        filename = tz
    elif isinstance(tz, tzfile):
        filename = getattr(tz, "_filename", None)

    if filename is None:
        return

    if filename == "/etc/localtime":
        filename = str(Path(filename).resolve())

    if "/zonename/" in filename:
        return filename.rsplit("/zoneinfo/", 1)[1]


def all_zones():
    zi = get_zonefile_instance()
    return sorted(zi.zones)


def main():
    print(parse(" ".join(sys.argv[1:])))


if __name__ == "__main__":
    main()
