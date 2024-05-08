#!/usr/bin/env python
import argparse
import logging
import sys
from pathlib import Path

from . import VERSION, core, db, utils
from .config import __doc__ as FORMAT_HELP
from .config import settings

logger = logging.getLogger(__name__)


def get_parser():
    parser = argparse.ArgumentParser(
        description="Convert times to and from time zones or cities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )

    parser.add_argument(
        "timestr",
        default="",
        nargs="*",
        help="Timestamp to parse, defaults to local time",
    )

    parser.add_argument(
        "--delta",
        choices=["long", "short"],
        help="Show the delta to the given timestamp",
    )

    parser.add_argument(
        "--offset",
        type=utils.parse_timedelta_offet,
        help="Show the difference from a given offset",
        metavar=r"[+-]?(\d+wdhm)+",
    )

    parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        default=False,
        help="Show helpful usage information",
    )

    parser.add_argument(
        "--prefix", action="store_true", default=False, help="Show when's directory"
    )

    parser.add_argument(
        "-s",
        "--source",
        action="append",
        help="""
            Timezone / city to convert the timestr from, defaulting to local time
        """,
    )

    parser.add_argument(
        "-t",
        "--target",
        action="append",
        help="""
            Timezone / city to convert the timestr to (globbing patterns allowed, can be comma
            delimited), defaulting to local time
        """,
    )

    default_format = settings["formats"]["named"]["default"]
    parser.add_argument(
        "-f",
        "--format",
        default=default_format,
        help="Output formatting. Additional formats can be shown using the -v option with -h",
    )

    parser.add_argument(
        "-g",
        "--group",
        action="store_true",
        default=False,
        help="Group sources together under same target results",
    )

    parser.add_argument(
        "--all",
        action="store_true",
        default=False,
        help="Show times in all common timezones",
    )

    parser.add_argument(
        "--holidays", help="Show holidays for given country code.", metavar="COUNTRY_CODE"
    )

    parser.add_argument(
        "-v",
        "--verbosity",
        action="count",
        default=0,
        help="Verbosity (-v, -vv, etc). Use -v to show `when` extension detailed help",
    )

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version="%(prog)s (version {version})".format(version=VERSION),
    )

    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output results in nicely formatted JSON",
    )

    # config options
    parser.add_argument(
        "--config",
        action="store_true",
        default=False,
        help="Toggle config mode. With no other option, dump current configuration settings",
    )

    # DB options
    parser.add_argument(
        "--db",
        action="store_true",
        default=False,
        help="Create cities database, used with --db-size and --db-pop",
    )

    parser.add_argument(
        "--db-force",
        action="store_true",
        default=False,
        help="Force an existing database to be overwritten",
    )

    parser.add_argument(
        "--db-search",
        action="store_true",
        default=False,
        help="Search database for the given city with similar value",
    )

    parser.add_argument(
        "--db-xsearch",
        action="store_true",
        default=False,
        help="Search database for the given city with exact value",
    )

    parser.add_argument("--db-alias", type=int, help="Create a new alias from the city id")

    parser.add_argument(
        "--db-aliases",
        action="store_true",
        default=False,
        help="Show all DB aliases",
    )

    parser.add_argument(
        "--db-size",
        default=15_000,
        type=int,
        help="Geonames file size. Can be one of {}. ".format(
            ", ".join(str(i) for i in db.CITY_FILE_SIZES)
        ),
    )

    parser.add_argument(
        "--db-pop",
        default=10_000,
        type=int,
        help="City population minimum.",
    )

    return parser


def log_config(verbosity):
    log_level = logging.WARNING
    log_format = "[%(levelname)s]: %(message)s"
    if verbosity:
        log_format = "[%(levelname)s %(pathname)s:%(lineno)d]: %(message)s"
        log_level = logging.INFO
        if verbosity > 1:
            log_level = logging.DEBUG
            logging.getLogger("asyncio").setLevel(logging.WARNING)

    logging.basicConfig(level=log_level, format=log_format, force=True)
    logger.debug("Configuration files read: %s", ", ".join(settings.read_from) or "None")


def main(sys_args, when=None):
    if "--pdb" in sys_args:
        sys_args.remove("--pdb")
        breakpoint()

    # A silly hack to handle negative offset patterns, otherwise argparse chokes
    try:
        offset_index = sys_args.index("--offset")
    except ValueError:
        pass
    else:
        if (
            offset_index + 1 < len(sys_args)
            and len(sys_args[offset_index + 1]) > 2
            and sys_args[offset_index + 1][0] == "-"
            and sys_args[offset_index + 1][1].isdigit()
        ):
            sys_args[offset_index + 1] = f"~{sys_args[offset_index + 1][1:]}"

    parser = get_parser()
    args = parser.parse_args(sys_args)

    log_config(args.verbosity)
    logger.debug(args)
    if args.help:
        parser.print_help()
        print(FORMAT_HELP if args.verbosity else "\nUse -v option for details\n")
        sys.exit(0)

    if args.config:
        print(settings.write_text())
        return 0

    if args.prefix:
        print(str(Path(__file__).parent))
        return 0

    if args.holidays:
        return core.holidays(args.holidays, args.timestr[0] if args.timestr else None)

    targets = utils.all_zones() if args.all else args.target
    when = when or core.When()
    if any(a for a in vars(args) if a.startswith("db") and getattr(args, a) is True):
        return db.main(when.db, args)

    if args.json:
        print(
            when.as_json(
                args.timestr,
                sources=args.source,
                targets=targets,
                indent=2,
                offset=args.offset,
            )
        )
        return 0

    formatter = core.Formatter(args.format)
    try:
        results = when.results(
            args.timestr,
            targets=targets,
            sources=args.source,
            offset=args.offset,
        )
    except core.UnknownSourceError as e:
        print(e, file=sys.stderr)
        return 1

    if args.group:
        prefix = settings["formats"]["source"]["grouped"]
        grouped = when.grouped(results, offset=args.offset)
        for key in grouped:
            if key is None:
                for result in grouped[key]:
                    print(formatter(result))
            else:
                print(formatter(key))
                for src in grouped[key]:
                    print(f"{prefix}{formatter(src)}")
    else:
        for result in results:
            print(formatter(result))

    return 0
