"""Tests for the small sun/moon calculator (ephemeris.py)."""

from datetime import date

from weatherstar_4000.ephemeris import next_moon_phases, sun_clock_minutes


def test_sun_times_are_plausible_and_differ_by_day():
    # Orlando, FL around the equinox: sunrise ~6-7am, sunset ~6-8pm.
    rise, fall = sun_clock_minutes(date(2026, 3, 20), 28.5383, -81.3792)
    assert 300 <= rise <= 480  # 5:00am - 8:00am
    assert 1080 <= fall <= 1260  # 6:00pm - 9:00pm
    assert rise < fall

    # Tomorrow drifts at most a couple minutes from today.
    rise_next, fall_next = sun_clock_minutes(date(2026, 3, 21), 28.5383, -81.3792)
    assert abs(rise - rise_next) <= 3
    assert abs(fall - fall_next) <= 3


def test_sun_times_winter_is_short_day():
    rise, fall = sun_clock_minutes(date(2026, 12, 21), 44.0, -93.0)
    assert (fall - rise) < 60 * 11  # under ~11 hours at latitude 44 in winter


def test_next_moon_phases_four_primary_events_chronological():
    phases = next_moon_phases(date(2026, 9, 6))
    names = [name for name, _when in phases]
    assert set(names) == {"NEW", "FIRST", "FULL", "LAST"}
    whens = [when for _name, when in phases]
    assert whens == sorted(whens)
    # All four phases fit within a synodic month of the start date.
    assert all((when - date(2026, 9, 6)).days <= 30 for when in whens)


def test_moon_phase_gap_between_events_roughly_weekly():
    whens = [when for _name, when in next_moon_phases(date(2026, 9, 6))]
    gaps = [(whens[i + 1] - whens[i]).days if i + 1 < len(whens) else 0 for i in range(len(whens))]
    for gap in gaps[:-1]:
        assert 6 <= gap <= 9
