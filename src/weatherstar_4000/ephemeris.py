"""Small deterministic sun/moon calculator for display screens.

Kept deliberately simple (like the legacy screens it feeds): pure functions of
a date and coordinate so screens stay offline and tests deterministic.  Times
are close to local wall-clock for continental US latitudes (US DST rule), not
survey-grade.

- :func:`sun_clock_minutes`: sunrise/sunset as minutes since local midnight.
- :func:`next_moon_phases`: the next four primary moon phases from a date.
"""

from __future__ import annotations

import math
from datetime import date, timedelta

#: Synodic month (new moon to new moon).
_SYNODIC = 29.53058867
#: Reference new moon (approximate date of the 2000-01-06 new moon).
_REF_NEW_MOON = date(2000, 1, 6)
#: Earth's axial tilt (degrees).
_OBLIQUITY = 23.44
#: Sunrise/sunset are defined by the sun's center 0.833 deg below the horizon
#: (accounts for atmospheric refraction and the solar disc).
_HORIZON = -0.833


def _day_of_year(day: date) -> int:
    return day.timetuple().tm_yday


def _us_dst(day: date) -> bool:
    """True when US daylight-saving is in effect for ``day``."""
    if day.month < 3 or day.month > 11:
        return False
    if day.month > 3 and day.month < 11:
        return True
    # March: DST starts the second Sunday; November: ends the first Sunday.
    if day.month == 3:
        start = date(day.year, 3, 1)
        second_sunday = start + timedelta(days=(6 - start.weekday()) % 7 + 7)
        return day >= second_sunday
    end = date(day.year, 11, 1)
    first_sunday = end + timedelta(days=(6 - end.weekday()) % 7)
    return day < first_sunday


def _solar_declination(doy: int) -> float:
    """Solar declination (degrees) for a day of year (approximate sinusoid)."""
    return -_OBLIQUITY * math.cos(math.radians(360.0 / 365.0 * (doy + 10)))


def sun_clock_minutes(day: date, lat: float, lon: float) -> tuple[int, int]:
    """Local sunrise/sunset minutes-since-midnight for ``day`` at (lat, lon).

    A simplified solar-day model: the hour angle of sunrise/sunset is computed
    from the solar declination, then expressed in the location's local clock
    (approximated with the US DST rule).  Returns ``(sunrise, sunset)``.
    """
    lat = float(lat or 0.0)
    lon = float(lon or 0.0)
    doy = _day_of_year(day)
    decl = math.radians(_solar_declination(doy))
    lat_rad = math.radians(lat)

    cosine = (math.sin(math.radians(_HORIZON)) - math.sin(lat_rad) * math.sin(decl)) / (
        math.cos(lat_rad) * math.cos(decl)
    )
    cosine = max(-1.0, min(1.0, cosine))
    half_day_minutes = math.degrees(math.acos(cosine)) / 15.0 * 60.0

    # Apparent solar minutes when the center crosses the horizon.
    rise_solar = 12.0 * 60.0 - half_day_minutes
    set_solar = 12.0 * 60.0 + half_day_minutes

    # Pseudo wall clock: solar time minus the longitude-in-zone offset (the
    # location's own meridian is solar noon) plus daylight-saving when active.
    zone_correction = (lon - round(lon / 15.0) * 15.0) * 4.0  # 4 min / degree
    dst = 60 if _us_dst(day) and lat > 0 else 0
    return int(round(rise_solar + zone_correction + dst)), int(
        round(set_solar + zone_correction + dst)
    )


def _phase_fraction(day: date) -> float:
    """0.0 = new moon ... 0.5 = full ... 1.0 wraps to new again."""
    days = (day - _REF_NEW_MOON).days
    return (days / _SYNODIC) % 1.0


def next_moon_phases(start: date) -> list[tuple[str, date]]:
    """The next four primary phases from ``start`` as ``(name, date)``.

    Names follow ws3kp's almanac ("NEW", "FIRST", "FULL", "LAST"); the dates
    are the crossings nearest after ``start``, in chronological order.
    """
    fraction = _phase_fraction(start)
    targets = ((0.0, "NEW"), (0.25, "FIRST"), (0.5, "FULL"), (0.75, "LAST"))
    events: list[tuple[float, str, date]] = []
    for threshold, name in targets:
        cycles = (threshold - fraction) % 1.0
        when = start + timedelta(days=round(cycles * _SYNODIC))
        events.append((cycles, name, when))
    events.sort(key=lambda item: item[0])
    return [(name, when) for _cycles, name, when in events]
