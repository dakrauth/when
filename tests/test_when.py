import os
import re
import time
import json
from datetime import datetime
from dateutil.tz import gettz

from when.core import Formatter
from when.cli import main as when_main
from when.core import holidays
from when.timezones import zones

# "NYC", 5128581
# "DC", 4140963


def test_db_search_singleton(db):
    result = db.search("maastricht")
    assert len(result) == 1
    assert result[0].tz == "Europe/Amsterdam"


def test_db_search_multiple(db):
    result = db.search("paris")
    assert len(result) == 2
    assert set(r.tz for r in result) == {"Europe/Paris", "America/New_York"}


def test_db_search_co(db):
    result = db.search("paris", "fr")
    assert len(result) == 1
    assert result[0].tz == "Europe/Paris"


def test_iana_src_iana_tgt(when):
    result = when.convert("Jan 10, 2023 4:30am", sources="America/New_York", targets="Asia/Seoul")
    expect = datetime(2023, 1, 10, 18, 30, tzinfo=gettz("Asia/Seoul"))
    assert len(result) == 1
    assert result[0].dt == expect


def test_json_output(when):
    result = json.loads(when.as_json("Jan 19, 2024 22:00", sources="Lahaina", targets="Seoul"))
    expected = json.loads(
        """[
      {
        "iso": "2024-01-20T17:00:00+09:00",
        "offset": null,
        "zone": {
          "name": "Asia/Seoul",
          "city": {
            "name": "Seoul",
            "ascii": "Seoul",
            "country": "KR",
            "tz": "Asia/Seoul",
            "subnational": "Seoul"
          },
          "utcoffset": [9, 0, 0]
        },
        "source": {
          "iso": "2024-01-19T22:00:00-10:00",
          "offset": null,
          "zone": {
            "name": "Pacific/Honolulu",
            "city": {
              "name": "Lāhaina",
              "ascii": "Lahaina",
              "country": "US",
              "tz": "Pacific/Honolulu",
              "subnational": "Hawaii"
            },
            "utcoffset": [-10, 0, 0]
          },
          "source": null
        }
      }
    ]"""
    )
    assert result == expected


def test_city_src_city_tgt(when):
    result = when.convert("Jan 10, 2023 4:30am", sources="New York City", targets="Seoul")
    expect = datetime(2023, 1, 10, 18, 30, tzinfo=gettz("Asia/Seoul"))
    assert len(result) == 1
    assert result[0].dt == expect


def test_iso_formatter(when):
    fmt = Formatter("iso")
    result = when.convert("Jan 10, 2023 4:30am", sources="New York City", targets="Seoul")
    assert len(result) == 1
    assert fmt(result[0]).startswith("2023-01-10T18:30:00+0900")


def test_rfc_formatter(when):
    fmt = Formatter("rfc2822")
    result = when.convert("Jan 10, 2023 4:30am", sources="New York City", targets="Seoul")
    assert len(result) == 1
    value = fmt(result[0])
    assert value.startswith("Tue, 10 Jan 2023 18:30:00 +0900")


def test_zones_get():
    result = zones.get("Eastern")
    assert len(result) == 1
    assert result[0][1] == "Eastern Standard Time"
    assert "US/Eastern" in str(result[0][0])


def test_abbr_src_abbr_tgt(when):
    result = when.convert("Jan 10, 2023 4:30am", sources="EST", targets="KST")
    expect = datetime(2023, 1, 10, 18, 30, tzinfo=gettz("Asia/Seoul"))
    assert result[0].dt == expect


def test_main_db_search(capsys, when):
    argv = "--db-search maastricht".split()
    when_main(argv, when)
    captured = capsys.readouterr()
    assert captured.out == "2751283 Maastricht, Limburg, NL, Europe/Amsterdam\n"


def test_main_tz(capsys, when):
    orig_tz = os.getenv("TZ", "")
    try:
        os.environ["TZ"] = "EST"
        time.tzset()
        argv = "--source America/New_York --target Seoul Jan 10, 2023 4:30am".split()
        when_main(argv, when)
        captured = capsys.readouterr()
        output = captured.out
        expect = "2023-01-10 18:30:00+0900 (KST, Asia/Seoul) 010d02w (Seoul, KR"
        assert output.startswith(expect)
    finally:
        os.environ["TZ"] = orig_tz
        time.tzset()


HOLIDAYS = [
    r"New Year's Day.....Sun, Jan 01 2023 \([+-]\d+ days\) \[🌓 First Quarter\]",
    r"MLK Day............Mon, Jan 16 2023 \([+-]\d+ days\) \[🌗 Last Quarter\]",
    r"Valentine's Day....Tue, Feb 14 2023 \([+-]\d+ days\) \[🌗 Last Quarter\]",
    r"Presidents' Day....Mon, Feb 20 2023 \([+-]\d+ days\) \[🌑 New Moon\]",
    r"Mardi Gras.........Tue, Feb 21 2023 \([+-]\d+ days\) \[🌑 New Moon\]",
    r"Ash Wednesday......Wed, Feb 22 2023 \([+-]\d+ days\) \[🌑 New Moon\]",
    r"St. Patrick's Day..Fri, Mar 17 2023 \([+-]\d+ days\) \[🌗 Last Quarter\]",
    r"Palm Sunday........Sun, Apr 02 2023 \([+-]\d+ days\) \[🌔 Waxing Gibbous\]",
    r"Good Friday........Fri, Apr 07 2023 \([+-]\d+ days\) \[🌕 Full Moon\]",
    r"Easter.............Sun, Apr 09 2023 \([+-]\d+ days\) \[🌖 Waning Gibbous\]",
    r"Mother's Day.......Sun, May 14 2023 \([+-]\d+ days\) \[🌗 Last Quarter\]",
    r"Memorial Day.......Mon, May 29 2023 \([+-]\d+ days\) \[🌓 First Quarter\]",
    r"Father's Day.......Sun, Jun 18 2023 \([+-]\d+ days\) \[🌑 New Moon\]",
    r"Juneteenth.........Mon, Jun 19 2023 \([+-]\d+ days\) \[🌑 New Moon\]",
    r"Independence Day...Tue, Jul 04 2023 \([+-]\d+ days\) \[🌕 Full Moon\]",
    r"Labor..............Mon, Sep 04 2023 \([+-]\d+ days\) \[🌖 Waning Gibbous\]",
    r"Columbus Day.......Mon, Oct 09 2023 \([+-]\d+ days\) \[🌗 Last Quarter\]",
    r"Halloween..........Tue, Oct 31 2023 \([+-]\d+ days\) \[🌕 Full Moon\]",
    r"Veterans Day.......Sat, Nov 11 2023 \([+-]\d+ days\) \[🌘 Waning Crescent\]",
    r"Thanksgiving.......Thu, Nov 23 2023 \([+-]\d+ days\) \[🌓 First Quarter\]",
    r"Christmas..........Mon, Dec 25 2023 \([+-]\d+ days\) \[🌔 Waxing Gibbous\]",
]


def test_holidays(capsys):
    holidays(co="US", ts="2023")
    lines = capsys.readouterr().out.splitlines()
    for i, line in enumerate(lines):
        expect = HOLIDAYS[i]
        m = re.match(expect, line)
        assert m is not None
        assert m.end() == len(line)
