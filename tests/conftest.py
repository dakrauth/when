from pathlib import Path
import pytest
from when.db import client
from when.db import make
from when.core import When

test_dir = Path(__file__).parent


@pytest.fixture(scope="session", autouse=True)
def db():
    db_client = client.DB(":memory:")
    admin1 = make.load_admin1("US.HI\tHawaii\tHawaii\t5855797\nKR.11\tSeoul\tSeoul\t1835847")
    data = make.process_geonames_txt(test_dir / "citiesTest.txt", 0, admin_1=admin1)

    db_client.create_db(data)
    return db_client


@pytest.fixture
def when(db):
    return When(db=db)
