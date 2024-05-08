import os
from pathlib import Path

import pytest
from when.db import client
from when.db import make
from when.core import When

test_dir = Path(__file__).parent

ADMIN_1 = """\
US.HI\tHawaii\tHawaii\t5855797
US.NY\tNew York\tNew York\t5128581
US.ME\tMaine\tMaine\t4974617
US.DC\tWashington, D.C.\tWashington, D.C\t4140963
KR.11\tSeoul\tSeoul\t1835847
NL.05\tLimburg\tLimburg\t2751283
FR.11\tÎle-de-France\tÎle-de-France\t2988507"""


@pytest.fixture(scope="session", autouse=True)
def db():
    db_path = Path("test_when.db")
    db_client = client.DB(db_path)
    admin1 = make.load_admin1(ADMIN_1)
    data = make.process_geonames_txt(test_dir / "citiesTest.txt", 0, admin_1=admin1)
    db_client.create_db(data)
    yield db_client

    if not os.getenv("WHENSAVEDB"):
        db_path.unlink()


@pytest.fixture
def when(db):
    return When(db=db)
