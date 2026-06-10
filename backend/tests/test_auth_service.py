from uuid import uuid4

import pytest

from app.application.auth_service import AuthService
from app.core.domain.user import User as DomainUser
from app.core.exceptions import ConflictError, UnauthorizedError, NotFoundError
from tests.helpers import InMemoryUserRepository


@pytest.fixture
def repo() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@pytest.fixture
def auth(repo: InMemoryUserRepository) -> AuthService:
    return AuthService(repo)


def make_user(**kwargs) -> DomainUser:
    defaults = dict(
        username="testuser", email="test@example.com",
        hashed_password=AuthService.hash_password("secret"),
    )
    defaults.update(kwargs)
    return DomainUser(**defaults)


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
    def test_create_and_decode_access(self, auth: AuthService) -> None:
        uid = uuid4()
        token = auth.create_access_token(uid)
        assert auth.decode_token(token, "access") == uid

    def test_rejects_wrong_type(self, auth: AuthService) -> None:
        token = auth.create_access_token(uuid4())
        with pytest.raises(UnauthorizedError, match="Invalid token type"):
            auth.decode_token(token, "refresh")

    def test_rejects_bad_token(self, auth: AuthService) -> None:
        with pytest.raises(UnauthorizedError):
            auth.decode_token("garbage", "access")

    def test_create_refresh_token(self, auth: AuthService) -> None:
        uid = uuid4()
        token = auth.create_refresh_token(uid)
        assert auth.decode_token(token, "refresh") == uid


class TestVerifyToken:
    def test_returns_domain_user(self, auth: AuthService, repo: InMemoryUserRepository) -> None:
        user = repo.save(make_user())
        token = auth.create_access_token(user.id)
        verified = auth.verify_token(token)
        assert isinstance(verified, DomainUser)
        assert verified.username == "testuser"

    def test_raises_not_found(self, auth: AuthService) -> None:
        token = auth.create_access_token(uuid4())
        with pytest.raises(NotFoundError):
            auth.verify_token(token)


class TestRegister:
    def test_creates_user(self, auth: AuthService, repo: InMemoryUserRepository) -> None:
        user = auth.register("newuser", "new@example.com", "pass")
        assert isinstance(user, DomainUser)
        assert user.username == "newuser"
        assert repo.find_by_username("newuser") is not None

    def test_hashes_password(self, auth: AuthService) -> None:
        user = auth.register("newuser", "new@example.com", "pass")
        assert user.hashed_password != "pass"
        assert AuthService.verify_password("pass", user.hashed_password)

    def test_raises_on_duplicate(self, auth: AuthService) -> None:
        auth.register("dup", "d@d.com", "pass")
        with pytest.raises(ConflictError, match="already registered"):
            auth.register("dup", "d@d.com", "pass")


class TestAuthenticate:
    def test_success(self, auth: AuthService, repo: InMemoryUserRepository) -> None:
        repo.save(make_user())
        user = auth.authenticate("testuser", "secret")
        assert isinstance(user, DomainUser)

    def test_wrong_password(self, auth: AuthService, repo: InMemoryUserRepository) -> None:
        repo.save(make_user())
        with pytest.raises(UnauthorizedError, match="Invalid"):
            auth.authenticate("testuser", "wrongpass")

    def test_nonexistent_user(self, auth: AuthService) -> None:
        with pytest.raises(UnauthorizedError, match="Invalid"):
            auth.authenticate("ghost", "x")
