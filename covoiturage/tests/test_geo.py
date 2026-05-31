"""Tests for geo math: haversine distance and corridor (cross-track) distance."""

import pytest

from covoiturage import geo

# Reference coordinates (approx) on the Douala -> Yaoundé corridor in Cameroon.
DOUALA = (4.0511, 9.7679)
YAOUNDE = (3.8480, 11.5021)
EDEA = (3.8000, 10.1333)  # roughly on the route between the two
BAFOUSSAM = (5.4781, 10.4179)  # well north, off the corridor


def test_haversine_known_distance():
    # Douala -> Yaoundé is ~200 km as the crow flies.
    d = geo.haversine_km(*DOUALA, *YAOUNDE)
    assert 180 < d < 230


def test_haversine_zero():
    assert geo.haversine_km(*DOUALA, *DOUALA) == pytest.approx(0.0, abs=1e-6)


def test_point_on_corridor_is_close():
    # Edéa lies near the straight line Douala->Yaoundé.
    dist = geo.point_to_segment_km(EDEA, DOUALA, YAOUNDE)
    assert dist < 40


def test_point_off_corridor_is_far():
    # Bafoussam is far north of the corridor.
    dist = geo.point_to_segment_km(BAFOUSSAM, DOUALA, YAOUNDE)
    assert dist > 80


def test_progress_along_segment_orders_points():
    # A point near the start projects lower than a point near the end.
    near_start = geo.progress_along_segment(DOUALA, DOUALA, YAOUNDE)
    near_end = geo.progress_along_segment(YAOUNDE, DOUALA, YAOUNDE)
    assert near_start < near_end
    assert 0.0 <= near_start <= 1.0
    assert 0.0 <= near_end <= 1.0
