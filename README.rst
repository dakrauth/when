=========
when 🌐🕐
=========

.. image:: https://github.com/dakrauth/when/actions/workflows/test.yml/badge.svg
    :alt: Tests
    :target: https://github.com/dakrauth/when

.. image:: https://codecov.io/gh/dakrauth/when/branch/main/graph/badge.svg
    :alt: Coverage
    :target: https://codecov.io/gh/dakrauth/when

.. image:: https://img.shields.io/pypi/v/when.svg
    :alt: PyPI Version
    :target: https://pypi.python.org/pypi/when

Scenario
--------

Your favorite sporting event, concert, performance, conference, or symposium is happening
in Ulan Bator and all you know is the time of event relative to the city or time zone. 
So what time is that for you in your local time? What time did it or will it occur at some
other time? What about for your friends in other locations around the world?

``when`` can not only download a GeoNames_ cities database for referencing source or target locations
by city name, but also uses all IANA time zone info, as well as most common time zone aliases (i.e.: 
``EST`` / ``EDT`` / ``US/Eastern`` / ``America/New_York``). 

Additional features include:

* List common holidays for a given country and/or year (US or configurable)
* Show dates for full moons
* Extensive configuration options for results

Installation
============

Install from PyPI:

.. code:: bash

    $ pip install when

or using pipx_:

.. code:: bash

    $ pipx install when

or:

.. code:: bash

    $ pipx install git+https://github.com/dakrauth/when.git

.. note::

    Once installed, if you wish to utilize ``when``'s full capabilities, you should
    install the GeoNames cities database as describe next.



Database installation
---------------------

To access city names, you need to install the cities database after installing the ``when`` application:

.. code:: bash

    when --db [options]

Where ``options`` are:

* ``--db-size``: You can specify a database down size by using one of the following:

    - ``sm`` - cities with population > 15000 or country capitals
    - ``md`` - cities with population > 5000 or seat of first-order admin division, i.e. US state
    - ``lg`` - cities with population > 1000 or seat of third order admin division
    - ``xl`` - cities with population > 500 or seat of fourth-order admin division

* ``--db-pop``: Filter non-admin division seats providing a minimum city population size
* ``--db-force``



Database Usage
~~~~~~~~~~~~~~

* Search: ``--db-search``

    Once installed, you can search the database:

    .. code:: bash

        $ when --db-search New York
        5106292, West New York, West New York, US, New Jersey, America/New_York
        5128581, New York City, New York City, US, New York, America/New_York

* Aliases: ``--db-alias``
    
    You can add aliases for easier search. In the example directly above, we see that New York City has
    a GeoNames ID of 5128581. Pass that to the ``--db-alias`` option along with another name that
    you would like to use:

    .. code:: bash

        $ when --db-alias 5128581 NYC
        $ when --source NYC
        2023-07-06 07:58:33-0400 (EDT, America/New_York) 187d27w (New York City, New York, US)[🌕 Full Moon]

* Alias listing: ``--db-aliases``


Examples
========

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
=======

Requires Python 3.10+ and just_ for convenience.

.. code:: bash

    $ git clone git@github.com:dakrauth/when.git
    $ cd when
    $ just  # or just help

Set up dev env:

.. code:: bash

    $ just init

Test, and code coverage:

.. code:: bash

    $ just test
    $ just cov

Only run a test matching matching a given substring:

.. code:: bash

    $ just test -k test_sometest

Interactive development:

.. code:: bash

    $ . ./venv/bin/activate
    $ when --help
    $ when --db

Further Reading
===============

`Time Zones Aren’t Offsets – Offsets Aren’t Time Zones`_

.. _pipx: https://pypa.github.io/pipx/
.. _just: https://github.com/casey/just
.. _`Time Zones Aren’t Offsets – Offsets Aren’t Time Zones`: https://spin.atomicobject.com/time-zones-offsets/)
.. _GeoNames: https://www.geonames.org/export/
