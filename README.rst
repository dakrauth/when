when 🌐🕐
=========

.. image:: https://github.com/dakrauth/when/actions/workflows/test.yml/badge.svg
    :target: https://github.com/dakrauth/when


Usage
-----

.. code:: bash

    $ when --help
    usage: when [-h] [-z TZSTR] [-f FORMATTING] [-c] [--pdb] [--all] [-v] [-V]
                [timestamp [timestamp ...]]

    positional arguments:
      timestamp             Optional timestamp to parse, defaults to UTC now

    optional arguments:
      -h, --help            show this help message and exit
      -z TZSTR, --zone TZSTR
                            Timezone to convert the timestamp to (globbing
                            patterns allowed)
      -f FORMATTING, --format FORMATTING
                            Output formatting. Default: %Y-%m-%d %H:%M:%S%z (%Z)
                            %jd%Ww %K, where %K is timezone long name
      -c, --city            Interpret timestamp as city name
      --all                 Show times in all common timezones
      -v, --verbose         Verbosity (-v, -vv, etc)
      -V, --version         show program's version number and exit

Example
-------

.. code:: bash

    $ when
    2019-02-23 18:07:58-0500 (EST) 054d07w America/New_York

    $ when -z CST
    2019-02-23 17:07:58-0600 (CST) 054d07w US/Central

    $ when -z PST,CET
    2019-02-23 15:07:58-0800 (PST) 054d07w US/Pacific
    2019-02-24 00:07:58+0100 (CET) 055d07w CET

    $ when -c Paris
    2019-02-24 00:07:59+0100 (CET) 055d07w Europe/Paris
    2019-02-23 17:07:59-0600 (CST) 054d07w America/Chicago

    $ when Mar 7 1945 7:00pm PST
    1945-03-07 22:53:00-0400 (EWT) 066d10w America/New_York

    $ when Jun 7
    2019-06-07 00:00:00-0400 (EDT) 158d22w America/New_York

    $ when -z US/Hawaii Jun 7
    2019-06-06 18:00:00-1000 (HST) 157d22w US/Hawaii

    $ when -z "US/*" Feb 29 2020 6pm
    2020-02-29 14:00:00-0900 (AKST) 060d08w US/Alaska
    2020-02-29 13:00:00-1000 (HST) 060d08w US/Aleutian
    2020-02-29 16:00:00-0700 (MST) 060d08w US/Arizona
    2020-02-29 17:00:00-0600 (CST) 060d08w US/Central
    2020-02-29 18:00:00-0500 (EST) 060d08w US/East-Indiana
    2020-02-29 18:00:00-0500 (EST) 060d08w US/Eastern
    2020-02-29 13:00:00-1000 (HST) 060d08w US/Hawaii
    2020-02-29 17:00:00-0600 (CST) 060d08w US/Indiana-Starke
    2020-02-29 18:00:00-0500 (EST) 060d08w US/Michigan
    2020-02-29 16:00:00-0700 (MST) 060d08w US/Mountain
    2020-02-29 15:00:00-0800 (PST) 060d08w US/Pacific
    2020-02-29 12:00:00-1100 (SST) 060d08w US/Samoa

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
    $ pip install tox
    $ tox


