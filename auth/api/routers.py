# src/auth/api/routers.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from datetime import timedelta

from shared.dependencies import get_current_active_user, require_role
from auth.domain.entities import User,UserCreate, UserPublic, Token, TokenData
from auth.domain.services import AuthService
from auth.infrastructure.repositories import SqlAlchemyUserRepository
from shared.database import get_session
from shared.dependencies import get_current_active_user, require_role
from shared.security import create_access_token, decode_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, oauth2_scheme
from shared.exceptions import ConflictException

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register_user(user_create: UserCreate, db: Session = Depends(get_session)):
    """Registers a new user (client role by default)."""
    auth_service = AuthService(db)
    try:
        new_user = auth_service.register_user(user_create)
        return UserPublic(id=new_user.id, email=new_user.email, name=new_user.name, role=new_user.role)
    except ConflictException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.detail)

@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_session)):
    """Authenticates a user and returns an access token."""
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Determine scopes based on user role
    scopes = []
    if user.role == "client":
        scopes = ["client:read", "client:write"]
    elif user.role == "admin":
        scopes = ["admin:read", "admin:write", "client:read", "client:write"] # Admins can do everything

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "scopes": scopes}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Example of a protected endpoint
@router.get("/me", response_model=UserPublic)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Returns information about the current authenticated user."""
    return current_user