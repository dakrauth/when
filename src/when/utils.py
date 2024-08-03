import decimal
import os
import re
import sys
import time
import logging
from functools import cache
from datetime import datetime, timedelta
from pathlib import Path

import requests
from dateutil.parser import parse as dt_parse
from dateutil.tz import gettz as _gettz
from dateutil.tz import tzfile
from dateutil.zoneinfo import get_zonefile_instance

from .exceptions import WhenError


@cache
def logger():
    return logging.getLogger("when")


def gettz(name=None):
    tz = _gettz(name)
    if name is None:
        name = get_timezone_db_name(tz)
        if name is not None:
            tz = _gettz(name)

    return tz


def format_timedelta(td, short=False):
    seconds = int(td.total_seconds())
    sign = "-" if seconds < 0 else ""
    seconds = abs(seconds)
    values = []

    minutes, seconds = seconds // 60, seconds % 60
    hours, minutes = minutes // 60, minutes % 60
    days, hours = hours // 24, hours % 24
    weeks, days = days // 7, days % 7

    if seconds:
        values.append(
            f"{seconds}s"
            if short
            else "{} second{}".format(
                seconds,
                "s" if seconds > 1 else "",
            )
        )

    if minutes:
        values.append(
            f"{minutes}m" if short else "{} minute{}".format(minutes, "s" if minutes > 1 else "")
        )

    if hours:
        values.append(f"{hours}h" if short else "{} hour{}".format(hours, "s" if hours > 1 else ""))

    if days:
        values.append(f"{days}d" if short else "{} day{}".format(days, "s" if days > 1 else ""))

    if weeks:
        values.append(f"{weeks}w" if short else "{} week{}".format(weeks, "s" if weeks > 1 else ""))

    joiner = "" if short else ", "
    return sign + joiner.join(reversed(values))


def parse_timedelta_offset(offset):
    offset = offset.strip()
    sign = +1
    if offset.startswith(("+", "-", "~")):
        sign = 1 if offset[0] == "+" else -1
        offset = offset[1:]

    if len(offset) < 2:
        raise WhenError("Invalid offset")

    offset_args = {"days": 0, "hours": 0, "weeks": 0, "minutes": 0, "seconds": 0}
    matches = re.match(r"^(\d+[wdhms])+$", offset, re.IGNORECASE)
    if not matches:
        raise WhenError(f"Unrecognized offset value: {offset}")

    for _, i, kind in re.findall(r"((\d+)([wdhms]))", offset, re.IGNORECASE):
        kind = kind.lower()
        i = int(i)
        match kind:
            case "w":
                offset_args["weeks"] = i
            case "d":
                offset_args["days"] = i
            case "h":
                offset_args["hours"] = i
            case "m":
                offset_args["minutes"] = i
            case "s":
                offset_args["seconds"] = i

    return sign * timedelta(**offset_args)


def parse_timestamp(value):
    dt, tokens = dt_parse(value, fuzzy_with_tokens=True)
    return dt


def datetime_from_timestamp(arg):
    try:
        value = decimal.Decimal(arg)
    except decimal.InvalidOperation:
        return None

    value = float(value)
    try:
        dt = datetime.fromtimestamp(value)
    except ValueError as err:
        if "out of range" not in str(err):
            raise WhenError(f"Invalid timestamp format: {value}")
        dt = datetime.fromtimestamp(value / 1000)

    return dt


def parse_source_input(arg):
    # arg = arg or datetime.now().isoformat()
    if not isinstance(arg, str):
        arg = " ".join(arg)

    value = datetime_from_timestamp(arg)
    return value.isoformat() if value else arg.strip()


def timer(func):
    colorize = "\033[0;37;43m{}\033[0;0m".format

    def inner(*args, **kwargs):  # pragma: no cover
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        print(colorize(f"⌛️ {func.__name__}: {duration}"), file=sys.stderr)
        return result

    return inner if os.getenv("WHENTIMER") else func


@timer
def fetch(url):
    r = requests.get(url)
    if r.ok:
        return r.content

    raise WhenError(f"{r.status_code}: {url}")


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

    if "/zoneinfo/" in filename:
        filename = filename.rpartition("/zoneinfo/")[-1]

    return filename


def all_zones():
    zi = get_zonefile_instance()
    return sorted(zi.zones)
