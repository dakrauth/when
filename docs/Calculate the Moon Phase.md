Calculate the Moon Phase
========================

It is pretty easy to estimate the phase of the moon based on the relatively small variations in the orbits
of the Earth and moon. The **New Moon** (when the sun does not illuminate any of the moon’s surface we
see on Earth) repeats every 29.53 days. This is different than its period to revolve around the Earth
(27.32 days).

The difference is mainly due to the Earth moving in its orbit around the sun. The Earth
revolves around 360 degrees in about 365 days. So we move really close to 1 degree a day in our orbit.
To make up that distance and get in the same location in the sky, the moon needs about another hour
each day. That is why if you observe the moon at the same time each day, it will not be in the same
location in the sky.

The easiest way to calculate the current phase of the moon is to compare it to a known time when it
was new, and determine how many cycles it has passed through. We can do this by finding the number
of days from a known New Moon and then dividing by the lunar period.

On 1/6/2000 at 12:24:01, the moon was New. If we know how many days have elapsed since that time,
we can know how many lunar cycles we have seen. Let’s calculate this using Julian Day numbers.

Julian day numbers are a system of counting days since a specific day (January 1, 4713 BC). Entering the
above date of the New Moon in an online calculator gives the value of 2451549.5. Now we need to get
the current date in Julian Day number format.

Let’s calculate it.

    1) Express the date as Y = year, M = Month, D = day.
    2) If the month is January or February, subtract 1 from the year and add 12 to the month.
    3) With a calculator, do the following calculations:
        a. A = Y/100 and then record the integer part     A = _______________
        b. B = A/4 and then record the integer part       B = _______________
        c. C = 2-A+B                                      C = _______________
        d. E = 365.25 x (Y+4716) record the integer part  E = _______________
        e. F = 30.6001 x (M+1) record the integer part    F = _______________
        f. JD = C+D+E+F-1524.5                           JD = _______________

Now that we have the Julian day, let’s calculate the days since the last new moon:

    Day since New = JD - 2451549.5

If we divide this by the period, we will have how many new moons there have been:

    New Moons = Days since New / 29.53

If we drop the whole number, the decimal represents the fraction of a cycle that the moon is currently
in. Multiply the fraction by 29.53 and you will uncover how many days you are into the moon’s cycle.

Let’s do a sample calculation. Let’s calculate the phase of the moon on 3/1/2017:

    1) Express the date as Y = 2017, M = 3, D = 1.
    2) Since the month March (M=3), we don’t need to adjust the values.
    3) With a calculator, do the following calculations:
        a. A = Y/100 and then record the integer part    A = 20
        b. B = A/4 and then record the integer part      B = 5
        c. C = 2-A+B                                     C = -13
        d. E = 365.25 x (Y+4716) record the integer part E = 2459228
        e. F = 30.6001 x (M+1) record the integer part   F = 122
        f. JD = C+D+E+F-1524.5                          JD = 2457813.5

Now that we have the Julian day, let’s calculate the days since the last new moon:

    Day since New = 2457813.5 - 2451549.5 = 6264 days

If we divide this by the period, we will have how many new moons there have been:

    New Moons = 6264 / 29.53 = 212.123 cycles

Now, multiply the fractional part by 29.53:

    Days into cycle = 0.123 x 29.53 = 3.63 days since New Moon

Our simple calculation above doesn’t account for a few factors in the moon phase so it is not as
accurate as more rigorous calculations, but it is close enough to get a good idea of the status of the
moon. We also didn’t adjust for the time of day.

The age of the moon is the number of days since the most recent New Moon. Here is what that day
translates to:
