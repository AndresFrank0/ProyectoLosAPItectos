# src/auth/infrastructure/repositories.py
from abc import ABC, abstractmethod
from typing import Optional
from sqlmodel import Session
from auth.domain.entities import User

class AbstractUserRepository(ABC):
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    def create(self, user: User) -> User:
        pass

class SqlAlchemyUserRepository(AbstractUserRepository):
    def __init__(self, session: Session):
        self.session = session

    def get_by_email(self, email: str) -> Optional[User]:
        return self.session.query(User).filter(User.email == email).first()

    def create(self, user: User) -> User:
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user