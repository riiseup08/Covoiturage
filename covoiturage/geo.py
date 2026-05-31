"""Geo utilities: distances, route-corridor tests, and a cached geocoder.

Pure-stdlib math (no PostGIS dependency) so it runs anywhere the app runs.
The geocoder wraps the shared Nominatim instance with Redis caching.
"""

import hashlib
import math

from django.conf import settings
from django.core.cache import cache
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderServiceError

EARTH_RADIUS_KM = 6371.0088
_GEOCODE_CACHE_TTL = 60 * 60 * 24 * 7  # 7 days; place coordinates are stable


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance between two (lat, lon) points, in kilometres."""
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def _to_xy(lat, lon, lat_ref):
    """Local equirectangular projection (km) around a reference latitude.

    Good enough for the short corridor distances we care about (a few km of
    cross-track error over inter-city routes).
    """
    x = math.radians(lon) * math.cos(math.radians(lat_ref)) * EARTH_RADIUS_KM
    y = math.radians(lat) * EARTH_RADIUS_KM
    return x, y


def point_to_segment_km(p, a, b):
    """Shortest distance (km) from point ``p`` to the segment ``a``→``b``.

    Each argument is a ``(lat, lon)`` tuple. Used to test whether a passenger's
    pickup/dropoff lies along a driver's straight-line route.
    """
    lat_ref = (a[0] + b[0]) / 2
    px, py = _to_xy(p[0], p[1], lat_ref)
    ax, ay = _to_xy(a[0], a[1], lat_ref)
    bx, by = _to_xy(b[0], b[1], lat_ref)

    abx, aby = bx - ax, by - ay
    seg_len_sq = abx * abx + aby * aby
    if seg_len_sq == 0:
        return math.hypot(px - ax, py - ay)

    t = ((px - ax) * abx + (py - ay) * aby) / seg_len_sq
    t = max(0.0, min(1.0, t))
    closest_x = ax + t * abx
    closest_y = ay + t * aby
    return math.hypot(px - closest_x, py - closest_y)


def progress_along_segment(p, a, b):
    """Fractional position (0..1) of point ``p`` projected onto ``a``→``b``.

    Lets us check that a dropoff is *downstream* of a pickup (passenger isn't
    asking the driver to go backwards). Values are clamped to [0, 1].
    """
    lat_ref = (a[0] + b[0]) / 2
    px, py = _to_xy(p[0], p[1], lat_ref)
    ax, ay = _to_xy(a[0], a[1], lat_ref)
    bx, by = _to_xy(b[0], b[1], lat_ref)

    abx, aby = bx - ax, by - ay
    seg_len_sq = abx * abx + aby * aby
    if seg_len_sq == 0:
        return 0.0
    t = ((px - ax) * abx + (py - ay) * aby) / seg_len_sq
    return max(0.0, min(1.0, t))


_geocoder = Nominatim(
    user_agent=settings.NOMINATIM_USER_AGENT,
    timeout=settings.NOMINATIM_TIMEOUT,
)
_geocode = RateLimiter(_geocoder.geocode, min_delay_seconds=settings.NOMINATIM_MIN_DELAY)
_reverse = RateLimiter(_geocoder.reverse, min_delay_seconds=settings.NOMINATIM_MIN_DELAY)


def _cache_key(prefix, value):
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()
    return f"geo:{prefix}:{digest}"


def geocode_cached(query):
    """Forward-geocode a free-text place to ``(lat, lon)``, cached in Redis.

    Returns ``None`` on empty input, a miss, or a geocoder error so callers can
    fall back to city-name matching (important for USSD users who type a city).
    """
    query = (query or "").strip()
    if not query:
        return None
    # Allow disabling live geocoding (e.g. in tests/CI) to keep runs hermetic.
    if not getattr(settings, "GEOCODING_ENABLED", True):
        return None

    key = _cache_key("fwd", query.lower())
    cached = cache.get(key)
    if cached is not None:
        return tuple(cached) if cached else None

    try:
        location = _geocode(query, language=settings.NOMINATIM_LANGUAGE, exactly_one=True)
    except GeocoderServiceError:
        return None

    coords = (location.latitude, location.longitude) if location else None
    # Cache misses too (as an empty list) to avoid hammering Nominatim.
    cache.set(key, list(coords) if coords else [], _GEOCODE_CACHE_TTL)
    return coords
