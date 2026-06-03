from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.domain.user import User as DomainUser
from app.core.exceptions import ConflictError, NotFoundError, UnauthorizedError
from app.core.ports.user_repo import UserRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


class AuthService:

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    @staticmethod
    def hash_password(plain: str) -> str:
        return pwd_context.hash(plain)

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    def _make_token(self, user_id: UUID, token_type: str, expire: datetime) -> str:
        payload = {
            "sub": str(user_id),
            "type": token_type,
            "exp": expire,
        }
        return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    def create_access_token(self, user_id: UUID) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
        return self._make_token(user_id, TOKEN_TYPE_ACCESS, expire)

    def create_refresh_token(self, user_id: UUID) -> str:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
        return self._make_token(user_id, TOKEN_TYPE_REFRESH, expire)

    def decode_token(self, token: str, expected_type: str) -> UUID:
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
            if payload.get("type") != expected_type:
                raise UnauthorizedError("Invalid token type")
            user_id = payload.get("sub")
            if user_id is None:
                raise UnauthorizedError("Token missing subject")
            return UUID(user_id)
        except JWTError as e:
            raise UnauthorizedError(f"Invalid token: {e}") from e

    def verify_token(self, token: str) -> DomainUser:
        user_id = self.decode_token(token, TOKEN_TYPE_ACCESS)
        user = self._user_repo.find_by_id(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))
        return user

    def register(self, username: str, email: str, password: str) -> DomainUser:
        existing = self._user_repo.find_by_username_or_email(username, email)
        if existing:
            raise ConflictError("Username or email already registered")

        hashed = self.hash_password(password)
        user = DomainUser(username=username, email=email, hashed_password=hashed)
        return self._user_repo.save(user)

    def authenticate(self, username: str, password: str) -> DomainUser:
        user = self._user_repo.find_by_username(username)
        if not user or not self.verify_password(password, user.hashed_password):
            raise UnauthorizedError("Invalid username or password")
        return user
