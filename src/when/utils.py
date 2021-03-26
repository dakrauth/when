import os
import sys
import logging
from collections import defaultdict
from pprint import pformat
from zipfile import ZipFile, ZIP_DEFLATED
from operator import itemgetter
from zipimport import zipimporter

from dateutil.tz import tzfile
from dateutil.zoneinfo import get_zonefile_instance

try:
    from unidecode import unidecode
except ImportError:
    unidecode = None

logger = logging.getLogger(__name__)


def get_timezone_db_name(tz):
    return tz._filename.rsplit('/zoneinfo/', 1)[1] if (
        isinstance(tz, tzfile) and
        hasattr(tz, '_filename') and
        '/zoneinfo/' in tz._filename
    ) else None


def get_common(zip_file_name=None):
    if not zip_file_name:
        zip_file_name = os.path.join(os.path.dirname(__file__), 'common.zip')
    return zipimporter(zip_file_name).load_module('common').common


def all_zones():
    zi = get_zonefile_instance()
    return sorted(zi.zones)


def find_city(name, zip_file_name=None):
    bits = name.rsplit(',', 1)
    name, co = bits if len(bits) == 2 else (bits[0], None)
    result = get_common(zip_file_name).get(name.lower(), None)
    if result:
        if co:
            co = co.lower()
            return [a for a, b in result if b == co]
        else:
            return list(map(itemgetter(0), result))


def generate_cities_pyzip(data, fname_out=None):
    fname_out = fname_out or 'common.zip'
    if not unidecode:
        logger.warning('You should install Unidecode>=1.0.23')

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

    with ZipFile(fname_out, 'w') as z:
        z.writestr(
            'common.py',
            'common=(\n{}\n)'.format(pformat(dict(d), indent=0)),
            ZIP_DEFLATED
        )


def main():
    nargs = len(sys.argv)
    fname = sys.argv[1] if nargs > 1 else 'query_result.tsv'
    with open(fname) as fp:
        data = fp.read()

    generate_cities_pyzip(data, sys.argv[2] if nargs > 2 else None)


if __name__ == '__main__':
    main()
