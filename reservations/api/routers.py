# src/reservations/api/routers.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from typing import List, Optional
from datetime import datetime, date
from shared.dependencies import get_current_active_user, require_role
from reservations.domain.entities import ReservationCreate, ReservationPublic, ReservationUpdate, ReservationStatus
from reservations.domain.services import ReservationService
from shared.database import get_session
from auth.api.routers import get_current_active_user, require_role
from auth.domain.entities import User
from shared.exceptions import NotFoundException, ConflictException, BadRequestException, ForbiddenException

router = APIRouter(prefix="/reservations", tags=["reservations"])

@router.post("/", response_model=ReservationPublic, status_code=status.HTTP_201_CREATED)
def create_reservation(reservation_create: ReservationCreate,
                       current_user: User = Depends(get_current_active_user),
                       db: Session = Depends(get_session)):
    """Creates a new reservation for the current user."""
    service = ReservationService(db)
    try:
        reservation = service.create_reservation(current_user.id, reservation_create)
        return reservation
    except (NotFoundException, BadRequestException, ConflictException) as e:
        status_code = status.HTTP_404_NOT_FOUND if isinstance(e, NotFoundException) else \
                      status.HTTP_400_BAD_REQUEST if isinstance(e, BadRequestException) else \
                      status.HTTP_409_CONFLICT
        raise HTTPException(status_code=status_code, detail=e.detail)

@router.get("/me", response_model=List[ReservationPublic])
def get_my_reservations(current_user: User = Depends(get_current_active_user),
                        db: Session = Depends(get_session)):
    """Retrieves all active reservations for the current user."""
    service = ReservationService(db)
    return service.get_user_reservations(current_user.id)

@router.get("/", response_model=List[ReservationPublic],
            dependencies=[Depends(require_role(["admin"]))])
def get_all_reservations(db: Session = Depends(get_session),
                         date: Optional[date] = Query(None, description="Filter by date (YYYY-MM-DD)"),
                         restaurant_id: Optional[int] = Query(None, description="Filter by restaurant ID")):
    """Retrieves all reservations (Admin only), with optional filters."""
    service = ReservationService(db)
    filter_date_time: Optional[datetime] = None
    if date:
        filter_date_time = datetime.combine(date, datetime.min.time())
    return service.filter_reservations(filter_date_time, restaurant_id)


@router.patch("/{reservation_id}", response_model=ReservationPublic)
def update_reservation(reservation_id: int, reservation_update: ReservationUpdate,
                       current_user: User = Depends(get_current_active_user),
                       db: Session = Depends(get_session)):
    """Updates an existing reservation (Client can update their own pending reservations, Admin can update any)."""
    service = ReservationService(db)
    is_admin = current_user.role == "admin"
    try:
        updated_reservation = service.update_reservation(reservation_id, reservation_update, current_user.id, is_admin)
        return updated_reservation
    except (NotFoundException, BadRequestException, ConflictException, ForbiddenException) as e:
        status_code = status.HTTP_404_NOT_FOUND if isinstance(e, NotFoundException) else \
                      status.HTTP_400_BAD_REQUEST if isinstance(e, BadRequestException) else \
                      status.HTTP_409_CONFLICT if isinstance(e, ConflictException) else \
                      status.HTTP_403_FORBIDDEN
        raise HTTPException(status_code=status_code, detail=e.detail)


@router.delete("/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_reservation(reservation_id: int,
                       current_user: User = Depends(get_current_active_user),
                       db: Session = Depends(get_session)):
    """Cancels a reservation (Client can cancel their own, Admin can cancel any)."""
    service = ReservationService(db)
    is_admin = current_user.role == "admin"
    try:
        service.cancel_reservation(reservation_id, current_user.id, is_admin)
    except (NotFoundException, BadRequestException, ForbiddenException) as e:
        status_code = status.HTTP_404_NOT_FOUND if isinstance(e, NotFoundException) else \
                      status.HTTP_400_BAD_REQUEST if isinstance(e, BadRequestException) else \
                      status.HTTP_403_FORBIDDEN
        raise HTTPException(status_code=status_code, detail=e.detail)