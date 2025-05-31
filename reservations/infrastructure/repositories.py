# src/reservations/infrastructure/repositories.py
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from sqlmodel import Session, select
from reservations.domain.entities import Reservation, ReservationStatus

class AbstractReservationRepository(ABC):
    @abstractmethod
    def get_by_id(self, reservation_id: int) -> Optional[Reservation]:
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: int) -> List[Reservation]:
        pass

    @abstractmethod
    def get_all(self) -> List[Reservation]:
        pass

    @abstractmethod
    def create(self, reservation: Reservation) -> Reservation:
        pass

    @abstractmethod
    def update(self, reservation: Reservation) -> Reservation:
        pass

    @abstractmethod
    def delete(self, reservation_id: int):
        pass

    @abstractmethod
    def get_overlapping_table_reservations(self, table_id: int, start_time: datetime, end_time: datetime, exclude_reservation_id: Optional[int] = None) -> List[Reservation]:
        pass

    @abstractmethod
    def get_overlapping_user_reservations(self, user_id: int, start_time: datetime, end_time: datetime, exclude_reservation_id: Optional[int] = None) -> List[Reservation]:
        pass

    @abstractmethod
    def get_reservations_by_filters(self, date: Optional[datetime] = None, restaurant_id: Optional[int] = None) -> List[Reservation]:
        pass

class SqlAlchemyReservationRepository(AbstractReservationRepository):
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, reservation_id: int) -> Optional[Reservation]:
        return self.session.get(Reservation, reservation_id)

    def get_by_user_id(self, user_id: int) -> List[Reservation]:
        return self.session.exec(
            select(Reservation).where(Reservation.user_id == user_id)
        ).all()

    def get_all(self) -> List[Reservation]:
        return self.session.exec(select(Reservation)).all()

    def create(self, reservation: Reservation) -> Reservation:
        self.session.add(reservation)
        self.session.commit()
        self.session.refresh(reservation)
        return reservation

    def update(self, reservation: Reservation) -> Reservation:
        self.session.add(reservation)
        self.session.commit()
        self.session.refresh(reservation)
        return reservation

    def delete(self, reservation_id: int):
        reservation = self.get_by_id(reservation_id)
        if reservation:
            self.session.delete(reservation)
            self.session.commit()

    def get_overlapping_table_reservations(self, table_id: int, start_time: datetime, end_time: datetime, exclude_reservation_id: Optional[int] = None) -> List[Reservation]:
        query = select(Reservation).where(
            Reservation.table_id == table_id,
            Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.CONFIRMED]),
            Reservation.reservation_time < end_time,
            Reservation.end_time > start_time
        )
        if exclude_reservation_id:
            query = query.where(Reservation.id != exclude_reservation_id)
        return self.session.exec(query).all()

    def get_overlapping_user_reservations(self, user_id: int, start_time: datetime, end_time: datetime, exclude_reservation_id: Optional[int] = None) -> List[Reservation]:
        query = select(Reservation).where(
            Reservation.user_id == user_id,
            Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.CONFIRMED]),
            Reservation.reservation_time < end_time,
            Reservation.end_time > start_time
        )
        if exclude_reservation_id:
            query = query.where(Reservation.id != exclude_reservation_id)
        return self.session.exec(query).all()

    def get_reservations_by_filters(self, date: Optional[datetime] = None, restaurant_id: Optional[int] = None) -> List[Reservation]:
        query = select(Reservation)
        if date:
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            query = query.where(Reservation.reservation_time >= start_of_day, Reservation.reservation_time < end_of_day)
        if restaurant_id:
            query = query.where(Reservation.restaurant_id == restaurant_id)
        return self.session.exec(query).all()