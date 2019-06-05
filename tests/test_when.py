import os, sys, time
from datetime import datetime
from unittest.mock import patch
import pytest
from dateutil.tz import gettz

from when.when import When
from when import utils
from when.__main__ import main as when_main


def test_find_city():
    assert utils.find_city('maastricht') == ['Europe/Amsterdam']


def test_generate_cities_pyzip():
    data = 'city_name1\txq\tAmerica/New_York\ncity_name2\txz\tUS/Hawaii'
    utils.generate_cities_pyzip(data, 'test_cities.zip')
    fname = 'test_cities.zip'
    assert utils.find_city('city_name1', fname) == ['America/New_York']
    assert utils.find_city('city_name2', fname) == ['US/Hawaii']
    os.unlink(fname)
    assert not os.path.exists(fname)


def test_when():
    wh = When()
    result = wh.convert('Feb 24 2pm America/New_York')
    expect = datetime(2019, 2, 24, 14, tzinfo=gettz('America/New_York'))
    assert result [0] == expect


def test_main(capsys):
    argv = 'when Feb 24 2pm America/New_York'.split()
    with patch.object(sys, 'argv', argv):
        when_main()
        captured = capsys.readouterr()
        output = captured.out
        if 'UTC' in output:
            assert '2019-02-24 19:00:00+0000 (UTC) 055d07w Etc/UTC\n' == output
        else:
            assert '2019-02-24 14:00:00-0500 (EST) 055d07w America/New_York\n' == output

    argv = 'when -z CST Feb 24 2pm America/New_York'.split()
    with patch.object(sys, 'argv', argv):
        when_main()
        captured = capsys.readouterr()
        output = captured.out
        if 'UTC' in output:
            assert '2019-02-24 18:00:00-0600 (UTC) 055d07w Etc/UTC\n' == output
        else:
            assert '2019-02-24 13:00:00-0600 (CST) 055d07w US/Central\n' == output
