# src/dashboard/domain/services.py
from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import Counter
from sqlmodel import Session, select, func
from reservations.domain.entities import Reservation, ReservationStatus
from restaurants.domain.entities import Table, Restaurant
from menu.domain.entities import MenuItem

class DashboardService:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_reservations_by_period(self, period: str = "day") -> Dict[str, Any]:
        """Calculates total reservations grouped by day or week."""
        if period not in ["day", "week"]:
            raise ValueError("Period must be 'day' or 'week'.")

        reservations = self.db_session.exec(select(Reservation).where(
            Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.CONFIRMED, ReservationStatus.COMPLETED])
        )).all()

        counts: Dict[str, int] = Counter()
        for res in reservations:
            if period == "day":
                key = res.reservation_time.strftime("%Y-%m-%d")
            elif period == "week":
                # Get the start of the week (Monday)
                start_of_week = res.reservation_time - timedelta(days=res.reservation_time.weekday())
                key = start_of_week.strftime("%Y-%m-%d")
            counts[key] += 1
        return dict(sorted(counts.items()))

    def get_top_preordered_dishes(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Identifies the top pre-ordered dishes."""
        reservations = self.db_session.exec(select(Reservation).where(
            Reservation.preordered_menu_items != [] # Only reservations with pre-orders
        )).all()

        dish_counts: Dict[int, int] = Counter()
        for res in reservations:
            for item_id in res.preordered_menu_items:
                dish_counts[item_id] += 1

        top_dishes_data = []
        for item_id, count in dish_counts.most_common(limit):
            menu_item = self.db_session.get(MenuItem, item_id)
            if menu_item:
                top_dishes_data.append({
                    "menu_item_id": item_id,
                    "name": menu_item.name,
                    "count": count
                })
        return top_dishes_data

    def get_restaurant_occupancy(self) -> List[Dict[str, Any]]:
        """Calculates occupancy percentage for each restaurant."""
        restaurants = self.db_session.exec(select(Restaurant)).all()
        occupancy_data = []
        for restaurant in restaurants:
            total_tables = self.db_session.exec(select(func.count(Table.id)).where(Table.restaurant_id == restaurant.id)).one_or_none() or 0
            if total_tables is None:
                total_tables = 0

            # Count tables with active reservations for today or future
            now = datetime.now()
            reserved_tables_count = self.db_session.exec(
                select(func.count(func.distinct(Reservation.table_id))).where(
                    Reservation.restaurant_id == restaurant.id,
                    Reservation.status.in_([ReservationStatus.PENDING, ReservationStatus.CONFIRMED]),
                    Reservation.reservation_time >= now
                )
            ).one_or_none() or 0
            if reserved_tables_count is None:
                reserved_tables_count = 0

            occupancy_percentage = (reserved_tables_count / total_tables * 100) if total_tables > 0 else 0
            occupancy_data.append({
                "restaurant_id": restaurant.id,
                "restaurant_name": restaurant.name,
                "total_tables": total_tables,
                "reserved_tables": reserved_tables_count,
                "occupancy_percentage": round(occupancy_percentage, 2)
            })
        return occupancy_data