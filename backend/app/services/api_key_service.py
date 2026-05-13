import hashlib
import secrets
from datetime import datetime
from uuid import UUID

from sqlmodel import Session, select

from app.models.api_key import ApiKey
from app.models.user import User

KEY_PREFIX = "zwp_"
KEY_BYTES = 32  # 32 random bytes → 43-char base64url


def _generate_raw_key() -> str:
    """Generate a new raw API key string: 'zwp_' + 43 urlsafe base64 chars."""
    return KEY_PREFIX + secrets.token_urlsafe(KEY_BYTES)


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def create_api_key(session: Session, user_id: UUID, name: str) -> tuple[ApiKey, str]:
    """
    Generate a new API key. Returns (ApiKey row, raw_key).
    raw_key is the only time the full key is visible — it is NOT stored.
    """
    raw_key = _generate_raw_key()
    key = ApiKey(
        user_id=user_id,
        key_hash=_hash_key(raw_key),
        prefix=raw_key[:12],
        name=name,
    )
    session.add(key)
    session.commit()
    session.refresh(key)
    return key, raw_key


def list_keys(session: Session, user_id: UUID) -> list[ApiKey]:
    return session.exec(
        select(ApiKey).where(ApiKey.user_id == user_id, ApiKey.is_active == True)
    ).all()


def revoke_key(session: Session, key_id: int, user_id: UUID) -> bool:
    """Soft-delete an API key. Returns False if not found or not owned by user."""
    key = session.exec(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user_id)
    ).first()
    if not key:
        return False
    key.is_active = False
    session.add(key)
    session.commit()
    return True


def verify_api_key(raw_key: str, session: Session) -> User | None:
    """
    Validate a raw API key string. Returns the owning User on success, None on failure.
    Updates last_used_at if valid.
    """
    key_hash = _hash_key(raw_key)
    api_key = session.exec(
        select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active == True)
    ).first()
    if not api_key:
        return None
    # Update last_used_at
    api_key.last_used_at = datetime.utcnow()
    session.add(api_key)
    session.commit()
    # Fetch and return the user
    from app.models.user import User
    return session.get(User, api_key.user_id)
