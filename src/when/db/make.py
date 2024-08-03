import io
import time
import logging
import zipfile
from collections import defaultdict, namedtuple
from pathlib import Path

from .. import utils

logger = utils.logger()
GeoCity = namedtuple(
    "GeoCity",
    "gid,"
    "name,"
    "aname,"
    "alt,"
    "lat,"
    "lng,"
    "fclass,"
    "fcode,"
    "co,"
    "cc2,"
    "a1,"
    "a2,"
    "a3,"
    "a4,"
    "pop,"
    "el,"
    "dem,"
    "tz,"
    "mod"
)

DB_DIR = Path(__file__).parent
GEONAMES_CITIES_URL_FMT = "https://download.geonames.org/export/dump/cities{}.zip"
GEONAMES_TZ_URL = "https://download.geonames.org/export/dump/timeZones.txt"
GEONAMES_ADMIN1_URL = "https://download.geonames.org/export/dump/admin1CodesASCII.txt"
CITY_FILE_SIZES = {
    500,  # ~10M
    1_000,  # ~7.8M
    5_000,  # ~3.9M
    15_000,  # ~2.3M
}


@utils.timer
def fetch_cities(size, dirname=DB_DIR):
    assert size in CITY_FILE_SIZES, f"{size} is invalid"
    txt_filename = dirname / f"cities{size}.txt"
    if txt_filename.exists():
        return txt_filename

    url = GEONAMES_CITIES_URL_FMT.format(size)
    logger.info(f"Beginning download from {url}")
    start = time.time()
    zip_bytes = utils.fetch(url)
    end = time.time()
    logger.info(f"Received {len(zip_bytes):,} bytes in {end-start:,}s")
    zip_filename = io.BytesIO(zip_bytes)
    with zipfile.ZipFile(zip_filename) as z:
        z.extract(txt_filename.name, txt_filename.parent)

    return txt_filename


@utils.timer
def process_geonames_txt(fobj, minimum_population=15_000, admin_1=None):
    fcodes = defaultdict(int)
    skipped = defaultdict(int)

    # Unconditionally kept
    # --------------------
    # PPLA   seat of a first-order administrative division, seat of a first-order
    #        administrative division (PPLC takes precedence over PPLA)
    # PPLA2  seat of a second-order administrative division
    # PPLA3  seat of a third-order administrative division
    # PPLA4  seat of a fourth-order administrative division
    # PPLA5  seat of a fifth-order administrative division
    # PPLC   capital of a political entity
    # PPLG   seat of government of a political entity

    # Unconditionally skipped
    # -----------------------
    # PPLCH  historical capital of a political entity a former capital of a political entity
    # PPLH   historical populated place, a populated place that no longer exists
    # PPLQ   abandoned populated place
    # PPLW   destroyed populated place, a village, town or city destroyed by a natural disaster,
    #        or by war
    # PPLX   section of populated place
    # STLMT  israeli settlement
    skip = {"PPLCH", "PPLH", "PPLQ", "PPLW", "PPLX", "STLMT"}

    # Conditionally skipped
    # ---------------------
    # PPL    populated place: city, town, village, or other agglomeration of buildings
    #        where people live and work
    # PPLL   populated locality: an area similar to a locality but with a small group of dwellings
    #        or other buildings
    # PPLS   populated places: cities, towns, villages, or other agglomerations of buildings where
    #        people live and work
    # PPLR   religious populated place, a populated place whose population is largely engaged in
    #        religious occupations
    # PPLF   farm village, a populated place where the population is largely engaged in
    #        agricultural activities
    skip_if = {"PPL", "PPLL", "PPLS", "PPLF", "PPLR"}
    admin_1 = admin_1 or {}
    data = []
    for i, line in enumerate(fobj, 1):
        i += 1
        ct = GeoCity(*line.rstrip().split("\t"))

        pop = int(ct.pop) if ct.pop else 0
        if (
            (ct.fcode in skip)
            or (ct.fcode in skip_if and (pop < minimum_population))
            or (ct.fcode == "PPLA5" and ct.name.startswith("Marseille") and ct.name[-1].isdigit())
        ):
            skipped[ct.fcode] += 1
            continue

        fcodes[ct.fcode] += 1
        sub = admin_1.get(f"{ct.co}.{ct.a1}", ct.a1)
        data.append([int(ct.gid), ct.name, ct.aname, ct.co, sub, ct.tz, pop])

    for title, dct in [["KEPT", fcodes], ["SKIP", skipped]]:
        for k, v in sorted(dct.items(), key=lambda kv: kv[1], reverse=True):
            logger.debug(f"{title} {k:5}: {v}")

    logger.info(f"Processed {i:,} lines, kept {len(data):,}")
    return data


def load_admin1(txt):
    data = {}
    for line in txt.splitlines():
        co_sub, name, *_ = line.split("\t")
        data[co_sub] = name

    return data


def fetch_admin_1(dirname=DB_DIR):
    filename = dirname / "admin1CodesASCII.txt"
    if filename.exists():
        txt = filename.read_text()
    else:
        txt = utils.fetch(GEONAMES_ADMIN1_URL).decode()
        filename.write_text(txt)
        logger.info(f"Downloaded {len(txt):,} bytes from {GEONAMES_ADMIN1_URL}")

    return load_admin1(txt)
