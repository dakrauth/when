import contextlib
import logging
import re
import sqlite3
from collections import namedtuple
from pathlib import Path

from .. import utils
from ..exceptions import DBError

logger = logging.getLogger(__name__)

DB_FILENAME = Path(__file__).parent / "when.db"
DB_SCHEMA = """
PRAGMA encoding = "UTF-8";
CREATE TABLE "city" (
    "id"    INTEGER PRIMARY KEY,
    "name"  TEXT NOT NULL,
    "ascii" TEXT NOT NULL,
    "co"    TEXT NOT NULL,
    "sub"   TEXT NOT NULL,
    "tz"    TEXT NOT NULL,
    "pop"   INTEGER
);
CREATE TABLE "alias" (
    "alias" TEXT PRIMARY KEY,
    "city_id" INTEGER NOT NULL
);
CREATE INDEX "city-index" ON "alias" ("city_id");
"""

SEARCH_QUERY = """
SELECT c.id, c.name, c.ascii, c.sub, c.co, c.tz
FROM city c
WHERE
    c.id = :value OR
    {}
"""

XSEARCH_QUERY = """
SELECT c.id, c.name, c.ascii, c.sub, c.co, c.tz
FROM city c
WHERE
    (c.id = :value OR c.name = :value OR c.ascii = :value)
"""

ALIASES_LISTING_QUERY = """
SELECT a.alias, c.name, c.sub, c.co, c.tz
FROM alias a
LEFT JOIN city c on a.city_id = c.id
"""

ALIAS_SEARCH_QUERY = """
SELECT c.id, c.name, c.ascii, c.sub, c.co, c.tz
FROM city c
LEFT JOIN alias a on a.city_id = c.id
WHERE a.alias = ?
"""

MISSING_DB = """
The database is not currently available. You can generate it easily
(assuming you have internet access) by issuing the following command:

    when --db

For details, see:

    when --help
"""

EXISTING_DB = """
    An existing database currently exists and will not be overwritten.
    Use the --db-force option to override.
"""


class City(namedtuple("City", ["id", "name", "ascii", "sub", "co", "tz"])):
    __slots__ = ()
    sub_number_re = re.compile(r"\d")
    format_spec_re = re.compile(r"[inasczN]")

    @classmethod
    def from_results(cls, results):
        return [cls(*r) for r in results]

    def __str__(self):
        bits = [self.name, self.co, self.tz]
        if not self.sub_number_re.search(self.sub) and self.sub != self.name:
            bits.insert(1, self.sub)

        if self.name != self.ascii:
            bits[0] = f"{self.name} ({self.ascii})"

        return ", ".join(bits)

    def __format__(self, spec):
        if not spec:
            return str(self)

        def format_repl(m):
            char = m.string[m.start()]
            match char:
                case "i":
                    return str(self.id)
                case "n":
                    return self.name
                case "a":
                    return self.ascii
                case "s":
                    return self.sub
                case "c":
                    return self.co
                case "z":
                    return self.tz
                case "N":
                    if self.name == self.ascii:
                        return self.name

                    return f"{self.name} ({self.ascii})"

        value = self.format_spec_re.sub(format_repl, spec)
        return value

    def __repr__(self):
        return f"City({self.id},{self.name},{self.ascii},{self.sub},{self.co},{self.tz})"

    def to_dict(self):
        dct = {"name": self.name, "ascii": self.ascii, "country": self.co, "tz": self.tz}
        if not self.sub_number_re.search(self.sub):
            dct["subnational"] = self.sub

        return dct


class DB:
    def __init__(self, filename=DB_FILENAME):
        self.filename = Path(filename)

    @property
    def _db(self):
        return sqlite3.connect(self.filename)

    @contextlib.contextmanager
    def connection(self, commit=False, create=False):
        if not create and not self.filename.exists():
            raise DBError(MISSING_DB)

        db = self._db
        try:
            yield db
        finally:
            if commit:
                db.commit()

            db.close()

    def aliases(self):
        with self.connection() as con:
            return con.execute(ALIASES_LISTING_QUERY).fetchall()

    def add_alias(self, name, gid):
        with self.connection(commit=True) as con:
            con.executemany(
                "INSERT INTO alias(alias, city_id) VALUES (?, ?)",
                [(val.strip(), gid) for val in name.split(",")],
            )

    @utils.timer
    def create_db(self, data, remove_existing=True):
        if self.filename.exists():
            if not remove_existing:
                raise DBError(EXISTING_DB)

            self.filename.unlink()

        with self.connection(commit=True, create=True) as con:
            cur = con.cursor()
            cur.executescript(DB_SCHEMA)
            cur.executemany("INSERT INTO city VALUES (?, ?, ?, ?, ?, ?, ?)", data)
            nrows = cur.rowcount

        print(f"Inserted {nrows} rows")

    def _execute(self, con, sql, params):
        return con.execute(sql, params).fetchall()

    def _search(self, sql, value, params):
        with self.connection() as con:
            results = self._execute(con, ALIAS_SEARCH_QUERY, (value,))
            results += self._execute(con, sql, params)

        return City.from_results(results)

    def parse_search(self, value):
        bits = [a.strip() for a in value.split(",")]
        nbits = len(bits)
        if nbits > 3:
            raise DBError(f"Invalid city search expression: {value}")

        match nbits:
            case 1:
                return [value, None, None]
            case 2:
                return [bits[0], bits[1], None]
            case 3:
                return bits

    def search(self, value, exact=False):
        value, co, sub = self.parse_search(value)
        if exact:
            sql = XSEARCH_QUERY
            if co:
                sql = f"{sql} AND c.co = :co AND c.sub = :sub" if sub else f"{sql} AND c.co = :co"

            return self._search(
                sql, value, {"value": value, "co": co.upper() if co else co, "sub": sub}
            )

        like_exprs = ["c.name LIKE :like", "c.ascii LIKE :like"]
        if co:
            like_exprs = (
                [f"({bit} AND c.co = :co AND UPPER(c.sub) = :sub)" for bit in like_exprs]
                if sub
                else [f"({bit} AND c.co = :co)" for bit in like_exprs]
            )

        return self._search(
            SEARCH_QUERY.format(" OR ".join(like_exprs)),
            value,
            {
                "like": f"%{value}%",
                "value": value,
                "co": co.upper() if co else co,
                "sub": sub.upper() if sub else sub,
            },
        )
