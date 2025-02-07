# when 🌐🕐

[![Tests](https://github.com/dakrauth/when/actions/workflows/test.yml/badge.svg)](https://github.com/dakrauth/when)
[![PyPI](https://img.shields.io/pypi/v/when.svg)](https://pypi.python.org/pypi/when)

**Scenario:** Your favorite sporting event, concert, performance, conference, or symposium is happening
in Ulan Bator, Mongolia and all you have is the time of the event relative to the location -- Feb 8, 3pm.

* What time is it currently in Ulan Bator?

  ```console
  $ when --source "Ulan Bator"
  2025-02-07 03:08:58+0800 (+08, Asia/Ulaanbaatar) 038d05w (Ulan Bator, Ulaanbaatar, MN, Asia/Ulaanbaatar)[🌓 First Quarter]
  ```
* What time is the event in your local time (PST for me, currently)?

  ```console
  $ when --source "Ulan Bator" Feb 8 3pm
  2025-02-07 23:00:00-0800 (PST, America/Los_Angeles) 038d05w [🌓 First Quarter]
  ```

* What time did it or will it occur at some other time, past or present?

  ```console
  $ when --source "Ulan Bator" --offset +15d6h
  2025-02-22 09:18:01+0800 (+08, Asia/Ulaanbaatar) 053d07w (Ulan Bator, Ulaanbaatar, MN, Asia/Ulaanbaatar)[🌗 Last Quarter]
  ```
* What about for your friends in other locations around the world?

  ```console
  $ when --exact --target London,GB  --source "Ulan Bator" Feb 8 3pm
  2025-02-08 07:00:00+0000 (GMT, Europe/London) 039d05w (London, England, GB, Europe/London)[🌓 First Quarter]
  ```

## Table of Contents

- [Features](#features)
- [Installation](#installation)
  - [Database Installation](#database-installation)
- [Examples](#examples)
  - [Basic Usage](#basic-usage)
  - [Formats](#formats)
  - [Timezones](#timezones)
  - [Cities](#cities)
  - [Database Search](#database-search)
  - [Database Aliases](#database-aliases)
  - [Source Input Times](#source-input-times)
  - [Targets](#targets)
  - [JSON](#json)
  - [Holidays](#holidays)
  - [Full Moons](#full-moons)
- [Formatting](#formatting)
- [Configuration](#configuration)
  - [Default TOML](#default-toml)
- [Complete CLI Options](#complete-cli-options)
- [Development](#development)

## Features

``when`` can refer to source and target locations via the ``--source`` and ``--target`` specifiers.

* 🏙️ ``when`` can download a [GeoNames](https://www.geonames.org/export/) cities database for referencing locations by city name
* 🕘 All IANA time zone definitions are available, as well as the most common time zone aliases (i.e.: ``EST`` => ``US/Eastern``).
  For further reading, see [Time Zones Aren’t Offsets – Offsets Aren’t Time Zones](https://spin.atomicobject.com/time-zones-offsets/)
* 🌖 Display current lunar state
* 🎉 List common holidays for a given country and/or year (US or configurable)
* 🌝 Show dates for full moons
* ⚙️ Extensive configuration options for results
* 📄 JSON output
* 🗓️ Allow for past and future offsets
* 🔎 96% test code coverage


## Installation

> **Requirements**
>
> _Python 3.10+ or pipx_


* Install from [PyPI](https://pypi.org/project/when/):

  ```console
  $ pip install when
  ```
* Install using [`pipx`](https://pypa.github.io/pipx/):

  ```console
  $ pipx install when
  ```
  or:
  ```console
  $ pipx install git+https://github.com/dakrauth/when.git
  ```
* Install from [GitHub source](https://github.com/dakrauth/when)

  ```console
  git clone git@github.com:dakrauth/when.git
  python -m pip install --require-virtualenv when/
  ```
  See [Development](#development) below for detailed instructions for working on `when` below.

> **Note**
>
> _Once installed, if you wish to utilize ``when``'s full capabilities, you should install the GeoNames cities database as describe next._

### Database installation

To access city names, you need to install the cities database after installing the ``when`` application:

```console
$ when --db <SIZE> [options]
```

Use the ``<SIZE>`` option to specify a database download size. For detailed info, see the
[GeoNames ReadMe](https://download.geonames.org/export/dump/readme.txt).

``<SIZE>`` options must be one of the following:

* ``sm``: ~2.9M download, ~2M DB
  * All country capitals
  * Cities with population > 15,000
* ``md``: **_default_** ~4.8M download, ~3.1M DB; same as ``sm``, plus:
  * Seat of first-order admin division, i.e. US state
  * Cities with population > 5,000
* ``lg``: ~9.5M download, ~5.8M DB; same as ``md``, plus:
  * seat of admin division down to third level (counties)
  * cities with population > 1,000
* ``xl`` ~12.1M download, ~7.2M DB;  same as ``lg``, plus:
  * seat of admin division down to fourth order 
  * cities with population > 500


Additional ``options`` are:

* ``--db-pop``: Filter non-admin division seats providing a minimum city population size
* ``--force``: Force an existing database to be overwritten

## Examples

### Basic Usage

> **Note**
>
> _In the following examples, please the ``xl`` database has been installed, and that the system ``TZ`` is configured for the West coast of the NW United States._

The most basic form of `when` will show the following output, based upon the system's date and timezone configuration:

```console
$ when
2025-02-04 17:38:10-0800 (PST, America/Los_Angeles) 035d05w [🌒 Waxing Crescent]
```

### Formats

The default format of the output is structured as:

```<ISO 8601 timestamp> (<TZ abbreviation>, <TZ name>) <Day-if-year>d<Week-of-year>w [<Lunar information>]```

The default format configuration is specified by the string `'%F %T%z (%Z%!Z) %jd%Ww %!C[%!l]'`.

Output formatting can be configured in multiple ways:

* Creating a `.whenrc.toml` configuration file (see [Configuration](#configuration) below)
* Use the `--format` option and use formatting pattern (see [Formatting](#formatting) below):

  ```console
  $ when --format '%a %b %d %Y %T %!c' --source Seattle
  Tue Feb 04 2025 17:40:11 Seattle, Washington, US, America/Los_Angeles
  ```

* Use one of the pre-configured, named formats such as `iso` and `rfc2822`:

  ```console
  $ when --format iso
  2025-02-05T16:31:22-0800
  
  $ when --format rfc2822
  Wed, 05 Feb 2025 16:31:30 -0800
  ```

* Set a ``WHENFORMAT`` env variable, which can specified in your with your shell config (such as ``.bash_prole`` or ``.zshrc``),
  or prepended to the command line command, for instance:

  ```console
  $ WHENFORMAT='%a %b %d %Y %T %!c' when --source Seattle
  Tue Feb 04 2025 17:40:09 Seattle, Washington, US, America/Los_Angeles
  ```

### Timezones

Source (and target) locations can also be specified by IANA timezone names or aliases:

```console
$ when --source CST
2025-02-04 20:01:43-0600 (CST, Central Standard Time) 035d05w [🌒 Waxing Crescent]
2025-02-05 06:01:43+0400 (+04, Caucasus Standard Time) 036d05w [🌓 First Quarter]
2025-02-05 10:01:43+0800 (CST, China Standard Time) 036d05w [🌓 First Quarter]
2025-02-04 21:01:43-0500 (CST, Cuba Standard Time) 035d05w [🌒 Waxing Crescent]
```

### Cities

Searching by city can return numerous results, since by default the database is queried looking
for matches __containing__ the search string:

```console
$ when --source Paris
2025-02-05 04:04:44+0200 (EET, Europe/Athens) 036d05w (Kyparissía (Kyparissia), Peloponnese, GR, Europe/Athens)[🌓 First Quarter]
2025-02-05 02:04:44+0000 (GMT, Europe/London) 036d05w (Whiteparish, England, GB, Europe/London)[🌓 First Quarter]
2025-02-05 03:04:44+0100 (CET, Europe/Paris) 036d05w (Villeparisis, Île-de-France, FR, Europe/Paris)[🌓 First Quarter]
2025-02-05 03:04:44+0100 (CET, Europe/Paris) 036d05w (Seyssinet-Pariset, Auvergne-Rhône-Alpes, FR, Europe/Paris)[🌓 First Quarter]
2025-02-05 03:04:44+0100 (CET, Europe/Paris) 036d05w (Paris, Île-de-France, FR, Europe/Paris)[🌓 First Quarter]
2025-02-05 03:04:44+0100 (CET, Europe/Paris) 036d05w (Cormeilles-en-Parisis, Île-de-France, FR, Europe/Paris)[🌓 First Quarter]
...
2025-02-04 20:04:44-0600 (CST, America/Chicago) 035d05w (Paris, Texas, US, America/Chicago)[🌒 Waxing Crescent]
2025-02-04 21:04:44-0500 (EST, America/New_York) 035d05w (Paris, Maine, US, America/New_York)[🌒 Waxing Crescent]
2025-02-04 19:04:44-0700 (MST, America/Boise) 035d05w (Paris, Idaho, US, America/Boise)[🌒 Waxing Crescent]
2025-02-04 21:04:44-0500 (EST, America/Toronto) 035d05w (Paris, Ontario, CA, America/Toronto)[🌒 Waxing Crescent]
2025-02-05 09:04:44+0700 (WIB, Asia/Jakarta) 036d05w (Danauparis, Aceh, ID, Asia/Jakarta)[🌓 First Quarter]
```

Use ``--exact`` to restrict the results to a full match on the respective columns within the database:

```console
$ when --exact --source paris
2025-02-05 03:09:24+0100 (CET, Europe/Paris) 036d05w (Paris, Île-de-France, FR, Europe/Paris)[🌓 First Quarter]
2025-02-04 21:09:24-0500 (EST, America/Panama) 035d05w (París (Paris), Herrera Province, PA, America/Panama)[🌒 Waxing Crescent]
2025-02-04 20:09:24-0600 (CST, America/Chicago) 035d05w (Paris, Illinois, US, America/Chicago)[🌒 Waxing Crescent]
2025-02-04 21:09:24-0500 (EST, America/New_York) 035d05w (Paris, Kentucky, US, America/New_York)[🌒 Waxing Crescent]
2025-02-04 20:09:24-0600 (CST, America/Chicago) 035d05w (Paris, Missouri, US, America/Chicago)[🌒 Waxing Crescent]
2025-02-04 20:09:24-0600 (CST, America/Chicago) 035d05w (Paris, Tennessee, US, America/Chicago)[🌒 Waxing Crescent]
2025-02-04 20:09:24-0600 (CST, America/Chicago) 035d05w (Paris, Texas, US, America/Chicago)[🌒 Waxing Crescent]
2025-02-04 21:09:24-0500 (EST, America/New_York) 035d05w (Paris, Maine, US, America/New_York)[🌒 Waxing Crescent]
2025-02-04 19:09:24-0700 (MST, America/Boise) 035d05w (Paris, Idaho, US, America/Boise)[🌒 Waxing Crescent]
2025-02-04 21:09:24-0500 (EST, America/Toronto) 035d05w (Paris, Ontario, CA, America/Toronto)[🌒 Waxing Crescent]
```

You can also filter by country:

```console
$ when --exact --source paris,fr
2025-02-05 03:10:17+0100 (CET, Europe/Paris) 036d05w (Paris, Île-de-France, FR, Europe/Paris)[🌓 First Quarter]
```

Or by subnational region (e.g. a state in the US):

```console
$ when --exact --source paris,maine,us
2025-02-04 21:11:13-0500 (EST, America/New_York) 035d05w (Paris, Maine, US, America/New_York)[🌒 Waxing Crescent]
```

### Database Search

Use ``--search`` to search the GeoNames database, once installed:

```console
$ when --search paris
 259782 Kyparissía (Kyparissia), Peloponnese, GR, Europe/Athens
2634065 Whiteparish, England, GB, Europe/London
2968496 Villeparisis, Île-de-France, FR, Europe/Paris
2974645 Seyssinet-Pariset, Auvergne-Rhône-Alpes, FR, Europe/Paris
2988507 Paris, Île-de-France, FR, Europe/Paris
3023645 Cormeilles-en-Parisis, Île-de-France, FR, Europe/Paris
3703358 París (Paris), Herrera Province, PA, America/Panama
3725276 Fond Parisien, Ouest, HT, America/Port-au-Prince
4246659 Paris, Illinois, US, America/Chicago
4303602 Paris, Kentucky, US, America/New_York
4402452 Paris, Missouri, US, America/Chicago
4647963 Paris, Tennessee, US, America/Chicago
4717560 Paris, Texas, US, America/Chicago
4974617 Paris, Maine, US, America/New_York
5603240 Paris, Idaho, US, America/Boise
6942553 Paris, Ontario, CA, America/Toronto
8571689 Danauparis, Aceh, ID, Asia/Jakarta
```

Results of a database search are formated as:

```<GeoName ID> <Name> [(<ASCII Name>)], <Subregion>, <Country code>, <Timezone info>```

The search feature checks for containment by default, but exact filtering can be useful, as discussed above:

```console
$ when --search paris --exact
2988507 Paris, Île-de-France, FR, Europe/Paris
3703358 París (Paris), Herrera Province, PA, America/Panama
4246659 Paris, Illinois, US, America/Chicago
4303602 Paris, Kentucky, US, America/New_York
4402452 Paris, Missouri, US, America/Chicago
4647963 Paris, Tennessee, US, America/Chicago
4717560 Paris, Texas, US, America/Chicago
4974617 Paris, Maine, US, America/New_York
5603240 Paris, Idaho, US, America/Boise
6942553 Paris, Ontario, CA, America/Toronto
```

### Database Aliases

Use ``--alias`` to add aliases for easier search. For instance, consider the following:

```console
$ when --search "New York City"
5128581 New York City, New York, US, America/New_York
```

If you are checking New York City often, it can be a pain to type out;  however, 
in the result above, we see that New York City has a GeoNames ID of 5128581. You can pass along with the ``--alias`` option along with another name that you would like to use instead:

```console
$ when --alias 5128581 NYC
$ when --source NYC
2025-02-04 21:33:33-0500 (EST, America/New_York) 035d05w (New York City, New York, US, America/New_York)[🌒 Waxing Crescent]
```

A complete list of aliases can be shown:

```console
$ when --aliases
NYC: New York City | New York | US | America/New_York
```

### Source Input Times

If we know a given time in a specific city or timezone, we can have that converted to our current timezone:

```console
$ when --source Honolulu 17:00
2025-02-04 19:00:00-0800 (PST, America/Los_Angeles) 035d05w [🌒 Waxing Crescent]
2025-02-04 19:00:00-0800 (PST, America/Los_Angeles) 035d05w [🌒 Waxing Crescent]
```

**But, wait!** Why are there two results?

Doing a DB search will reveal that there are two entries that could match _Honolulu_:

```console
$ when --search Honolulu
5856195 Honolulu, Hawaii, US, Pacific/Honolulu
7315245 East Honolulu, Hawaii, US, Pacific/Honolulu
```
In this case, ``--exact`` will show only one result:

```console
$ when --exact --source Honolulu 17:00
2025-02-04 19:00:00-0800 (PST, America/Los_Angeles) 035d05w [🌒 Waxing Crescent]
```
The timestamp string parsing is provided by ``python-dateutil`` and is very generous:

```console
$ when --exact --source Honolulu March 7, 1945 5pm
1945-03-07 19:30:00-0700 (PWT, America/Los_Angeles) 066d10w [🌘 Waning Crescent]
```

### Targets

By default, if the ``--target`` option is not specified, it will default to the local machine's date/time/timezone. However, you can specify another target. For instance, if you are traveling to New York City, and you wish to see when an event occurring in Olso, Norway will be, relatively speaking:

```console
$ when --exact --target NYC --source Oslo June 2 6pm
2025-06-02 12:00:00-0400 (EDT, America/New_York) 153d22w (New York City, New York, US, America/New_York)[🌒 Waxing Crescent]
```

Notice that details regarding the source (Oslo) are absent. Adding the ``--group`` option will remedy that:

```console
$ when --group --exact --target NYC --source Oslo June 2 6pm
2025-06-02 12:00:00-0400 (EDT, America/New_York) 153d22w (New York City, New York, US, America/New_York)[🌒 Waxing Crescent]
 ↳ @2025-06-02 18:00:00+0200 (CEST, Europe/Oslo) 153d22w (Oslo, NO, Europe/Oslo)[🌒 Waxing Crescent]

$ when --exact --source paris,fr --target paris,us --group 21:00
2025-02-04 14:00:00-0600 (CST, America/Chicago) 035d05w (Paris, Illinois, US, America/Chicago)[🌒 Waxing Crescent]
 ↳ @2025-02-04 21:00:00+0100 (CET, Europe/Paris) 035d05w (Paris, Île-de-France, FR, Europe/Paris)[🌒 Waxing Crescent]
...
 ↳ @2025-02-04 21:00:00+0100 (CET, Europe/Paris) 035d05w (Paris, Île-de-France, FR, Europe/Paris)[🌒 Waxing Crescent]
2025-02-04 13:00:00-0700 (MST, America/Boise) 035d05w (Paris, Idaho, US, America/Boise)[🌒 Waxing Crescent]
 ↳ @2025-02-04 21:00:00+0100 (CET, Europe/Paris) 035d05w (Paris, Île-de-France, FR, Europe/Paris)[🌒 Waxing Crescent]
```

### JSON

Output can be formatted as `JSON`, e.g., for use in API's:

```console
$ when --exact --json --source Seattle --target Honolulu
[
  {
    "iso": "2025-02-04T17:12:18-10:00",
    "lunar": {
      "emoji": "\ud83c\udf12",
      "phase": "Waxing Crescent",
      "age": 6.545
    },
    "zone": {
      "name": "Pacific/Honolulu",
      "city": {
        "name": "Honolulu",
        "ascii": "Honolulu",
        "country": "US",
        "tz": "Pacific/Honolulu",
        "subnational": "Hawaii"
      },
      "utcoffset": [-10, 0]
    },
    "source": {
      "iso": "2025-02-04T19:12:18-08:00",
      "lunar": {
        "emoji": "\ud83c\udf12",
        "phase": "Waxing Crescent",
        "age": 6.545
      },
      "zone": {
        "name": "America/Los_Angeles",
        "city": {
          "name": "Seattle",
          "ascii": "Seattle",
          "country": "US",
          "tz": "America/Los_Angeles",
          "subnational": "Washington"
        },
        "utcoffset": [-8, 0]
      },
      "source": null,
      "offset": null
    },
    "offset": null
  }
]
```

### Holidays

`when` comes pre-configured with most US holidays:

```console
$ when --holidays US
New Year's Day.....Wed, Jan 01 2025 ( -35 days) [🌑 New Moon]
MLK Day............Mon, Jan 20 2025 ( -16 days) [🌖 Waning Gibbous]
Valentine's Day....Fri, Feb 14 2025 (   9 days) [🌕 Full Moon]
Presidents' Day....Mon, Feb 17 2025 (  12 days) [🌖 Waning Gibbous]
Mardi Gras.........Tue, Mar 04 2025 (  27 days) [🌒 Waxing Crescent]
Ash Wednesday......Wed, Mar 05 2025 (  28 days) [🌒 Waxing Crescent]
St. Patrick's Day..Mon, Mar 17 2025 (  40 days) [🌕 Full Moon]
Palm Sunday........Sun, Apr 13 2025 (  67 days) [🌕 Full Moon]
Good Friday........Fri, Apr 18 2025 (  72 days) [🌖 Waning Gibbous]
Easter.............Sun, Apr 20 2025 (  74 days) [🌗 Last Quarter]
Mother's Day.......Sun, May 11 2025 (  95 days) [🌔 Waxing Gibbous]
Memorial Day.......Mon, May 26 2025 ( 110 days) [🌘 Waning Crescent]
Father's Day.......Sun, Jun 15 2025 ( 130 days) [🌖 Waning Gibbous]
Juneteenth.........Thu, Jun 19 2025 ( 134 days) [🌗 Last Quarter]
Independence Day...Fri, Jul 04 2025 ( 149 days) [🌓 First Quarter]
Labor..............Mon, Sep 01 2025 ( 208 days) [🌓 First Quarter]
Columbus Day.......Mon, Oct 13 2025 ( 250 days) [🌖 Waning Gibbous]
Halloween..........Fri, Oct 31 2025 ( 268 days) [🌓 First Quarter]
Veterans Day.......Tue, Nov 11 2025 ( 279 days) [🌖 Waning Gibbous]
Thanksgiving.......Thu, Nov 27 2025 ( 295 days) [🌒 Waxing Crescent]
Christmas..........Thu, Dec 25 2025 ( 323 days) [🌒 Waxing Crescent]
```

You can specify a year as well:

```console
$ when --holidays US 2026
New Year's Day.....Thu, Jan 01 2026 ( 330 days) [🌔 Waxing Gibbous]
MLK Day............Mon, Jan 19 2026 ( 348 days) [🌑 New Moon]
Valentine's Day....Sat, Feb 14 2026 ( 374 days) [🌘 Waning Crescent]
...
Veterans Day.......Wed, Nov 11 2026 ( 644 days) [🌑 New Moon]
Thanksgiving.......Thu, Nov 26 2026 ( 659 days) [🌕 Full Moon]
Christmas..........Fri, Dec 25 2026 ( 688 days) [🌕 Full Moon]
```

### Full Moons

```console
$ when --fullmoon
2025-01-13
2025-02-12
2025-03-14
2025-04-12
2025-05-12
2025-06-10
2025-07-10
2025-08-08
2025-09-06
2025-10-06
2025-11-05
2025-12-04
```

You can specify `next`, `prev`, or use `YYY[-MM]`:

```console
$ when --fullmoon next
2025-02-12

$ when --fullmoon prev
2025-01-13

$ when --fullmoon 2026
2026-01-03
2026-02-01
...
2026-11-23
2026-12-23

$ when --fullmoon 2026-01
2026-01-03
```
## Formatting

**Complete listing of specifiers:**

* `%a`: Abbreviated weekday name, `Thu` *
* `%A`: Full weekday name, `Thursday` *
* `%b`: Abbreviated month name, `Aug` *
* `%B`: Full month name, `August` *
* `%c`: Date and time representation, `Thu Aug 23 14:55:02 2001` *
* `%C`: Year divided by 100 and truncated to integer (00-99), `20` †
* `%d`: Day of the month, zero-padded (01-31), `23`
* `%D`: Short MM/DD/YY date, equivalent to `%m/%d/%y`, `08/23/01` †
* `%e`: Day of the month, space-padded ( 1-31), `23` †
* `%F`: Short YYYY-MM-DD date, equivalent to `%Y-%m-%d`, `2001-08-23` †
* `%g`: Week-based year, last two digits (00-99), `01` †
* `%G`: Week-based year, `2001` †
* `%h`: Abbreviated month name (same as `%b`), `Aug` †*
* `%H`: Hour in 24h format (00-23), `14`
* `%I`: Hour in 12h format (01-12), `02`
* `%j`: Day of the year (001-366), `235`
* `%m`: Month as a decimal number (01-12), `08`
* `%M`: Minute (00-59), `55`
* `%n`: New-line character, `\\n` †
* `%p`: AM or PM designation, `PM`
* `%r`: 12-hour clock time, `02:55:02 pm` †*
* `%R`: 24-hour HH:MM time, equivalent to `%H:%M`, `14:55` †
* `%S`: Second (00-61), `02`
* `%t`: Horizontal-tab character, `\\t` †
* `%T`: ISO 8601 time format (HH:MM:SS), equivalent to `%H:%M:%S`, `14:55:02` †
* `%u`: ISO 8601 weekday as number with Monday as 1 (1-7), `4` †
* `%U`: Week number with the first Sunday as the first day of week one (00-53), `33`
* `%V`: ISO 8601 week number (01-53), `34` †
* `%w`: Weekday as a decimal number with Sunday as 0 (0-6), `4`
* `%W`: Week number with the first Monday as the first day of week one (00-53), `34`
* `%x`: Date representation, `08/23/01` *
* `%X`: Time representation, `14:55:02` *
* `%y`: Year, last two digits (00-99), `01`
* `%Y`: Year, `2001`
* `%z`: ISO 8601 offset from UTC in timezone (1 minute=1, 1 hour=100), no characters if timezone cannot be determined `+100`
* `%Z`: Locale timezone name or abbreviation, no characters if timezone cannot be determined `CDT` *
* `%%`: A % sign, `%`
* `%!z`: When timezone name, `US/New_York` ‡
* `%!Z`: When timezone name, using conditional format in settings, `US/New_York` ‡
* `%!c`: City name, `Honolulu, Hawaii, US` ‡
* `%!C`: City name, using conditional format in settings, `Honolulu, Hawaii, US` ‡
* `%!l`: Lunar phase emoji, `🌖` ‡

† C99 extension | ‡ `when` extension | * Locale-dependent

## Configuration

Configuration is done via [TOML format](https://toml.io/en/) and can be overridden (overlayed, actually)
by creating a `.whenrc.toml` in either the local directory from which `when` is executed, or from
`~/.whenrc.toml`.

To show the current configuration status, you can do:

```console
$ when --config
``` 

You can refer to [Default TOML](#default-toml) below for all configuration values.

To begin, create the file:

```console
$ cat << EOF > .whenrc.toml
[formats.named]
foo = "%x %X"
bar = "%!l"

[formats.source]
grouped = " ➡️ From "
EOF
```

Now, verify the configuration by doing:

```console
$ when --config
``` 

At the top of the output there should be a line similar to the following:

```console
# Read from /path/to/pwd/.whenrc.toml
```

Let's see the result:

```console
$ when --format foo --group --source seattle --target "New York City"
02/05/25 19:02:12
 ➡️ From 02/05/25 16:02:12

$ when --format bar --source seattle
🌓 First Quarter
```

### Default TOML

```toml
[calendar]
months = [ "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
days = [ "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

[holidays]
format = "%a, %b %d %Y"

[lunar]
phases = [ "New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous", "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent"]
emojis = "🌑🌒🌓🌔🌕🌖🌗🌘"
format = "%a, %b %d %Y"

[holidays.US]
Easter = "Easter +0"
"Ash Wednesday" = "Easter -46"
"Mardi Gras" = "Easter -47"
"Palm Sunday" = "Easter -7"
"Good Friday" = "Easter -2"
"Memorial Day" = "Last Mon in May"
"MLK Day" = "3rd Mon in Jan"
"Presidents' Day" = "3rd Mon in Feb"
"Mother's Day" = "2nd Sun in May"
"Father's Day" = "3rd Sun in Jun"
Labor = "1st Mon in Sep"
"Columbus Day" = "2nd Mon in Oct"
Thanksgiving = "4th Thu in Nov"
"New Year's Day" = "Jan 1"
"Valentine's Day" = "Feb 14"
"St. Patrick's Day" = "Mar 17"
Juneteenth = "Jun 19"
"Independence Day" = "Jul 4"
Halloween = "Oct 31"
"Veterans Day" = "Nov 11"
Christmas = "Dec 25"

[formats.named]
default = "%F %T%z (%Z%!Z) %jd%Ww %!C[%!l]"
rfc2822 = "%a, %d %b %Y %H:%M:%S %z"
iso = "%Y-%m-%dT%H:%M:%S%z"

[formats.conditional]
Z = ", {}"
C = "({})"

[formats.source]
grouped = " ↳ @"
```

## Complete CLI Options

```console
usage: when [--delta {long,short}] [--offset [+-]?(\d+wdhm)+] [--prefix] [-s SOURCE] [-t TARGET] [-f FORMAT] [-g] [--all]
            [--holidays COUNTRY_CODE] [-v] [-V] [--json] [--config] [--force] [--search] [--exact] [--alias ALIAS]
            [--aliases] [--db DB] [--db-pop DB_POP] [--tz-alias] [--fullmoon] [-h]
            [timestr ...]

Convert times to and from time zones or cities

positional arguments:
  timestr               Timestamp to parse, defaults to local time

options:
  --delta {long,short}  Show the delta to the given timestamp
  --offset [+-]?(\d+wdhm)+
                        Show the difference from a given offset
  --prefix              Show when's directory
  -s SOURCE, --source SOURCE
                        Timezone / city to convert the timestr from, defaulting to local time
  -t TARGET, --target TARGET
                        Timezone / city to convert the timestr to (globbing patterns allowed, can be comma delimited),
                        defaulting to local time
  -f FORMAT, --format FORMAT
                        Output formatting. Additional formats can be shown using the -v option with -h
  -g, --group           Group sources together under same target results
  --all                 Show times in all common timezones
  --holidays COUNTRY_CODE
                        Show holidays for given country code.
  -v, --verbosity       Verbosity (-v, -vv, etc). Use -v to show `when` extension detailed help
  -V, --version         show program's version number and exit
  --json                Output results in nicely formatted JSON
  --config              Show current configuration settings
  --force               Force an existing database to be overwritten
  --search              Search database for the given city
  --exact               DB searches must be exact
  --alias ALIAS         Create a new alias from the city id
  --aliases             Show all DB aliases
  --db DB               Create cities database from Geonames file. Can be one of 'xl' ('xlarge'), 'lg' ('large'), 'md'
                        ('medium'), 'sm' ('small')
  --db-pop DB_POP       City population minimum.
  --tz-alias            Search for a time zone alias
  --fullmoon            Show full moon(s) for given year or month. Can be in the format of: 'next' | 'prev' | YYYY[-MM]
  -h, --help            Show helpful usage information

Use -v option for details
```

## Development

Requires Python 3.10+ and [just](https://github.com/casey/just) for convenience.

```console
$ git clone git@github.com:dakrauth/when.git
$ cd when
$ just
```

> **Note:**
>
> _``just`` is a shortcut for ``just --help``_

Set up dev env:

```console
$ just init
```

Test, and code coverage:

```console
$ just test
$ just cov
```

Only run a test matching matching a given substring:

```console
$ just test -k test_sometest
```

Run the when command with any arguments:

```console
$ just when --source poulsbo
```

Or, start an interactive session:

```console
$ . ./dev/venv/bin/activate
$ when --help
```
