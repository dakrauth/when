import os
from pathlib import Path

import pytest
from when.db import client
from when.db import make
from when.core import When
from when.config import Settings

TEST_DIR = Path(__file__).parent
DATA_DIR = TEST_DIR / "data"


@pytest.fixture
def data_dir():
    return DATA_DIR


@pytest.fixture(scope="session", autouse=True)
def loader():
    def load(filename, binary=False):
        path = DATA_DIR / filename
        return path.read_bytes() if binary else path.read_text()

    return load


@pytest.fixture(scope="session", autouse=True)
def db(loader):
    db_path = Path("test_when.db")
    db_client = client.DB(db_path)
    admin1 = make.load_admin1(loader("admin1"))
    with open(DATA_DIR / "cities") as fp:
        data = make.process_geonames_txt(fp, 0, admin_1=admin1)
    db_client.create_db(data)
    yield db_client

    if not os.getenv("WHENSAVEDB"):
        db_path.unlink()


@pytest.fixture
def when(db):
    return When(Settings(name="NopeNopeNope"), db=db)
