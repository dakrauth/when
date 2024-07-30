import sys

from . import make, client

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


def aliases(db):
    for row in db.aliases():
        alias, *details = row
        print(f"{alias}: {' | '.join(details)}")


def search(db, value, exact=False):
    values = parse_search(" ".join(value))
    fn = db.exact_search if exact else db.search
    for row in fn(*values):
        print(f"{row.id:7} {row}")


def create(db, size, pop, remove_existing=False, dirname=make.DB_DIR):
    filename = make.fetch_cities(size, dirname=dirname)
    admin_1 = make.fetch_admin_1(dirname=dirname)
    with open(filename) as fp:
        data = make.process_geonames_txt(fp, pop, admin_1)
    db.create_db(data, remove_existing)


def db_main(db, args):
    try:
        if args.db:
            create(db, args.db_size, args.db_pop, args.db_force)
        elif args.db_search:
            search(db, args.timestr)
        elif args.db_xsearch:
            search(db, args.timestr, True)
        elif args.db_alias:
            db.add_alias(" ".join(args.timestr), args.db_alias)
        elif args.db_aliases:
            aliases(db)

    except client.DBError as err:
        print(f"{err}", file=sys.stderr)
        return -1

    return 0
