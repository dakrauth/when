import os
import re
import math
import time
import json
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime, timedelta, date
from dateutil.tz import gettz

from when.cli import main as when_main
from when.timezones import zones
from when import utils, lunar, core, exceptions
from when import db as dbm
from when.config import Settings
from when.core import When
from when.db import make

import pytest
import responses
from freezegun import freeze_time

# "NYC", 5128581
# "DC", 4140963
HERE_DIR = Path(__file__).parent


def assert_nested_items_are_equal(o1, o2):
    assert type(o1) == type(o2)

    if isinstance(o1, float):
        assert math.isclose(o1, o2)

    elif isinstance(o1, dict):
        o1_keys = sorted(o1.keys())
        assert (len(o1) == len(o2)) and (o1_keys == sorted(o2.keys()))

        for key in o1_keys:
            o1v = o1[key]
            o2v = o2[key]
            assert_nested_items_are_equal(o1v, o2v)

    elif isinstance (o1, (list, tuple)):
        assert len(o1) == len(o2)

        for a, b in zip(o1, o2):
            assert_nested_items_are_equal(a, b)

    assert o1 == o2


class TestZones:
    def test_tz_alias_offset(self):
        z = zones.get("utc+8:30")
        assert z and z[0][1] == "UTC+8:30"

        z = zones.get("UTC+8:30")
        assert z and z[0][1] == "UTC+8:30"

    def test_abbr_src_abbr_tgt(self, when):
        result = when.convert("Jan 10, 2023 4:30am", sources="EST", targets="KST")
        expect = datetime(2023, 1, 10, 18, 30, tzinfo=gettz("Asia/Seoul"))
        assert result[0].dt == expect

    def test_zones_get(self):
        result = zones.get("Eastern")
        assert len(result) == 1
        assert result[0][1] == "Eastern Standard Time"
        assert "US/Eastern" in str(result[0][0])


class TestUtils:
    def test_format_timedelta(self):
        td = timedelta(weeks=1, days=1, hours=1, minutes=1, seconds=1)
        assert utils.format_timedelta(td) == "1 week, 1 day, 1 hour, 1 minute, 1 second"
        assert utils.format_timedelta(td, short=True) == "1w1d1h1m1s"

        td = timedelta(days=2, hours=2, minutes=2, seconds=2)
        assert utils.format_timedelta(td) == "2 days, 2 hours, 2 minutes, 2 seconds"
        assert utils.format_timedelta(td, short=True) == "2d2h2m2s"

    def test_parse_timedelta_offset(self):
        td = timedelta(days=1, hours=1, minutes=1, seconds=1)
        assert utils.parse_timedelta_offset("1d1h1m1s") == td

        with pytest.raises(exceptions.WhenError, match="Invalid offset"):
            utils.parse_timedelta_offset("1")

        with pytest.raises(exceptions.WhenError, match="Unrecognized offset value: foo"):
            utils.parse_timedelta_offset("foo")

        assert utils.parse_timedelta_offset("-1d") == timedelta(days=-1)
        assert utils.parse_timedelta_offset("~1w") == timedelta(weeks=-1)

    @pytest.mark.parametrize("inp", ["1721774096", 1721774096, "1721774096000", 1721774096000])
    def test_datetime_from_timestamp(self, inp):
        with freeze_time("2024-08-01", tz_offset=0):
            assert utils.datetime_from_timestamp(inp) == datetime(2024, 7, 23, 22, 34, 56)

    def test_datetime_from_timestamp_error(self):
        with pytest.raises(exceptions.WhenError, match="Invalid timestamp format: nan"):
            utils.datetime_from_timestamp(math.nan)

    def test_get_timezone_db_name(self):
        assert utils.get_timezone_db_name(None) == None
        assert utils.get_timezone_db_name("/some/path/zoneinfo/foo/bar") == "foo/bar"

    def test_fetch(self):
        with responses.RequestsMock() as rsp:
            rsp.add(responses.GET, "https://foo.com/bar/", body=b"asdf", status=200)
            assert utils.fetch("https://foo.com/bar/") == b"asdf"

            url = "https://foo.com/baz/"
            rsp.add(responses.GET, url, status=404)
            with pytest.raises(exceptions.WhenError, match=f"404: {url}"):
                utils.fetch(url)


class TestLunar:
    def test_full_moon_iterator(self):
        it = lunar.full_moon_iterator(datetime(2024, 6, 1))
        assert next(it) == date(2024, 6, 21)

    def test_full_moon(self):
        blue = lunar.full_moon("2026-05")
        assert len(blue) == 2

        assert len(lunar.full_moon(2026)) == 13
        assert len(lunar.full_moon("2026")) == 13
        assert len(lunar.full_moon()) == 12

        with pytest.raises(exceptions.WhenError, match="Unknown arg for full_moon: foo"):
            lunar.full_moon("foo")

        with freeze_time("2026-06-02"):
            val = lunar.full_moon("next")
            assert val == [date(2026, 6, 29)]

            # breakpoint()
            val = lunar.full_moon("prev")
            assert val == [date(2026, 5, 31)]


class TestDB:
    def _args(self, **kwargs):
        kwargs = (
            dict(
                db_search=None,
                db_size=None,
                db_alias=False,
                db_aliases=False,
                db_force=False,
                db_exact=False,
                db_pop=10_000,
            )
            | kwargs
        )
        return SimpleNamespace(**kwargs)

    def test_aliases(self, capsys, db):
        args = self._args(db_alias="5128581", timestr=["nyc"])
        dbm.db_main(db, args)
        dbm.db_main(db, self._args(db_aliases=True))
        captured = capsys.readouterr().out
        assert "nyc: New York City" in captured

    def test_db_exact_search(self, capsys, db):
        dbm.db_main(db, self._args(exact=True, db_search=True, timestr=["Paris,FR"]))
        captured = capsys.readouterr().out.strip()
        assert len(captured.split("\n")) == 1
        assert captured == "2988507 Paris, Île-de-France, FR, Europe/Paris"

    def test_db_error(self):
        db = dbm.client.DB("doesnotexist")
        assert -1 == dbm.db_main(db, self._args(db_search=True, timestr=["foo"]))

    def test_db_create(self, loader):
        db = dbm.client.DB(HERE_DIR / "test_create.db")
        files = [db.filename, HERE_DIR / "cities500.txt", HERE_DIR / "admin1CodesASCII.txt"]
        [f.unlink(True) for f in files]

        try:
            args = self._args(db_size=500, db_pop=10_000, db_force=True)
            with responses.RequestsMock() as mock:
                rsp_city = mock.add(
                    responses.GET,
                    make.GEONAMES_CITIES_URL_FMT.format(500),
                    body=loader("cities500.zip", binary=True),
                    status=200,
                )
                rsp_admin1 = mock.add(
                    responses.GET,
                    make.GEONAMES_ADMIN1_URL,
                    body=loader("admin1", binary=True),
                    status=200,
                )

                dbm.db_main(db, args)
                assert 2 == len(db.search("Paris"))
        finally:
            [f.unlink(True) for f in files]

    def test_fetch_cities(self, loader):
        size = 500
        expect = HERE_DIR / f"cities{size}.txt"
        expect.unlink(True)
        url = make.GEONAMES_CITIES_URL_FMT.format(size)
        with responses.RequestsMock() as mock:
            body = loader("cities500.zip", binary=True)
            rsp = mock.add(responses.GET, url, body=body, status=200)
            fn = make.fetch_cities(size, HERE_DIR)
            assert fn == expect
            assert rsp.call_count == 1

            fn = make.fetch_cities(size, HERE_DIR)
            assert fn == expect
            assert rsp.call_count == 1

            with expect.open() as fp:
                data = make.process_geonames_txt(fp, 10_000)

            assert len(data) == 7

        expect.unlink(True)

    def test_fetch_admin_1(self, loader):
        expect = HERE_DIR / "admin1CodesASCII.txt"
        expect.unlink(True)
        url = make.GEONAMES_ADMIN1_URL
        with responses.RequestsMock() as mock:
            rsp = mock.add(responses.GET, url, body=loader("admin1", binary=True), status=200)

            data = make.fetch_admin_1(HERE_DIR)
            assert rsp.call_count == 1
            assert expect.exists()
            assert len(data) == 7

            data = make.fetch_admin_1(HERE_DIR)
            assert rsp.call_count == 1
            assert len(data) == 7

        expect.unlink(True)

    def test_parse_search(self, db):
        assert db.parse_search("a") == ["A", None, None]
        assert db.parse_search("a, b") == ["A", None, "B"]
        assert db.parse_search("a, b,c") == ["A", "B", "C"]
        with pytest.raises(exceptions.DBError, match="Invalid city search expression: a,b,c,d"):
            db.parse_search("a,b,c,d")

    def test_db_search_singleton(self, db):
        result = db.search("maastricht")
        assert len(result) == 1
        assert result[0].tz == "Europe/Amsterdam"

    def test_db_search_multiple(self, db):
        result = db.search("paris")
        assert len(result) == 2
        assert set(r.tz for r in result) == {"Europe/Paris", "America/New_York"}

    def test_db_search_co(self, db):
        result = db.search("paris,fr")
        assert len(result) == 1
        assert result[0].tz == "Europe/Paris"

    def test_main_db_search(self, capsys, when):
        argv = "--search maastricht".split()
        when_main(argv, when)
        captured = capsys.readouterr()
        assert captured.out == "2751283 Maastricht, Limburg, NL, Europe/Amsterdam\n"


class TestIANA:
    def test_iana_src_iana_tgt(self, when):
        result = when.convert(
            "Jan 10, 2023 4:30am", sources="America/New_York", targets="Asia/Seoul"
        )
        expect = datetime(2023, 1, 10, 18, 30, tzinfo=gettz("Asia/Seoul"))
        assert len(result) == 1
        assert result[0].dt == expect


class TestJSON:
    def test_json_output(self, loader, when):
        result = json.loads(when.as_json("Jan 19, 2024 22:00", sources="Lahaina", targets="Seoul"))
        expected = json.loads(loader("json"))
        assert_nested_items_are_equal(result, expected)


class TestCity:
    def test_string(self):
        city = dbm.client.City(1, "foo", "foo", "foobar", "FO", "UTC")
        assert str(city) == "foo, foobar, FO, UTC"
        assert f"{city:N}" == "foo"

        city = dbm.client.City(1, "føø", "foo", "foobar", "FO", "UTC")
        assert str(city) == "føø (foo), foobar, FO, UTC"

        assert f"{city}" == str(city)
        assert f"{city:i,n,a,s,c,z,N}" == "1,føø,foo,foobar,FO,UTC,føø (foo)"
 
    def test_city_src_city_tgt(self, when):
        result = when.convert("Jan 10, 2023 4:30am", sources="New York City", targets="Seoul")
        expect = datetime(2023, 1, 10, 18, 30, tzinfo=gettz("Asia/Seoul"))
        assert len(result) == 1
        assert result[0].dt == expect

    def test_iso_formatter(self, when):
        fmt = core.Formatter(when.settings, "iso")
        result = when.convert("Jan 10, 2023 4:30am", sources="New York City", targets="Seoul")
        assert len(result) == 1
        assert fmt(result[0]).startswith("2023-01-10T18:30:00+0900")

    def test_rfc_formatter(self, when):
        fmt = core.Formatter(when.settings, "rfc2822")
        result = when.convert("Jan 10, 2023 4:30am", sources="New York City", targets="Seoul")
        assert len(result) == 1
        value = fmt(result[0])
        assert value.startswith("Tue, 10 Jan 2023 18:30:00 +0900")


class TestMain:
    def test_main_tz(self, capsys, when):
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

    def test_logging(self, capsys, data_dir):
        argv = ["-vv"]
        when = When(Settings(dirs=[data_dir], name="when_rc_toml"))
        when_main(argv, when)
        assert "when_rc_toml" in capsys.readouterr().err


    def test_source_target_no_timestr(self, capsys, when):
        with freeze_time("2025-02-03 22:00", tz_offset=0):
            argv = "--source utc --target paris,maine,us --exact".split()
            when_main(argv, when)
            out = capsys.readouterr().out
            assert len(out.splitlines()) == 1
            assert out.startswith("2025-02-03 17:00")
            assert "Paris, Maine, US" in out

    @pytest.mark.parametrize(
        "args,exp",
        [
            (["-h"], "Use -v option for details"),
            (["--config"], "[calendar]"),
            (["--holidays", "US"], "Halloween"),
            (["--prefix"], str(Path(exceptions.__file__).parent)),
            (["--tz-alias", "EST"], "Eastern Standard Time"),
            (["--fullmoon", "2026-05"], "2026-05-01\n2026-05-31"),
        ],
    )
    def test_simple_actions(self, capsys, args, exp):
        when_main(args)
        out = capsys.readouterr().out
        assert exp in out

    def test_offset(self, capsys, when):
        args = ["--offset", "-1d", "--target", "xxx"]
        rc = when_main(args, when)
        err = capsys.readouterr().err
        assert "Could not find matching resource: xxx" in err
        assert rc == 1
        assert args[1] == "~1d"

    def test_group(self, capsys, when):
        argv = "--target paris,maine,us --target paris,fr --exact --source maastricht --group".split()
        argv.append("Feb 3, 2025 2pm")
        when_main(argv, when)
        out = capsys.readouterr().out
        lines = out.splitlines()
        assert len(lines) == 4
        assert lines[0].startswith("2025-02-03 08:00")
        assert lines[1].startswith(" ↳ @")
        assert lines[2].startswith("2025-02-03 14:00")
        assert lines[3].startswith(" ↳ @")

class TestMisc:
    def test_settings(self, data_dir):
        name = "when_rc_toml"
        s = Settings(dirs=[data_dir], name=name)
        assert s.read_from == [data_dir / name]

        text = s.write_text()
        assert "[foo]\n" in text
        assert 'bar = "baz"' in text

    def test_holidays(self, capsys, loader):
        expected_holidays = loader("holidays").splitlines()
        core.holidays(Settings(), co="US", ts="2023")
        lines = capsys.readouterr().out.splitlines()
        for i, line in enumerate(lines):
            expect = expected_holidays[i]
            m = re.match(expect, line)
            assert m is not None
            assert m.end() == len(line)

    def test_base_import(self):
        from when import when as xxx

        assert isinstance(xxx, When)

    @pytest.mark.parametrize(
        "spec,exp",
        [
            ("%!z", "Pacific/Honolulu"),
            ("%!Z", ", Pacific/Honolulu"),
            ("%!c", "Lāhaina (Lahaina), Hawaii, US, Pacific/Honolulu"),
            ("%C", "20"),
            ("%D", "07/31/24"),
            ("%e", "31"),
            ("%F", "2024-07-31"),
            ("%g", "24"),
            ("%G", "2024"),
            ("%h", "Jul"),
            ("%n", "\n"),
            ("%r", "02:00:00 PM"),
            ("%R", "14:00"),
            ("%t", "\t"),
            ("%T", "14:00:00"),
            ("%u", "3"),
            ("%V", "31"),
        ],
    )
    def test_formatting(self, when, spec, exp):
        res = when.convert("2024-08-01T00:00", sources=["UTC"], targets=["Lahaina"], exact=True)[0]
        fmt = core.Formatter(when.settings, spec)
        val = fmt(res)
        assert val == exp, f"{spec} bad, {val} != {exp}"
