from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.database import get_session
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, RefreshRequest, UserRead
from app.services.auth import (
    register_user,
    authenticate_user,
    create_access_token,
    create_refresh_token,
    decode_token,
    TOKEN_TYPE_REFRESH,
)

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(body: UserRegister, session: Session = Depends(get_session)):
    user = register_user(session, username=body.username, email=body.email, password=body.password)
    return UserRead(
        id=str(user.id),
        username=user.username,
        email=user.email,
        is_admin=user.is_admin,
    )


@router.post("/login", response_model=TokenResponse)
def login(body: UserLogin, session: Session = Depends(get_session)):
    user = authenticate_user(session, username=body.username, password=body.password)
    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh")
def refresh(body: RefreshRequest, session: Session = Depends(get_session)):
    user_id = decode_token(body.refresh_token, TOKEN_TYPE_REFRESH)
    new_access_token = create_access_token(user_id)
    return {"access_token": new_access_token, "token_type": "bearer"}
