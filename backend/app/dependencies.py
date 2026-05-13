from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.database import get_session
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> User:
    from app.services.auth import verify_token
    return verify_token(token, session)


async def get_current_user_by_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    session: Session = Depends(get_session),
) -> User:
    from app.services.api_key_service import verify_api_key
    user = verify_api_key(x_api_key, session)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key",
        )
    return user
