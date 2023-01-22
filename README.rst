when 🌐🕐
=========

.. image:: https://github.com/dakrauth/when/actions/workflows/test.yml/badge.svg
    :target: https://github.com/dakrauth/when


Usage
-----

To access city names, you must install the cities database, downloaded from 
http://download.geonames.org/export/dump/citiesXXX.zip - depending upon where you specify the
``--size [500|1000|5000|15000]`` or ``--pop POP`` option(s).

.. code:: bash

    $ when --help
    usage: when [-h] [-s SOURCE] [-t TARGET] [-f FORMAT] [--all] [--holidays HOLIDAYS] [-v] [-V] [--pdb] [--db] [--search SEARCH] [--alias ALIAS] [--size SIZE]
                [--pop POP]
                [timestamp ...]

    Convert times to and from time zones or cities

    positional arguments:
      timestamp             Timestamp to parse, defaults to local time

    options:
      -h, --help            show this help message and exit
      -s SOURCE, --source SOURCE
                            Timezone / city to convert the timestamp from, defaulting to local time
      -t TARGET, --target TARGET
                            Timezone / city to convert the timestamp to (globbing patterns allowed, can be comma delimited), defaulting to local time
      -f FORMAT, --format FORMAT
                            Output formatting. Additionaly predefined formats by name are rfc2822, iso, . Default: %Y-%m-%d %H:%M:%S%z (%Z) %jd%Ww %C %O, where %K
                            is timezone long name
      --all                 Show times in all common timezones
      --holidays HOLIDAYS   Show holidays for given country code.
      -v, --verbosity       Verbosity (-v, -vv, etc)
      -V, --version         show program's version number and exit
      --pdb
      --db                  Togge database mode, used with --search, --alias, --size, and --pop
      --search SEARCH       Search database for the given city (used with --db)
      --alias ALIAS         (Used with --db) Create a new alias from the city id
      --size SIZE           (Used with --db) Geonames file size. Can be one of 1000, 500, 15000, 5000.
      --pop POP             (Used with --db) City population minimum.

    Examples:
    =========

    # Show the time in a given source city or time zone

    when --source New York City
    when --source America/New_York

    # Show the specified time at a given source in local time

    when --source Paris,FR 21:35

    # Show the specified time at a given source in the target locale's time

    when --target Bangkok --source Seattle

Example
-------

.. code:: bash

    $ when
    2023-02-11 17:43:44+0900 (KST) 042d06w  [🌖 Waning Gibbous]

    $ when --source CST
    2023-02-11 02:44:22-0600 (Central Standard Time) 042d06w  [🌖 Waning Gibbous]
    2023-02-11 12:44:22+0400 (Caucasus Standard Time) 042d06w  [🌖 Waning Gibbous]
    2023-02-11 16:44:22+0800 (China Standard Time) 042d06w  [🌖 Waning Gibbous]
    2023-02-11 03:44:22-0500 (Cuba Standard Time) 042d06w  [🌖 Waning Gibbous]

    $ when --source Paris
    2023-02-11 09:45:11+0100 (Europe/Paris) 042d06w  (Villeparisis, FR, Île-de-France) [🌖 Waning Gibbous]
    2023-02-11 09:45:11+0100 (Europe/Paris) 042d06w  (Paris, FR, Île-de-France) [🌖 Waning Gibbous]
    2023-02-11 09:45:11+0100 (Europe/Paris) 042d06w  (Cormeilles-en-Parisis, FR, Île-de-France) [🌖 Waning Gibbous]
    2023-02-11 03:45:11-0500 (America/Port-au-Prince) 042d06w  (Fond Parisien, HT, Ouest) [🌖 Waning Gibbous]
    2023-02-11 02:45:11-0600 (America/Chicago) 042d06w  (Paris, US, Texas) [🌖 Waning Gibbous]

    $ when --source "San Francisco,US" --target America/New_York Mar 7 1945 7:00pm
    1945-03-07 22:00:00-0400 (America/New_York) 066d10w  [🌘 Waning Crescent]
    1945-03-07 22:00:00-0400 (America/New_York) 066d10w  [🌘 Waning Crescent]


Develop
-------

Requirements Python 3.7+

.. code:: bash

    $ git clone git@github.com:dakrauth/when.git
    $ cd when
    $ python -mvenv venv
    $ . venv/bin/activate
    $ pip install .
    $ when --help
    $ when --db
    $ pip install tox
    $ tox


