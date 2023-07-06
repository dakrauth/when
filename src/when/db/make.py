import io
import logging
import zipfile
from pathlib import Path
from collections import defaultdict

from .. import utils

logger = logging.getLogger(__name__)

HERE_DIR = Path(__file__).parent
GEONAMES_CITIES_URL_FMT = "http://download.geonames.org/export/dump/cities{}.zip"
GEONAMES_TZ_URL = "https://download.geonames.org/export/dump/timeZones.txt"
GEONAMES_ADMIN1_URL = "https://download.geonames.org/export/dump/admin1CodesASCII.txt"
CITY_FILE_SIZES = {
    500,  # ~ 10M
    1_000,  # ~7.8M
    5_000,  # ~3.9M
    15_000,  # ~2.3M
}


@utils.timer
def fetch_cities(size):
    assert size in CITY_FILE_SIZES
    txt_filename = Path(__file__).parent / f"cities{size}.txt"
    if txt_filename.exists():
        return txt_filename

    zip_bytes = utils.fetch(GEONAMES_CITIES_URL_FMT.format(size))
    zip_filename = io.BytesIO(zip_bytes)
    with zipfile.ZipFile(zip_filename) as z:
        z.extract(txt_filename.name, txt_filename.parent)

    return txt_filename


@utils.timer
def process_geonames_txt(filename, minimum_population=15_000, admin_1=None):
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
    with open(filename) as fp:
        i = 0
        for line in fp:
            i += 1
            (
                gid,
                name,
                aname,
                alt,
                lat,
                lng,
                fclass,
                fcode,
                co,
                cc2,
                a1,
                a2,
                a3,
                a4,
                pop,
                el,
                dem,
                tz,
                mod,
            ) = line.rstrip().split("\t")

            pop = int(pop) if pop else 0
            if (
                (fcode in skip)
                or (fcode in skip_if and (pop < minimum_population))
                or (fcode == "PPLA5" and name.startswith("Marseille") and name[-1].isdigit())
            ):
                skipped[fcode] += 1
                continue

            fcodes[fcode] += 1
            sub = admin_1.get(f"{co}.{a1}", a1)
            data.append([int(gid), name, aname, co, sub, tz, int(pop)])

    for title, dct in [["KEPT", fcodes], ["SKIP", skipped]]:
        for k, v in sorted(dct.items(), key=lambda kv: kv[1], reverse=True):
            logger.debug(f"{title} {k:5}: {v}")

    logger.debug(f"Processed {i} lines, kept {len(data)}")
    return data


def load_admin1(txt):
    data = {}
    for line in txt.splitlines():
        co_sub, name, *_ = line.split("\t")
        data[co_sub] = name

    return data


def fetch_admin_1():
    filename = HERE_DIR / "admin1CodesASCII.txt"
    if filename.exists():
        txt = filename.read_text()
    else:
        txt = utils.fetch(GEONAMES_ADMIN1_URL).decode()
        filename.write_text(txt)

    return load_admin1(txt)
