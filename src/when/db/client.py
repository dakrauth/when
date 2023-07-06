import re
import sqlite3
import logging
from collections import namedtuple
from pathlib import Path

from .. import utils

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
SELECT c.id, c.name, c.ascii, c.co, c.sub, c.tz
FROM city c
WHERE
    c.id = :value OR
    {}
"""

MISSING_DB = """
The when database is not currently available. You can generate it easily
(assuming you have internet access) by issuing the following command:

    when --db

For details, see:

    when --help
"""


class City(namedtuple("City", ["id", "name", "ascii", "co", "sub", "tz"])):
    __slots__ = ()
    sub_number_re = re.compile(r"\d")

    def __str__(self):
        bits = [self.name, self.co]
        if not self.sub_number_re.search(self.sub):
            bits.insert(1, self.sub)

        return ", ".join(bits)

    def __repr__(self):
        return f"City({self.ascii},{self.sub},{self.co} {self.tz})"


class DBError(RuntimeError):
    pass


class DB:
    MEMORY_DB = ":memory:"

    def __init__(self, filename=None):
        self.filename = None if filename == self.MEMORY_DB else Path(filename or DB_FILENAME)
        self._memory = None

    @property
    def _db(self):
        if self.filename:
            return sqlite3.connect(self.filename)

        if not self._memory:
            self._memory = sqlite3.connect(self.MEMORY_DB)

        return self._memory

    @property
    def connection(self):
        if self.filename and not self.filename.exists():
            raise DBError(MISSING_DB)

        return self._db

    def add_alias(self, name, gid):
        con = self.connection
        with con:
            con.executemany(
                "INSERT INTO alias(alias, city_id) VALUES (?, ?)",
                [(val.strip(), gid) for val in name.split(",")],
            )

        if self.filename:
            con.close()

    def close(self, con):
        if self.filename:
            con.close()

    @utils.timer
    def create_db(self, data, remove_existing=True):
        if self.filename and self.filename.exists() and remove_existing:
            self.filename.unlink()

        con = self._db
        cur = con.cursor()
        cur.executescript(DB_SCHEMA)
        cur.executemany("INSERT INTO city VALUES (?, ?, ?, ?, ?, ?, ?)", data)
        con.commit()

        self.close(con)

    def search(self, value):
        try:
            con = self.connection
        except DBError as e:
            logger.warning(str(e))
            return []

        result = con.execute(
            """
                SELECT c.id, c.name, c.ascii, c.co, c.sub, c.tz
                FROM city c
                LEFT JOIN alias a on a.city_id = c.id
                WHERE a.alias = ?
            """,
            (value,),
        ).fetchall()

        if not result:
            sub = co = ""
            like_exprs = ["c.name LIKE :like", "c.ascii LIKE :like"]
            bits = [a.strip() for a in value.split(",")]
            nbits = len(bits)
            if nbits == 2:
                value, co = bits
                like_exprs = [f"({bit} AND c.co = :co)" for bit in like_exprs]
            elif nbits == 3:
                value, sub, co = bits
                like_exprs = [f"({bit} AND c.co = :co AND c.sub = :sub)" for bit in like_exprs]
            elif nbits > 4:
                raise ValueError(f"Invalid search expression: {value}")

            like_exprs = " OR ".join(like_exprs)
            sql = SEARCH_QUERY.format(like_exprs)
            dct = {
                "like": f"%{value}%",
                "value": value,
                "co": co.upper(),
                "sub": sub.upper(),
            }
            cursor = con.cursor()
            cursor.execute(sql, dct)
            result = cursor.fetchall()

        self.close(con)

        return [City(*r) for r in result]
