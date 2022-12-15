import sys
from datetime import datetime, timedelta


class LunarPhase:
    JULIAN_OFFSET = 1721424.5
    LUNAR_CYCLE = 29.53
    KNOWN_NEW_MOON = 2451549.5
    TABLE = [
        ("🌑", "New Moon"),
        ("🌒", "Waxing Crescent"),
        ("🌓", "First Quarter"),
        ("🌔", "Waxing Gibbous"),
        ("🌕", "Full Moon"),
        ("🌖", "Waning Gibbous"),
        ("🌗", "Last Quarter"),
        ("🌘", "Waning Crescent"),
    ]

    def __init__(self, dt=None, dt_fmt="%a, %b %d %Y"):
        self.dt = dt or datetime.now()
        self.dt_fmt = dt_fmt

        self.julian = dt.toordinal() + self.JULIAN_OFFSET
        new_moons = (self.julian - self.KNOWN_NEW_MOON) / self.LUNAR_CYCLE
        self.age = (new_moons - int(new_moons)) * self.LUNAR_CYCLE
        self.index = int(self.age / (self.LUNAR_CYCLE / 8))
        self.emoji, self.name = self.TABLE[self.index]

    @property
    def description(self):
        return f"{self.emoji} {self.name}"

    def __str__(self):
        dt_fmt = self.dt.strftime(self.dt_fmt)
        return f"{dt_fmt} {self.description}"


def main(): 
    import sys
    from dateutil.parser import parse

    inp = " ".join(sys.argv[1:])
    start, sep, end = inp.partition("..")
    day = parse(start) if start else datetime.now()
    end = parse(end) if end else day
    td = timedelta(days=+1)

    while day <= end:
        print(LunarPhase(day))
        day += td

if __name__=="__main__": 
    sys.exit(main())
