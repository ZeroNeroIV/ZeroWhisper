from datetime import datetime, timedelta
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import Session, select

from app.config import settings
from app.exceptions import unauthorized, conflict
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: UUID) -> str:
    """Create a short-lived JWT (access token)."""
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    return _make_token(user_id, TOKEN_TYPE_ACCESS, expire)


def create_refresh_token(user_id: UUID) -> str:
    """Create a long-lived JWT (refresh token)."""
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    return _make_token(user_id, TOKEN_TYPE_REFRESH, expire)


def _make_token(user_id: UUID, token_type: str, expire: datetime) -> str:
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str, expected_type: str) -> UUID:
    """
    Decode a JWT and return the user_id UUID.
    Raises HTTPException(401) if invalid, expired, or wrong type.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise unauthorized("Invalid or expired token")
    if payload.get("type") != expected_type:
        raise unauthorized(f"Expected {expected_type} token")
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise unauthorized("Token missing subject")
    return UUID(user_id_str)


def register_user(session: Session, username: str, email: str, password: str) -> User:
    """Create a new user. Raises 409 if username or email already taken."""
    existing = session.exec(
        select(User).where((User.username == username) | (User.email == email))
    ).first()
    if existing:
        raise conflict("Username or email already registered")
    user = User(username=username, email=email, hashed_password=hash_password(password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def authenticate_user(session: Session, username: str, password: str) -> User:
    """Return User if credentials valid, else raise 401."""
    user = session.exec(select(User).where(User.username == username)).first()
    if not user or not verify_password(password, user.hashed_password):
        raise unauthorized("Invalid username or password")
    return user


def verify_token(token: str, session: Session) -> User:
    """Decode access token and return the User. Raises 401 if invalid."""
    user_id = decode_token(token, TOKEN_TYPE_ACCESS)
    user = session.get(User, user_id)
    if not user:
        raise unauthorized("User not found")
    return user
