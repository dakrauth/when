
#!/usr/bin/env python
import sys
import argparse
import logging

from .core import When, DEFAULT_FORMAT
from . import VERSION
from . import utils

logger = logging.getLogger(__name__)


def get_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'timestamp',
        default=None,
        nargs='*',
        help='Optional timestamp to parse, defaults to UTC now'
    )

    parser.add_argument(
        '-z',
        '--zone',
        dest='tzstr',
        default='',
        help='Timezone to convert the timestamp to (globbing patterns allowed)'
    )

    parser.add_argument(
        '-i',
        '--zone-info',
        dest='zone_info',
        action='store_true',
        default=False,
        help='Just show details for a given timezone'
    )
    
    parser.add_argument(
        '-f',
        '--format',
        dest='formatting',
        default=DEFAULT_FORMAT,
        help='Output formatting. Default: {}, where %%K is timezone long name'.format(
            DEFAULT_FORMAT.replace('%', '%%')
        )
    )

    parser.add_argument(
        '-c',
        '--city',
        dest='city',
        action='store_true',
        default=False,
        help='Interpret timestamp as city name'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        default=False,
        help='Show times in all common timezones'
    )

    parser.add_argument(
        '-v',
        '--verbosity',
        action='count',
        default=0,
        help='Verbosity (-v, -vv, etc)'
    )

    parser.add_argument(
        '-V',
        '--version',
        action='version',
        version='%(prog)s (version {version})'.format(version=VERSION)
    )

    parser.add_argument('--pdb', dest='pdb', action='store_true', default=False)
    return parser


def log_config(verbosity):
    log_level = logging.WARNING
    log_format = '%(levelname)s: %(message)s'
    if verbosity:
        log_format = '%(levelname)s:%(name)s:%(lineno)d: %(message)s'
        log_level = logging.DEBUG if verbosity > 1 else logging.INFO

    logging.basicConfig(level=log_level, format=log_format)


def main(parser=None):
    if '--pdb' in sys.argv:
        sys.argv.remove('--pdb')
        try:
            import ipdb as pdb
        except ImportError:
            import pdb
        pdb.set_trace()

    parser = parser or get_parser()
    args = parser.parse_args()

    log_config(args.verbosity)
    ts = args.timestamp
    tzstrs = args.tzstr.split(',') if args.tzstr else None
    if not isinstance(ts, str):
        ts = ' '.join(ts)

    if args.all:
        tzstrs = utils.all_zones()

    if args.city:
        if not ts:
            print('City name required with -c option')
            return

        tzstrs = utils.find_city(ts)
        ts = ''
        if not tzstrs:
            print('Could not find city: {}'.format(args.city))
            return

    when = When(formatter=args.formatting)
    if args.zone_info:
        res = when.zone_info(ts)
        print('\n'.join([f'{k}: {v}' for (k, v) in res]))
    else:
        for result in when.convert(ts, tzstrs):
            print(when.formatter(result))


if __name__ == '__main__':
    main()
