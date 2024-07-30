when 🌐🕐
=========

.. image:: https://github.com/dakrauth/when/actions/workflows/test.yml/badge.svg
    :target: https://github.com/dakrauth/when

Scenario
--------

Your favorite sporting event, concert, performance, conference, or symposium is happening
in Ulan Bator and all you know is the time of event is relative to the location city or time zone. 
But wait! You need to know when that occurs relative to you while traveling to Seoul or Paris.

Installation
------------

Install from PyPI::

    $ pip install when

or using pipx_::

    $ pipx install when

or::

    $ pipx install git+https://github.com/dakrauth/when.git

.. _pipx: https://pypa.github.io/pipx/

To access city names, you must install the cities database::

    when --db [options]

For ``options``:

You can specify minimum city size by adding ``--size SIZE``, where *SIZE* can be one of:

- ``15000`` - cities with population > 15000 or country capitals
- ``5000`` - cities with population > 5000 or seat of first-order admin division, i.e. US state
- ``1000`` - cities with population > 1000 or seat of third order admin division
- ``500`` - cities with population > 500 or seat of fourth-order admin division

Additionally, you can filter non-admin division seats using ``--pop POP``.

The appropriate GeoNames Gazetteer is downloaded and a Sqlite database generated.

Usage
-----

Once installed, you can search the database::

    $ when --db-search New York
    5106292, West New York, West New York, US, New Jersey, America/New_York
    5128581, New York City, New York City, US, New York, America/New_York


Additionally, you can add aliases. In the example directly above, we see that New York City has
a GeoNames ID of 5128581. Pass that to the ``--db-alias`` option along with another name that
you would like to use::

    $ when --db-alias 5128581 NYC
    $ when --source NYC
    2023-07-06 07:58:33-0400 (EDT, America/New_York) 187d27w (New York City, New York, US)[🌕 Full Moon]


Example
-------

For the sake of clarity, in the following examples I am in Seoul, Korea.

.. code:: bash

    $ when
    2023-07-06 20:58:02+0900 (KST, Asia/Seoul) 187d27w [🌕 Full Moon]

    $ when --source CST
    2023-07-06 06:58:54-0500 (CDT, Central Standard Time) 187d27w [🌕 Full Moon]
    2023-07-06 15:58:54+0400 (+04, Caucasus Standard Time) 187d27w [🌕 Full Moon]
    2023-07-06 19:58:54+0800 (CST, China Standard Time) 187d27w [🌕 Full Moon]
    2023-07-06 07:58:54-0400 (CDT, Cuba Standard Time) 187d27w [🌕 Full Moon]

    $ when --source Paris
    2023-07-06 13:59:25+0200 (CEST, Europe/Paris) 187d27w (Villeparisis, Île-de-France, FR)[🌕 Full Moon]
    2023-07-06 13:59:25+0200 (CEST, Europe/Paris) 187d27w (Paris, Île-de-France, FR)[🌕 Full Moon]
    2023-07-06 13:59:25+0200 (CEST, Europe/Paris) 187d27w (Cormeilles-en-Parisis, Île-de-France, FR)[🌕 Full Moon]
    2023-07-06 07:59:25-0400 (EDT, America/Port-au-Prince) 187d27w (Fond Parisien, Ouest, HT)[🌕 Full Moon]
    2023-07-06 06:59:25-0500 (CDT, America/Chicago) 187d27w (Paris, Texas, US)[🌕 Full Moon]

    $ when --source "San Francisco,US" --target America/New_York Mar 7 1945 7:00pm
    1945-03-07 22:00:00-0400 (EWT, America/New_York) 066d10w [🌘 Waning Crescent]
    1945-03-07 22:00:00-0400 (EWT, America/New_York) 066d10w [🌘 Waning Crescent]


Develop
-------

Requirements Python 3.10+. Also, [just](https://github.com/casey/just) for convenience.

.. code:: bash

    $ git clone git@github.com:dakrauth/when.git
    $ cd when
    $ just
    $ just venv
    $ just test
    $ . ./venv/bin/activate
    $ when --help
    $ when --db

Further Reading
---------------

[Time Zones Aren’t Offsets – Offsets Aren’t Time Zones
](https://spin.atomicobject.com/time-zones-offsets/)
