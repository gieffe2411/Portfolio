import json
import os
import secrets
import time
from threading import Lock

DATA_FILE = os.path.join(os.path.dirname(__file__), "links.json")
_lock = Lock()

VALID_PAGES = {"friends", "professional"}


def _load():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def _save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def create_link(page, label="", expires_in=None, max_uses=None):
    """Create a new access token for a given page.

    expires_in: seconds from now until expiry, or None for no expiry.
    max_uses: max number of times the link can be redeemed, or None for unlimited.
    """
    if page not in VALID_PAGES:
        raise ValueError("Invalid page")

    token = secrets.token_urlsafe(24)
    with _lock:
        data = _load()
        data[token] = {
            "page": page,
            "label": label,
            "created": time.time(),
            "expires_at": (time.time() + expires_in) if expires_in else None,
            "max_uses": max_uses,
            "uses": 0,
            "revoked": False,
        }
        _save(data)
    return token


def get_link(token):
    data = _load()
    return data.get(token)


def list_links():
    data = _load()
    # newest first
    return sorted(
        [{"token": t, **v} for t, v in data.items()],
        key=lambda x: x["created"],
        reverse=True,
    )


def revoke_link(token):
    with _lock:
        data = _load()
        if token in data:
            data[token]["revoked"] = True
            _save(data)
            return True
    return False


def delete_link(token):
    with _lock:
        data = _load()
        if token in data:
            del data[token]
            _save(data)
            return True
    return False


def redeem(token):
    """Validate a token and register a use. Returns the page name if valid, else None."""
    with _lock:
        data = _load()
        entry = data.get(token)
        if not entry:
            return None
        if entry.get("revoked"):
            return None
        if entry.get("expires_at") and time.time() > entry["expires_at"]:
            return None
        if entry.get("max_uses") is not None and entry["uses"] >= entry["max_uses"]:
            return None

        entry["uses"] += 1
        data[token] = entry
        _save(data)
        return entry["page"]