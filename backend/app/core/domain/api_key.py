from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from app.core.time import utc_now
from uuid import UUID


@dataclass
class ApiKey:
    user_id: UUID
    key_hash: str
    prefix: str
    name: str
    is_active: bool = True
    last_used_at: datetime | None = None
    id: int | None = field(default=None)
    created_at: datetime = field(default_factory=utc_now)
