# src/reservations/domain/entities.py
from typing import Optional, List
from datetime import datetime, timedelta
from enum import Enum

from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import Column


class ReservationStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class ReservationBase(SQLModel):
    user_id: int = Field(foreign_key="user.id", index=True) # Asumiendo relación con User
    restaurant_id: int = Field(foreign_key="restaurant.id", index=True) # Asumiendo relación con Restaurant
    num_guests: int = Field(gt=0) # Número de personas para la reserva
    reservation_time: datetime # Fecha y hora de la reserva
    status: ReservationStatus = Field(default="pending") # <-- ¡CAMBIA ESTO!
    notes: Optional[str] = None
    special_requests: List[str] = Field(default_factory=list, sa_column=Column(JSON))

    allergens: List[str] = Field(default_factory=list, sa_column=Column(JSON))

class Reservation(ReservationBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class ReservationCreate(ReservationBase):
    pass

class ReservationUpdate(SQLModel):
    num_guests: Optional[int] = None
    reservation_time: Optional[datetime] = None
    status: Optional[ReservationStatus] = None
    notes: Optional[str] = None
    # Si actualizas special_requests, también debe ser List[str]
    special_requests: Optional[List[str]] = Field(default=None, sa_column=Column(JSON)) # Para updates, puede ser None

class ReservationPublic(ReservationBase):
    id: int