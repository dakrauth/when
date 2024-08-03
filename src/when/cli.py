#!/usr/bin/env python
import argparse
import sys
import logging
from pathlib import Path

from . import __version__, core, db, utils, lunar, exceptions
from . import timezones
from .config import Settings, __doc__ as FORMAT_HELP


class DBSizeAction(argparse.Action):
    city_file_sizes = [
        ("xl", "xlarge", 500, "10M"),
        ("lg", "large", 1_000, "7.8M"),
        ("md", "medium", 5_000, "3.9M"),
        ("sm", "small", 15_000, "2.3M"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lookup = {}
        for a, b, c, d in self.city_file_sizes:
            self.lookup[a] = c
            self.lookup[b] = c

    def __call__(self, parser, namespace, values, option_string=None):
        if values not in self.lookup:
            raise ValueError(f"{values} not allowed for DB size")

        setattr(namespace, self.dest, self.lookup[values])

    @classmethod
    def format_usage(cls):
        return ", ".join(f"'{a}' ('{b}')" for a, b, *c in cls.city_file_sizes)


def get_parser(settings):
    parser = argparse.ArgumentParser(
        description="Convert times to and from time zones or cities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )

    parser.add_argument(
        "timestr",
        default="",
        nargs="*",
        help="Timestamp to parse, or other contextual input",
    )

    # TODO
    # parser.add_argument(
    #     "--delta",
    #     choices=["long", "short"],
    #     help="Show the delta to the given timestamp",
    # )

    parser.add_argument(
        "--offset",
        type=utils.parse_timedelta_offset,
        help="Show the difference from a given offset",
        metavar=r"[+-]?(\d+wdhm)+",
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
        version="%(prog)s (version {version})".format(version=__version__),
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
        help="Show current configuration settings",
    )

    size_opts = DBSizeAction.format_usage()
    parser.add_argument(
        "--db",
        action=DBSizeAction,
        dest="db_size",
        help=f"Create cities database from Geonames file. Must one of {size_opts}",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        dest="db_force",
        help="Force an existing database to be overwritten",
    )

    parser.add_argument(
        "--search",
        action="store_true",
        default=False,
        dest="db_search",
        help="Search database for the given city",
    )

    parser.add_argument(
        "--exact",
        action="store_true",
        default=False,
        dest="db_exact",
        help="DB searches must be exact",
    )

    parser.add_argument(
        "--alias",
        type=int,
        dest="db_alias",
        help="Create a new alias from the city id"
    )

    parser.add_argument(
        "--aliases",
        action="store_true",
        default=False,
        dest="db_aliases",
        help="Show all DB aliases",
    )

    parser.add_argument(
        "--population",
        default=10_000,
        type=int,
        dest="db_pop",
        help="City population minimum.",
    )

    parser.add_argument(
        "--tz-alias", action="store_true", default=False, help="Search for a time zone alias"
    )

    parser.add_argument(
        "--fullmoon",
        action="store_true",
        default=False,
        help="Show full moon(s) for given year or month. Can be in the format of: "
        "'next' | 'prev' | YYYY[-MM]",
    )

    parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        default=False,
        help="Show helpful usage information",
    )

    return parser


def log_config(verbosity, settings):
    log_level = logging.WARNING
    log_format = "[%(levelname)s]: %(message)s"
    if verbosity:
        log_format = "[%(levelname)s %(pathname)s:%(lineno)d]: %(message)s"
        log_level = logging.INFO
        if verbosity > 1:
            log_level = logging.DEBUG
            logging.getLogger("asyncio").setLevel(logging.WARNING)

    logging.basicConfig(level=log_level, format=log_format, force=True)
    logger = utils.logger()
    logger.debug(
        "Configuration files read: %s",
        ", ".join(str(s) for s in settings.read_from) if settings.read_from else "None",
    )

    return logger


def main(sys_args, when=None, settings=None):
    if "--pdb" in sys_args:  # pragma: no cover
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

    if settings is None:
        settings = when.settings if when else Settings()

    parser = get_parser(settings)
    args = parser.parse_args(sys_args)

    logger = log_config(args.verbosity, settings)
    logger.debug(args)
    if args.help:
        parser.print_help()
        print(FORMAT_HELP if args.verbosity else "\nUse -v option for details\n")
        return 0

    if args.config:
        print(settings.write_text())
        return 0

    if args.prefix:
        print(str(Path(__file__).parent))
        return 0

    if args.holidays:
        return core.holidays(settings, args.holidays, args.timestr[0] if args.timestr else None)

    if args.tz_alias:
        for tz, name in timezones.zones.get(args.timestr[0] if args.timestr else ""):
            print(f"{name:.<40}{tz}")

        return 0

    if args.fullmoon:
        for result in lunar.full_moon(args.timestr[0] if args.timestr else ""):
            print(result)

        return 0

    when = when or core.When(settings)
    db_triggers = ("db_size", "db_search", "db_alias")
    if any(a for a in vars(args) if a.startswith(db_triggers) and getattr(args, a)):
        return db.db_main(when.db, args)

    targets = utils.all_zones() if args.all else args.target
    if args.json:
        print(
            when.as_json(
                args.timestr,
                sources=args.source,
                targets=targets,
                indent=2,
                offset=args.offset,
                exact=args.db_exact,
            )
        )
        return 0

    formatter = when.formatter(args.format)
    try:
        results = when.results(
            args.timestr,
            targets=targets,
            sources=args.source,
            offset=args.offset,
            exact=args.db_exact,
        )
    except exceptions.UnknownSourceError as e:
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
