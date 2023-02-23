#!/usr/bin/env python
"""
Examples:
=========

# Show the time in a given source city or time zone

when --source New York City
when --source America/New_York

# Show the specified time at a given source in local time

when --source Paris,FR 21:35

# Show the specified time at a given source in the target locale's time

when --target Bangkok --source Seattle
"""
import re
import sys
import logging
import argparse
import decimal
from datetime import date, datetime, timedelta

from dateutil import rrule
from dateutil.easter import easter

from . import core
from .db import make
from .db import client
from . import VERSION
from . import utils
from .lunar import LunarPhase

logger = logging.getLogger(__name__)
HOLIDAYS = {
    "US": [
        # Relative to Easter
        ("Easter", "Easter +0"),
        ("Ash Wednesday", "Easter -46"),
        ("Mardi Gras", "Easter -47"),
        ("Palm Sunday", "Easter -7"),
        ("Good Friday", "Easter -2"),

        # Floating holidays
        ("Memorial Day",  "Last Mon in May"),
        ("MLK Day", "3rd Mon in Jan"),
        ("Presidents' Day", "3rd Mon in Feb"),
        ("Mother's Day", "2nd Sun in May"),
        ("Father's Day", "3rd Sun in Jun"),
        ("Labor", "1st Mon in Sep"),
        ("Columbus Day", "2nd Mon in Oct"),
        ("Thanksgiving", "4th Thr in Nov"),

        # Fixed holidays
        ("New Year's Day", "Jan 1"),
        ("Valentine's Day", "Feb 14"),
        ("St. Patrick's Day", "Mar 17"),
        ("Juneteenth", "Jun 19"),
        ("Independence Day", "Jul 4"),
        ("Halloween", "Oct 31"),
        ("Veterans Day", "Nov 11"),
        ("Christmas", "Dec 25"),
    ]
}


def db_main(args, db):
    if args.search:
        for row in db.search(args.search):
            print(", ".join(str(c) for c in row))
        return 0

    if args.alias:
        value = " ".join(args.timestamp)
        db.add_alias(value, args.alias)
        return 0

    filename = make.fetch_cities(args.size)
    admin_1 = make.fetch_admin_1()
    data = make.process_geonames_txt(filename, args.pop, admin_1)
    db.create_db(data, admin_1)
    return 0


def holidays(co="US", ts=None):
    year = datetime(int(ts) if ts else datetime.now().year, 1, 1)
    holiday_fmt = "%a, %b %d %Y"
    wkds = "(mon|tue|wed|thr|fri|sat|sun)"
    mos = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    mos_pat = '|'.join(mos)

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
        (re.compile(fr"^(la|\d)(?:st|rd|th|nd) {wkds} in ({mos_pat})$", re.I), floating),
        (re.compile(fr"^({mos_pat}) (\d\d?)$", re.I), fixed),
    ]
    
    results = []
    for title, expr in HOLIDAYS[co.upper()]:
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



def get_parser():
    parser = argparse.ArgumentParser(
        description="Convert times to and from time zones or cities",
        epilog=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "timestamp",
        default="",
        nargs="*",
        help="Timestamp to parse, defaults to local time",
    )

    parser.add_argument(
        "-s",
        "--source",
        action="append",
        help="""
            Timezone / city to convert the timestamp from, defaulting to local time
        """,
    )

    parser.add_argument(
        "-t",
        "--target",
        action="append",
        help="""
            Timezone / city to convert the timestamp to (globbing patterns allowed, can be comma
            delimited), defaulting to local time
        """,
    )

    parser.add_argument(
        "-f",
        "--format",
        default=core.DEFAULT_FORMAT,
        help="""
            Output formatting. Additionaly predefined formats by name are {}.
            Default: {}, where %%K is timezone long name
        """.format(
            ", ".join(["rfc2822, iso, "]),
            core.DEFAULT_FORMAT.replace("%", "%%"),
        ),
    )

    parser.add_argument(
        "--all",
        action="store_true",
        default=False,
        help="Show times in all common timezones",
    )

    parser.add_argument("--holidays", help="Show holidays for given country code.")

    parser.add_argument(
        "-v", "--verbosity", action="count", default=0, help="Verbosity (-v, -vv, etc)"
    )

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version="%(prog)s (version {version})".format(version=VERSION),
    )
    parser.add_argument("--pdb", dest="pdb", action="store_true", default=False)

    # DB options
    parser.add_argument(
        "--db",
        action="store_true",
        default=False,
        help="Togge database mode, used with --search, --alias, --size, and --pop",
    )

    parser.add_argument(
        "--search", help="Search database for the given city (used with --db)"
    )
    parser.add_argument(
        "--alias", type=int, help="(Used with --db) Create a new alias from the city id"
    )

    parser.add_argument(
        "--size",
        default=15_000,
        type=int,
        help="(Used with --db) Geonames file size. Can be one of {}. ".format(
            ", ".join(str(i) for i in make.CITY_FILE_SIZES)
        ),
    )

    parser.add_argument(
        "--pop",
        default=10_000,
        type=int,
        help="(Used with --db) City population minimum.",
    )

    return parser


def log_config(verbosity):
    log_level = logging.WARNING
    log_format = "%(levelname)s: %(message)s"
    if verbosity:
        log_format = "%(levelname)s:%(name)s:%(lineno)d: %(message)s"
        log_level = logging.DEBUG if verbosity > 1 else logging.INFO

    logging.basicConfig(level=log_level, format=log_format)


def from_timestamp(arg):
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

    return dt.isoformat()


def parse_source_input(arg):
    # arg = arg or datetime.now().isoformat()
    if not isinstance(arg, str):
        arg = " ".join(arg)

    value = from_timestamp(arg)
    return value or arg.strip()


def main(sys_args, when=None):
    debug = "--pdb" in sys_args
    if debug:
        sys_args.remove("--pdb")

    args = get_parser().parse_args(sys_args)

    if debug:
        try:
            import ipdb as pdb
        except ImportError:
            import pdb
        pdb.set_trace()

    log_config(args.verbosity)
    when = when or core.When()
    if args.db:
        return db_main(args, when.db)
    elif args.holidays:
        return holidays(args.holidays, args.timestamp[0] if args.timestamp else None)

    ts = parse_source_input(args.timestamp)
    targets = args.target
    if args.all:
        targets = utils.all_zones()

    formatter = core.Formatter(args.format)
    try:
        results = when.convert(ts, args.source, targets)
    except core.UnknownSourceError as e:
        print(e)
        return 1

    for result in results:
        print(formatter(result))

    return 0
