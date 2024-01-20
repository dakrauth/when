import os
import re
import sys
import time
import decimal
from pathlib import Path
from datetime import datetime

import requests
from dateutil.tz import tzfile, gettz as _gettz
from dateutil.zoneinfo import get_zonefile_instance
from dateutil.parser import parse as dt_parse

utc_offset_re = re.compile(r"\b(UTC([+-]\d\d?)(?::(\d\d))?)")


def gettz(name=None):
    tz = _gettz(name)
    if name is None:
        name = get_timezone_db_name(tz)
        if name is not None:
            tz = _gettz(name)

    return tz


def parse(value):
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
            raise
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

    def inner(*args, **kwargs):
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

    if "/zoneinfo/" in filename:
        filename = filename.rpartition("/zoneinfo/")[-1]

    return filename


def all_zones():
    zi = get_zonefile_instance()
    return sorted(zi.zones)


def main():
    print(parse(" ".join(sys.argv[1:])))


if __name__ == "__main__":
    main()
