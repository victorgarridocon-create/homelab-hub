"""Icons uploaded as data URLs are stored in the database, but lists only reference them by URL.

Embedding base64 images in every list made /inventory and the map ~1.8 MB for 150 items; with a
URL the browser downloads each icon once and caches it (the ?v= version changes when it's edited).
"""
import base64
import binascii
import re

_DATA_URL = re.compile(r"^data:(image/[a-z0-9.+-]+);base64,(.+)$", re.IGNORECASE | re.DOTALL)


def icon_url(entity_type, item):
    icon = getattr(item, "icon", None)
    if not icon or not icon.startswith("data:image/"):
        return icon  # emoji/text icons stay inline
    version = int(item.updated_at.timestamp()) if getattr(item, "updated_at", None) else 0
    return f"/api/icons/{entity_type}/{item.id}?v={version}"


def list_dict(entity_type, item):
    """to_dict() for list responses: image icons replaced by their URL."""
    data = item.to_dict()
    if "icon" in data:
        data["icon"] = icon_url(entity_type, item)
    return data


def decode(data_url):
    """(mimetype, bytes) from a data URL, or None if it isn't a valid base64 image."""
    match = _DATA_URL.match(data_url or "")
    if not match:
        return None
    try:
        return match.group(1).lower(), base64.b64decode(match.group(2), validate=False)
    except (binascii.Error, ValueError):
        return None
