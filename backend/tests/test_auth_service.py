from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from jose import jwt
from sqlmodel import Session

from app.application.auth_service import AuthService
from app.core.config import settings
from app.core.domain.user import User as DomainUser
from app.core.exceptions import ConflictError, UnauthorizedError, NotFoundError
from app.models.user import User as ORMUser


@pytest.fixture
def session() -> MagicMock:
    return MagicMock(spec=Session)


@pytest.fixture
def auth(session: MagicMock) -> AuthService:
    return AuthService(session)


def fake_orm_user(**kwargs) -> ORMUser:
    defaults = dict(
        id=str(uuid4()), username="testuser", email="test@example.com",
        hashed_password=AuthService.hash_password("secret"),
        is_admin=False, created_at=datetime.utcnow(),
    )
    defaults.update(kwargs)
    obj = MagicMock(spec=ORMUser)
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


class TestHashPassword:
    def test_hash_returns_string(self) -> None:
        h = AuthService.hash_password("hello")
        assert isinstance(h, str)
        assert len(h) > 10

    def test_hashes_differ(self) -> None:
        assert AuthService.hash_password("a") != AuthService.hash_password("a")


class TestVerifyPassword:
    def test_correct(self) -> None:
        h = AuthService.hash_password("secret")
        assert AuthService.verify_password("secret", h)

    def test_incorrect(self) -> None:
        h = AuthService.hash_password("secret")
        assert not AuthService.verify_password("wrong", h)


class TestTokens:
    def test_create_and_decode_access(self) -> None:
        uid = uuid4()
        token = AuthService(MagicMock()).create_access_token(uid)
        decoded = AuthService(MagicMock()).decode_token(token, "access")
        assert decoded == uid

    def test_rejects_wrong_type(self) -> None:
        token = AuthService(MagicMock()).create_access_token(uuid4())
        with pytest.raises(UnauthorizedError, match="Invalid token type"):
            AuthService(MagicMock()).decode_token(token, "refresh")

    def test_rejects_bad_token(self) -> None:
        with pytest.raises(UnauthorizedError):
            AuthService(MagicMock()).decode_token("garbage", "access")

    def test_create_refresh_token(self) -> None:
        uid = uuid4()
        token = AuthService(MagicMock()).create_refresh_token(uid)
        decoded = AuthService(MagicMock()).decode_token(token, "refresh")
        assert decoded == uid


class TestVerifyToken:
    def test_returns_domain_user(self, auth: AuthService, session: MagicMock) -> None:
        orm = fake_orm_user()
        session.get.return_value = orm
        token = auth.create_access_token(UUID(orm.id))
        user = auth.verify_token(token)
        assert isinstance(user, DomainUser)
        assert user.username == "testuser"

    def test_raises_not_found(self, auth: AuthService, session: MagicMock) -> None:
        session.get.return_value = None
        token = auth.create_access_token(uuid4())
        with pytest.raises(NotFoundError):
            auth.verify_token(token)


class TestRegister:
    def test_creates_user(self, auth: AuthService, session: MagicMock) -> None:
        session.exec.return_value.first.return_value = None
        session.add = Mock()
        session.commit = Mock()
        session.refresh = Mock()
        session.refresh.side_effect = lambda obj: setattr(
            obj, "id", str(uuid4())
        )

        user = auth.register("newuser", "new@example.com", "pass", "pass")
        assert isinstance(user, DomainUser)
        assert user.username == "newuser"
        session.add.assert_called_once()

    def test_raises_on_mismatched_passwords(self, auth: AuthService) -> None:
        with pytest.raises(ValueError, match="do not match"):
            auth.register("u", "e@e.com", "pass1", "pass2")

    def test_raises_on_duplicate(self, auth: AuthService, session: MagicMock) -> None:
        session.exec.return_value.first.return_value = MagicMock()
        with pytest.raises(ConflictError, match="already registered"):
            auth.register("dup", "d@d.com", "pass", "pass")


class TestAuthenticate:
    def test_success(self, auth: AuthService, session: MagicMock) -> None:
        orm = fake_orm_user()
        session.exec.return_value.first.return_value = orm
        user = auth.authenticate("testuser", "secret")
        assert isinstance(user, DomainUser)

    def test_wrong_password(self, auth: AuthService, session: MagicMock) -> None:
        orm = fake_orm_user()
        session.exec.return_value.first.return_value = orm
        with pytest.raises(UnauthorizedError, match="Invalid"):
            auth.authenticate("testuser", "wrongpass")

    def test_nonexistent_user(self, auth: AuthService, session: MagicMock) -> None:
        session.exec.return_value.first.return_value = None
        with pytest.raises(UnauthorizedError, match="Invalid"):
            auth.authenticate("ghost", "x")
