import sys

from . import make
from .client import DBError

CITY_FILE_SIZES = make.CITY_FILE_SIZES


def parse_search(value):
    bits = [a.strip() for a in value.split(",")]
    nbits = len(bits)
    if nbits > 3:
        raise ValueError(f"Invalid city search expression: {value}")

    match nbits:
        case 1:
            return [value, None, None]
        case 2:
            return [bits[0], bits[1], None]
        case 3:
            return bits


def alias(db, alias, value):
    db.add_alias(" ".join(value), alias)


def aliases(db):
    for row in db.aliases():
        alias, *details = row
        print(f"{alias}: {' | '.join(details)}")


def search(db, value, exact=False):
    values = parse_search(" ".join(value))
    fn = db.exact_search if exact else db.search
    for row in fn(*values):
        print(f"{row.id:7} {row}")


def create(db, size, pop, remove_existing=False):
    filename = make.fetch_cities(size)
    admin_1 = make.fetch_admin_1()
    data = make.process_geonames_txt(filename, pop, admin_1)
    db.create_db(data, remove_existing)


def main(db, args):
    try:
        if args.db:
            create(db, args.db_size, args.db_pop, args.db_force)
        elif args.db_search:
            search(db, args.timestr)
        elif args.db_xsearch:
            search(db, args.timestr, True)
        elif args.db_alias:
            alias(db, args.db_alias, args.timestr)
        elif args.db_aliases:
            aliases(db)

    except DBError as err:
        print(f"{err}", file=sys.stderr)
        return -1

    return 0
