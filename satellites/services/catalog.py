from __future__ import annotations

from typing import Dict, List, Optional

from satellites.models import TLE


def _clean_name(name: Optional[str]) -> str:
    return (name or "").strip()


def catalog_label(name: Optional[str], norad_id: int) -> str:
    clean = _clean_name(name)
    return clean or f"NORAD {norad_id}"


def list_catalog_entries() -> List[Dict[str, object]]:
    """Return lightweight catalog entries ready for template rendering."""
    entries = []
    for tle in TLE.objects.only("norad_id", "name"):
        name = _clean_name(tle.name)
        entries.append(
            {
                "norad_id": tle.norad_id,
                "name": name,
                "label": catalog_label(name, tle.norad_id),
            }
        )
    entries.sort(key=lambda entry: entry["label"].lower())
    return entries


def search_catalog(query: str) -> Optional[TLE]:
    """Return the best matching TLE for the provided query."""
    query = (query or "").strip()
    if not query:
        return None

    qs = TLE.objects.all()
    if query.isdigit():
        match = qs.filter(norad_id=int(query)).first()
        if match:
            return match

    match = qs.filter(name__iexact=query).first()
    if match:
        return match

    return qs.filter(name__icontains=query).order_by("name").first()
