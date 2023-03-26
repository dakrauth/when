when 🌐🕐
=========

.. image:: https://github.com/dakrauth/when/actions/workflows/test.yml/badge.svg
    :target: https://github.com/dakrauth/when

Installation
------------

Install from PyPI::

    $ pip install when

or using pipx_::

    $ pipx install when

or::

    $ pipx install git+https://github.com/dakrauth/when.git

.. _pipx: https://pypa.github.io/pipx/


Usage
-----

To access city names, you must install the cities database::

    when --db

You can specify minimum city size by adding ``--size SIZE``, where *SIZE* can be one of:

- ``15000`` - cities with population > 15000 or capitals
- ``5000`` - cities with population > 5000 or seat of first-order admin division, i.e. US state
- ``1000`` - cities with population > 1000 or seat of third order admin division
- ``500`` - cities with population > 500 or seat of fourth-order admin division

Additionally, you can filter non-admin division seats using ``--pop POP``.

The appropriate GeoNames Gazetteer is downloaded and a Sqlite database generated. Once 
installed, you can search the database::

    $ when --db --search New York
    5106292, West New York, West New York, US, New Jersey, America/New_York
    5128581, New York City, New York City, US, New York, America/New_York


Additionally, you can add aliases. In the example directly above, we see that New York City has
a GeoNames ID of 5128581. Pass that to the ``--alias`` option along with another name that
you would like to use::

    $ when --db --alias 5128581 NYC
    $ when NYC
    2023-03-26 05:24:02-0400 (America/New_York) 085d12w (New York City, US, New York) [🌒 Waxing Crescent]


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

Requirements Python 3.8+

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


