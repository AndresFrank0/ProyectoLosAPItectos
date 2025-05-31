# src/auth/domain/services.py
from typing import Optional
from sqlmodel import Session
from auth.domain.entities import User, UserCreate
from shared.security import get_password_hash, verify_password
from shared.exceptions import ConflictException

class AuthService:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def register_user(self, user_create: UserCreate) -> User:
        """Registers a new user."""
        existing_user = self.db_session.query(User).filter(User.email == user_create.email).first()
        if existing_user:
            raise ConflictException(detail="Email already registered")

        hashed_password = get_password_hash(user_create.password)
        # Ensure new users are always 'client' role unless manually set by admin in DB
        db_user = User(
            email=user_create.email,
            name=user_create.name,
            hashed_password=hashed_password,
            role="client"
        )
        self.db_session.add(db_user)
        self.db_session.commit()
        self.db_session.refresh(db_user)
        return db_user

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticates a user by email and password."""
        user = self.db_session.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user