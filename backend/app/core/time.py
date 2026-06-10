"""
Time helpers — single source for "now" across the codebase.

The DB stores naive UTC datetimes (SQLite has no timezone type), so this
helper returns naive UTC. It replaces the deprecated datetime.utcnow()
without changing stored semantics.
"""
from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Current UTC time as a naive datetime (matches DB storage)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
