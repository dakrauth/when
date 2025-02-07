import sys

from . import make, client

CITY_FILE_SIZES = make.CITY_FILE_SIZES


def create(db, size, pop, remove_existing=False, dirname=None):
    dirname = dirname or db.filename.parent
    filename = make.fetch_cities(size, dirname=dirname)
    admin_1 = make.fetch_admin_1(dirname=dirname)
    with open(filename) as fp:
        data = make.process_geonames_txt(fp, pop, admin_1)

    db.create_db(data, remove_existing)


def db_main(db, args):
    try:
        if args.db_size:
            create(db, args.db_size, args.db_pop, args.db_force)
        elif args.db_search:
            for row in db.search(" ".join(args.timestr), args.db_exact):
                print(f"{row.id:7} {row}")
        elif args.db_alias:
            db.add_alias(" ".join(args.timestr), args.db_alias)
        elif args.db_aliases:
            for row in db.aliases():
                alias, *details = row
                print(f"{alias}: {' | '.join(details)}")

    except client.DBError as err:
        print(f"{err}", file=sys.stderr)
        return -1

    return 0
