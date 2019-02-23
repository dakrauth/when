import os
import sys
import logging
from collections import defaultdict
from pprint import pformat
from zipfile import ZipFile, ZIP_DEFLATED
from operator import itemgetter
from zipimport import zipimporter

import pytz
try:
    from unidecode import unidecode
except ImportError:
    unidecode = None

logger = logging.getLogger(__name__)


def get_common(zip_file_name=None):
    if not zip_file_name:
        zip_file_name = os.path.join(os.path.dirname(__file__), 'common.zip')
    return zipimporter(zip_file_name).load_module('common').common


def all_zones():
    return sorted(list(pytz.all_timezones))


def find_city(name):
    bits = name.rsplit(',', 1)
    name, co = bits if len(bits) == 2 else (bits[0], None)
    result = get_common().get(name.lower(), None)
    if result:
        if co:
            co = co.lower()
            return [a for a,b in result if b == co]
        else:
            return list(map(itemgetter(0), result))


def parse_cities(fname):
    if not unidecode:
        logger.warning('You should install Unidecode>=1.0.23')

    with open(fname) as fp:
        data = fp.read()

    lines = [line.split('\t') for line in data.splitlines()]
    d = defaultdict(list)
    for city, co, tz in lines:
        city = city.lower()
        co = co.lower()
        d[city].append([tz, co])
        if unidecode:
            city2 = unidecode(city)
            if city2 != city:
                d[city2].append([tz, co])

    with ZipFile('common.zip', 'w') as z:
        z.writestr(
            'common.py',
            'common=(\n{}\n)'.format(pformat(dict(d), indent=0)),
            ZIP_DEFLATED
        )


if __name__ == '__main__':
    parse_cities(sys.argv[1] if len(sys.argv) > 1 else 'query_result.tsv')
