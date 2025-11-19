from __future__ import annotations

from typing import Iterable, List, Dict

from satellites.models import Favorite


def serialize_favorite(favorite: Favorite) -> Dict[str, object]:
    """Return a stable representation of a single favorite for API responses."""
    return {
        "id": favorite.id,
        "norad_id": favorite.norad_id,
        "name": favorite.name,
        "notes": favorite.notes,
        "created_at": favorite.created_at.isoformat() if favorite.created_at else None,
    }


def serialize_favorites(favorites: Iterable[Favorite]) -> List[Dict[str, object]]:
    """Serialize an iterable of favorites."""
    return [serialize_favorite(favorite) for favorite in favorites]
