from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Tuple

from satellites.models import Favorite, TLE
from satellites.services.catalog import catalog_label
from satellites.services.propagation import propagate_now
from satellites.services.tle_fetcher import TLENotFound, get_or_refresh_tle


def _resolve_tle_data(tle: TLE, max_age_hours: int = 48) -> Tuple[str, str, str]:
    """Return the freshest TLE data available for the provided TLE record."""
    try:
        return get_or_refresh_tle(tle.norad_id, max_age_hours=max_age_hours)
    except TLENotFound:
        return (tle.name or "").strip(), tle.line1, tle.line2


def _enrich_stats(stats: Optional[Dict[str, object]]) -> Optional[Dict[str, object]]:
    if not stats:
        return stats
    timestamp = stats.get("timestamp")
    if timestamp:
        try:
            stats["timestamp_obj"] = datetime.fromisoformat(timestamp)
        except ValueError:
            stats["timestamp_obj"] = None
    else:
        stats["timestamp_obj"] = None
    return stats


def satellite_detail_payload(tle: TLE, *, max_age_hours: int = 48) -> Dict[str, object]:
    """Build the context data for the satellite detail page."""
    name, line1, line2 = _resolve_tle_data(tle, max_age_hours=max_age_hours)
    clean_name = (name or "").strip()
    try:
        stats = propagate_now(line1, line2)
        error_message = None
    except ValueError as exc:
        stats = None
        error_message = str(exc)

    payload = {
        "satellite": {
            "norad_id": tle.norad_id,
            "name": clean_name,
            "label": catalog_label(clean_name, tle.norad_id),
        },
        "stats": _enrich_stats(stats),
        "error": error_message,
    }
    return payload


def satellite_position_payload(norad_id: int, *, max_age_hours: int = 48) -> Dict[str, object]:
    """Return the API payload for a single satellite position."""
    tle = TLE.objects.get(pk=norad_id)
    name, line1, line2 = _resolve_tle_data(tle, max_age_hours=max_age_hours)
    pos = propagate_now(line1, line2)
    return {"norad_id": norad_id, "name": name, **pos}


def favorite_positions_for_user(user, *, max_age_hours: int = 48) -> List[Dict[str, object]]:
    """Return current positions for the authenticated user's favorites."""
    favorites = Favorite.objects.filter(user=user).only("norad_id", "name")
    results: List[Dict[str, object]] = []
    for fav in favorites:
        try:
            name, line1, line2 = get_or_refresh_tle(fav.norad_id, max_age_hours=max_age_hours)
            stats = propagate_now(line1, line2)
        except (TLENotFound, ValueError):
            continue
        results.append({"norad_id": fav.norad_id, "name": name, **stats})
    return results
