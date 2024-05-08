import math
import time
from datetime import datetime, timedelta


class LunarPhase:
    JULIAN_OFFSET = 1721424.5
    KNOWN_NEW_MOON = 2451549.5
    SYNMONTH = 29.53050000

    def __init__(self, dt=None, dt_fmt=None):
        from .config import settings

        self.dt = dt or datetime.now()
        self.dt_fmt = dt_fmt or settings["lunar"]["format"]

        self.julian = dt.toordinal() + self.JULIAN_OFFSET
        new_moons = (self.julian - self.KNOWN_NEW_MOON) / self.SYNMONTH
        self.age = (new_moons - int(new_moons)) * self.SYNMONTH
        self.index = int(self.age / (self.SYNMONTH / 8))

        self.emoji = settings["lunar"]["emojis"][self.index]
        self.name = settings["lunar"]["phases"][self.index]

    @property
    def description(self):
        return f"{self.emoji} {self.name}"

    def __str__(self):
        dt_fmt = self.dt.strftime(self.dt_fmt)
        return f"{dt_fmt} {self.description}"


# Full moon calculations adapted from https://github.com/jr-k/python-fullmoon


def to_radian(degrees):
    return degrees * math.pi / 180


def dsin(angle):
    return math.sin(to_radian(angle))


def julian_date(td):
    td += 0.5
    z = math.floor(td)
    f = td - z
    if z < 2299161.0:
        a = z
    else:
        alpha = math.floor((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - math.floor(alpha / 4)

    b = a + 1524
    c = math.floor((b - 122.1) / 365.25)
    d = math.floor(365.25 * c)
    e = math.floor((b - d) / 30.6001)

    dd = b - d - math.floor(30.6001 * e) + f
    mm = e - 1 if e < 14 else e - 13
    yy = c - 4716 if mm > 2 else c - 4715
    return datetime(yy, mm, int(dd))


# Calculate time of the mean new Moon for date.
# ``k`` is the precomputed synodic month index, given by:  k = (year - 1900) * 12.3685
# where ``year`` is expressed as a year and fractional year.
def mean_phase(start_date, k):
    t = (start_date - 2415020) / 365.25  # time in centuries since 1900 January 0.5
    t2 = t**2
    return (
        2415020.75933
        + LunarPhase.SYNMONTH * k
        + 0.0001178 * t2
        - 0.000000155 * t**3
        + 0.00033 * dsin(166.56 + 132.87 * t - 0.009173 * t2)
    )


def moon_phase(tm, phase, second=False):
    k1k2 = time_2k_1_k2(tm)
    julian_day = true_phase(k1k2[1 if second else 0], phase)
    return (julian_day - 2440587.5) * 86400


def time_2k_1_k2(tm):
    start_date = (tm / 86400.0) + 2440587.5
    a_date = start_date - 45
    date_julian = julian_date(a_date)
    k1 = math.floor((date_julian.year + ((date_julian.month - 1) * (1.0 / 12.0)) - 1900) * 12.3685)
    a_date = nt1 = mean_phase(a_date, k1)
    while True:
        a_date += LunarPhase.SYNMONTH
        k2 = k1 + 1
        nt2 = mean_phase(a_date, k2)
        if nt1 <= a_date and nt2 > start_date:
            break

        nt1 = nt2
        k1 = k2

    return [k1, k2]


def true_phase(k, phase):
    # Please enjoy all the magic numbers!
    k += phase
    t = k / 1236.85
    t2 = t**2
    t3 = t**3

    _dsin = dsin
    pt = (
        2415020.75933
        + (LunarPhase.SYNMONTH * k)
        + (0.0001178 * t2)
        - (0.000000155 * t3)
        + (0.00033 * _dsin(166.56 + 132.87 * t - 0.009173 * t2))
    )

    m = 359.2242 + (29.10535608 * k) - (0.0000333 * t2) - (0.00000347 * t3)
    mprime = 306.0253 + (385.81691806 * k) + (0.0107306 * t2) + (0.00001236 * t3)
    f = 21.2964 + (390.67050646 * k) - (0.0016528 * t2) - (0.00000239 * t3)

    if phase < 0.01 or math.fabs(phase - 0.5) < 0.01:
        pt += (
            (0.1734 - 0.000393 * t) * _dsin(m)
            + (0.0021 * _dsin(2 * m))
            - (0.4068 * _dsin(mprime))
            + (0.0161 * _dsin(2 * mprime))
            - (0.0004 * _dsin(3 * mprime))
            + (0.0104 * _dsin(2 * f))
            - (0.0051 * _dsin(m + mprime))
            - (0.0074 * _dsin(m - mprime))
            + (0.0004 * _dsin(2 * f + m))
            - (0.0004 * _dsin(2 * f - m))
            - (0.0006 * _dsin(2 * f + mprime))
            + (0.0010 * _dsin(2 * f - mprime))
            + (0.0005 * _dsin(m + 2 * mprime))
        )

    elif math.fabs(phase - 0.25) < 0.01 or math.fabs(phase - 0.75) < 0.01:
        pt += (
            (0.1721 - 0.0004 * t) * _dsin(m)
            + 0.0021 * _dsin(2 * m)
            - 0.6280 * _dsin(mprime)
            + 0.0089 * _dsin(2 * mprime)
            - 0.0004 * _dsin(3 * mprime)
            + 0.0079 * _dsin(2 * f)
            - 0.0119 * _dsin(m + mprime)
            - 0.0047 * _dsin(m - mprime)
            + 0.0003 * _dsin(2 * f + m)
            - 0.0004 * _dsin(2 * f - m)
            - 0.0006 * _dsin(2 * f + mprime)
            + 0.0021 * _dsin(2 * f - mprime)
            + 0.0003 * _dsin(m + 2 * mprime)
            + 0.0004 * _dsin(m - 2 * mprime)
            - 0.0003 * _dsin(2 * m + mprime)
        )

        def dcos(angle):
            return math.cos(to_radian(angle))

        if phase < 0.5:
            pt += 0.0028 - 0.0004 * dcos(m) + 0.0003 * dcos(mprime)
        else:
            pt += -0.0028 + 0.0004 * dcos(m) - 0.0003 * dcos(mprime)

    return pt


def full_moon_iterator(dt=None):
    _from_timestamp = dt.timestamp() if dt else time.time()
    while True:
        full_moon = moon_phase(_from_timestamp, 0.5)
        if full_moon < _from_timestamp:
            ts = math.floor(moon_phase(_from_timestamp, 0.5, True))
        else:
            ts = math.floor(full_moon)

        yield datetime.fromtimestamp(ts)
        _from_timestamp = ts + 86400


def full_moons_for_year(year):
    dt = datetime(year, 1, 1) - timedelta(days=1)
    nfm = full_moon_iterator(dt)
    while True:
        dt = next(nfm)
        if dt.year > year:
            break

        yield dt


def full_moon(arg=None):
    # 2024-01-25
    # 2024-02-23
    # 2024-03-24
    # 2024-04-23
    # 2024-05-23
    # 2024-06-21
    # 2024-07-20
    # 2024-08-19
    # 2024-09-17
    # 2024-10-16
    # 2024-11-15
    # 2024-12-14

    match arg:
        case "next":
            return next(full_moon_iterator())
        case "last" | "prev":
            return next(full_moon_iterator(datetime.now() - timedelta(days=30)))
        case arg if isinstance(arg, int):
            pass
        case arg if isinstance(arg, str) and arg.isdigit():
            arg = int(arg)
        case None:
            arg = datetime.now().year

    return list(full_moons_for_year(arg))


if __name__ == "__main__":
    print(full_moon("last"))
    print(full_moon("next"))
    print(full_moon("2024"))
