#!/usr/bin/env python
import sys
import argparse
import logging

from .when import When, DEFAULT_FORMAT
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
        help='Timezone to convert the timestamp to'
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
        '--verbose',
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

    return parser


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

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG if args.verbose > 1 else logging.INFO)

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
    for result in when.convert(ts, tzstrs):
        print(when.formatter(result))


if __name__ == '__main__':
    main()
