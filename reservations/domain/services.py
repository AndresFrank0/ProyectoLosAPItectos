# src/reservations/domain/services.py
from typing import List, Optional
from datetime import datetime, timedelta
from sqlmodel import Session, select
from reservations.domain.entities import Reservation, ReservationCreate, ReservationUpdate, ReservationStatus
from restaurants.domain.entities import Restaurant, Table
from menu.domain.entities import MenuItem
from shared.exceptions import NotFoundException, ConflictException, BadRequestException, ForbiddenException
from notifications.services import notify_reservation_created, notify_reservation_cancelled, notify_preorder_registered

class ReservationService:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create_reservation(self, user_id: int, reservation_create: ReservationCreate) -> Reservation:
        """Creates a new reservation with extensive validations."""
        restaurant = self.db_session.get(Restaurant, reservation_create.restaurant_id)
        if not restaurant:
            raise NotFoundException(detail="Restaurant not found.")

        table = self.db_session.get(Table, reservation_create.table_id)
        if not table or table.restaurant_id != reservation_create.restaurant_id:
            raise NotFoundException(detail="Table not found for this restaurant.")

        if not (2 <= reservation_create.num_guests <= table.capacity):
            raise BadRequestException(detail=f"Number of guests must be between 2 and table capacity ({table.capacity}).")

        # Validate reservation time within restaurant's operating hours
        reservation_hour = reservation_create.reservation_time.time()
        if not (restaurant.opening_time <= reservation_hour < restaurant.closing_time):
            raise BadRequestException(detail="Reservation time is outside restaurant operating hours.")

        # Calculate end time
        reservation_end_time = reservation_create.reservation_time + timedelta(hours=reservation_create.duration_hours)
        if reservation_end_time.time() > restaurant.closing_time and reservation_end_time.date() == reservation_create.reservation_time.date():
             # Handle cases where closing time might be on next day if it's past midnight
            if restaurant.opening_time < restaurant.closing_time: # Regular same-day closing
                raise BadRequestException(detail="Reservation duration extends past restaurant closing time.")
            # If closing time is next day (e.g., opens at 20:00, closes at 02:00), need more complex logic here
            # For simplicity, assuming same-day closing for now.

        # Validate no overlapping reservations for the same table
        overlapping_table_reservations = self.db_session.exec(
            select(Reservation).where(
                Reservation.table_id == reservation_create.table_id,
                Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.CONFIRMED]),
                Reservation.reservation_time < reservation_end_time,
                Reservation.end_time > reservation_create.reservation_time
            )
        ).all()
        if overlapping_table_reservations:
            raise ConflictException(detail="Table is already reserved for the requested time slot.")

        # Validate client has no more than 1 active reservation in the same exact time
        # This means no two reservations can start at the exact same minute for the same user.
        # Broader overlap check (any overlap for the user)
        overlapping_user_reservations = self.db_session.exec(
            select(Reservation).where(
                Reservation.user_id == user_id,
                Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.CONFIRMED]),
                Reservation.reservation_time < reservation_end_time,
                Reservation.end_time > reservation_create.reservation_time
            )
        ).all()
        if overlapping_user_reservations:
            raise ConflictException(detail="You already have an active reservation that overlaps with this time.")


        # Validate pre-ordered menu items
        if reservation_create.preordered_menu_items:
            if len(reservation_create.preordered_menu_items) > 5:
                raise BadRequestException(detail="Maximum 5 pre-ordered dishes allowed per reservation.")
            for item_id in reservation_create.preordered_menu_items:
                menu_item = self.db_session.get(MenuItem, item_id)
                if not menu_item or menu_item.restaurant_id != reservation_create.restaurant_id or not menu_item.is_available:
                    raise BadRequestException(detail=f"Pre-ordered menu item (ID: {item_id}) not found, not available, or does not belong to this restaurant.")

        db_reservation = Reservation(
            user_id=user_id,
            restaurant_id=reservation_create.restaurant_id,
            table_id=reservation_create.table_id,
            reservation_time=reservation_create.reservation_time,
            end_time=reservation_end_time,
            num_guests=reservation_create.num_guests,
            preordered_menu_items=reservation_create.preordered_menu_items
        )

        self.db_session.add(db_reservation)
        self.db_session.commit()
        self.db_session.refresh(db_reservation)

        # Send notifications
        notify_reservation_created(db_reservation.reservation_time, restaurant.name)
        if db_reservation.preordered_menu_items:
            notify_preorder_registered(len(db_reservation.preordered_menu_items))

        return db_reservation

    def get_user_reservations(self, user_id: int) -> List[Reservation]:
        """Retrieves active reservations for a specific user."""
        return self.db_session.exec(
            select(Reservation).where(
                Reservation.user_id == user_id,
                Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.CONFIRMED])
            )
        ).all()

    def get_all_reservations(self) -> List[Reservation]:
        """Retrieves all reservations (Admin only)."""
        return self.db_session.exec(select(Reservation)).all()

    def get_reservation_by_id(self, reservation_id: int) -> Optional[Reservation]:
        """Retrieves a single reservation by ID."""
        return self.db_session.get(Reservation, reservation_id)

    def cancel_reservation(self, reservation_id: int, current_user_id: int, is_admin: bool) -> Reservation:
        """Cancels a reservation."""
        reservation = self.get_reservation_by_id(reservation_id)
        if not reservation:
            raise NotFoundException(detail="Reservation not found.")

        if reservation.status == ReservationStatus.CANCELLED or reservation.status == ReservationStatus.COMPLETED:
            raise BadRequestException(detail="Cannot cancel a reservation that is already cancelled or completed.")

        # Client can only cancel their own future reservations with 1 hour anticipation
        if not is_admin:
            if reservation.user_id != current_user_id:
                raise ForbiddenException(detail="You can only cancel your own reservations.")
            if reservation.reservation_time < datetime.now() + timedelta(hours=1):
                raise BadRequestException(detail="Reservations can only be cancelled at least 1 hour in advance.")

        reservation.status = ReservationStatus.CANCELLED
        self.db_session.add(reservation)
        self.db_session.commit()
        self.db_session.refresh(reservation)

        notify_reservation_cancelled(reservation.id)
        return reservation

    def update_reservation(self, reservation_id: int, reservation_update: ReservationUpdate, current_user_id: int, is_admin: bool) -> Reservation:
        """Updates an existing reservation (limited for clients)."""
        reservation = self.get_reservation_by_id(reservation_id)
        if not reservation:
            raise NotFoundException(detail="Reservation not found.")

        if not is_admin and reservation.user_id != current_user_id:
            raise ForbiddenException(detail="You can only modify your own reservations.")

        if reservation.status != ReservationStatus.PENDING:
             raise BadRequestException(detail="Only pending reservations can be modified.")

        update_data = reservation_update.dict(exclude_unset=True)

        if "reservation_time" in update_data or "duration_hours" in update_data:
            # Re-validate time and duration if changed
            new_reservation_time = update_data.get("reservation_time", reservation.reservation_time)
            new_duration_hours = update_data.get("duration_hours", (reservation.end_time - reservation.reservation_time).total_seconds() / 3600)

            restaurant = self.db_session.get(Restaurant, reservation.restaurant_id)
            if not restaurant: # Should not happen if reservation exists
                raise NotFoundException(detail="Associated restaurant not found.")

            # Re-validate time within restaurant hours
            new_reservation_hour = new_reservation_time.time()
            if not (restaurant.opening_time <= new_reservation_hour < restaurant.closing_time):
                raise BadRequestException(detail="New reservation time is outside restaurant operating hours.")

            new_end_time = new_reservation_time + timedelta(hours=new_duration_hours)
            if new_end_time.time() > restaurant.closing_time and new_end_time.date() == new_reservation_time.date():
                raise BadRequestException(detail="New reservation duration extends past restaurant closing time.")

            # Check for overlapping table reservations (excluding the current reservation)
            overlapping_table_reservations = self.db_session.exec(
                select(Reservation).where(
                    Reservation.table_id == reservation.table_id,
                    Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.CONFIRMED]),
                    Reservation.id != reservation_id, # Exclude current reservation
                    Reservation.reservation_time < new_end_time,
                    Reservation.end_time > new_reservation_time
                )
            ).all()
            if overlapping_table_reservations:
                raise ConflictException(detail="Table is already reserved for the new requested time slot.")

            # Check for overlapping user reservations (excluding the current reservation)
            overlapping_user_reservations = self.db_session.exec(
                select(Reservation).where(
                    Reservation.user_id == current_user_id,
                    Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.CONFIRMED]),
                    Reservation.id != reservation_id, # Exclude current reservation
                    Reservation.reservation_time < new_end_time,
                    Reservation.end_time > new_reservation_time
                )
            ).all()
            if overlapping_user_reservations:
                raise ConflictException(detail="You already have an active reservation that overlaps with the new time.")

            reservation.reservation_time = new_reservation_time
            reservation.end_time = new_end_time

        if "num_guests" in update_data:
            table = self.db_session.get(Table, reservation.table_id)
            if not table:
                raise NotFoundException(detail="Associated table not found.")
            if not (2 <= update_data["num_guests"] <= table.capacity):
                raise BadRequestException(detail=f"Number of guests must be between 2 and table capacity ({table.capacity}).")
            reservation.num_guests = update_data["num_guests"]

        if "preordered_menu_items" in update_data:
            if len(update_data["preordered_menu_items"]) > 5:
                raise BadRequestException(detail="Maximum 5 pre-ordered dishes allowed per reservation.")
            for item_id in update_data["preordered_menu_items"]:
                menu_item = self.db_session.get(MenuItem, item_id)
                if not menu_item or menu_item.restaurant_id != reservation.restaurant_id or not menu_item.is_available:
                    raise BadRequestException(detail=f"Pre-ordered menu item (ID: {item_id}) not found, not available, or does not belong to this restaurant.")
            reservation.preordered_menu_items = update_data["preordered_menu_items"]

        if "status" in update_data and is_admin: # Only admin can change status
            reservation.status = update_data["status"]
        elif "status" in update_data and not is_admin:
            raise ForbiddenException(detail="Clients cannot change reservation status directly.")

        self.db_session.add(reservation)
        self.db_session.commit()
        self.db_session.refresh(reservation)
        return reservation

    def filter_reservations(self, date: Optional[datetime] = None, restaurant_id: Optional[int] = None) -> List[Reservation]:
        """Filters reservations by date and/or restaurant (Admin only)."""
        query = select(Reservation)
        if date:
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            query = query.where(Reservation.reservation_time >= start_of_day, Reservation.reservation_time < end_of_day)
        if restaurant_id:
            query = query.where(Reservation.restaurant_id == restaurant_id)
        return self.db_session.exec(query).all()