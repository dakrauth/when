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

import pytest
import responses
from freezegun import freeze_time

# "NYC", 5128581
# "DC", 4140963


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
        assert utils.datetime_from_timestamp(inp) == datetime(2024, 7, 23, 12, 34, 56)

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
        blue = lunar.full_moon("2026.05")
        assert len(blue) == 2

        assert len(lunar.full_moon(2026)) == 13
        assert len(lunar.full_moon("2026")) == 13
        assert len(lunar.full_moon()) == 12

        with pytest.raises(exceptions.WhenError, match="Unknown arg for full_moon: foo"):
            lunar.full_moon("foo")

        with freeze_time("2026-06-02"):
            val = lunar.full_moon("next")
            assert val == [date(2026, 6, 29)]

            #breakpoint()
            val = lunar.full_moon("prev")
            assert val == [date(2026, 5, 31)]


class TestDB:
    def _args(self, **kwargs):
        kwargs = dict(
            db=False,
            db_search=None,
            db_xsearch=False,
            db_alias=False,
            db_aliases=False,
            db_force=False,
        ) | kwargs
        return SimpleNamespace(**kwargs)

    def test_aliases(self, capsys, db):
        args = self._args(db_alias="5128581", timestr=["nyc"])
        dbm.db_main(db, args)
        dbm.db_main(db, self._args(db_aliases=True))
        captured = capsys.readouterr().out
        assert "nyc: New York City" in captured

    def test_db_xsearch(self, capsys, db):
        dbm.db_main(db, self._args(db_xsearch=True, timestr=["Paris,FR"]))
        captured = capsys.readouterr().out.strip()
        assert len(captured.split("\n")) == 1
        assert captured == "2988507 Paris, Île-de-France, FR, Europe/Paris"

    def test_db_error(self):
        db = dbm.client.DB("doesnotexist")
        assert -1 == dbm.db_main(db, self._args(db_search=True, timestr=["foo"]))

    def test_db_create(self):
        assert False

    def test_parse_search(self, db):
        assert dbm.parse_search("a") == ["a", None, None]
        assert dbm.parse_search("a, b") == ["a", "b", None]
        assert dbm.parse_search("a, b,c") == ["a", "b", "c"]
        with pytest.raises(ValueError, match="Invalid city search expression: a,b,c,d"):
            dbm.parse_search("a,b,c,d")

    def test_db_search_singleton(self, db):
        result = db.search("maastricht")
        assert len(result) == 1
        assert result[0].tz == "Europe/Amsterdam"

    def test_db_search_multiple(self, db):
        result = db.search("paris")
        assert len(result) == 2
        assert set(r.tz for r in result) == {"Europe/Paris", "America/New_York"}

    def test_db_search_co(self, db):
        result = db.search("paris", "fr")
        assert len(result) == 1
        assert result[0].tz == "Europe/Paris"

    def test_main_db_search(self, capsys, when):
        argv = "--db-search maastricht".split()
        when_main(argv, when)
        captured = capsys.readouterr()
        assert captured.out == "2751283 Maastricht, Limburg, NL, Europe/Amsterdam\n"


class TestIANA:
    def test_iana_src_iana_tgt(self, when):
        result = when.convert("Jan 10, 2023 4:30am", sources="America/New_York", targets="Asia/Seoul")
        expect = datetime(2023, 1, 10, 18, 30, tzinfo=gettz("Asia/Seoul"))
        assert len(result) == 1
        assert result[0].dt == expect


class TestJSON:
    def test_json_output(self, loader, when):
        result = json.loads(when.as_json("Jan 19, 2024 22:00", sources="Lahaina", targets="Seoul"))
        expected = json.loads(loader("json"))
        assert result == expected


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

    @pytest.mark.parametrize("args,exp", [
        (["-h"], "Use -v option for details"),
        (["--config"], "[calendar]"),
        (["--holidays", "US"], "Halloween"),
        (["--prefix"], str(Path(exceptions.__file__).parent)),
        (["--tz-alias", "EST"], "Eastern Standard Time"),
        (["--fullmoon", "2026.05"], "2026-05-01\n2026-05-31")
    ])
    def test_simple_actions(self, capsys, args, exp):
        when_main(args)
        out = capsys.readouterr().out
        assert exp in out

class TestHolidays:
    def test_holidays(self, capsys, loader):
        expected_holidays = loader("holidays").splitlines()
        core.holidays(Settings(), co="US", ts="2023")
        lines = capsys.readouterr().out.splitlines()
        for i, line in enumerate(lines):
            expect = expected_holidays[i]
            m = re.match(expect, line)
            assert m is not None
            assert m.end() == len(line)


class TestSettings:
    def test_settings(self, data_dir):
        name = "when_rc_toml"
        s = Settings(dirs=[data_dir], name=name)
        assert s.read_from == [data_dir / name]

        text = s.write_text()
        assert "[foo]\n" in text
        assert 'bar = "baz"' in text


class TestMisc:
    def test_base_import(self):
        from when import when as xxx
        assert isinstance(xxx, When)

    @pytest.mark.parametrize("spec,exp", [
        ("%!z", "Pacific/Honolulu"),
        ("%!Z", ", Pacific/Honolulu"),
        ("%!c", "Lāhaina (Lahaina), Hawaii, US, Pacific/Honolulu"),
        ("%C", "20"),
        ("%D", "07/29/24"),
        ("%e", "29"),
        ("%F", "2024-07-29"),
        ("%g", "24"),
        ("%G", "2024"),
        ("%h", "Jul"),
        ("%n", "\n"),
        ("%r", "10:00:00 AM"),
        ("%R", "10:00"),
        ("%t", "\t"),
        ("%T", "10:00:00"),
        ("%u", "1"),
        ("%V", "31"),
    ])
    def test_formatting(self, when, spec, exp):
        res = when.convert("July 29, 2024 10am", targets=["Lahaina"])[0]
        fmt = core.Formatter(when.settings, spec)
        val = fmt(res)
        assert val == exp, f"{spec} bad, {val} != {exp}"

