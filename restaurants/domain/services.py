# src/restaurants/domain/services.py
from typing import List, Optional
from sqlmodel import Session, select
from datetime import time

from restaurants.domain.entities import Restaurant, RestaurantCreate, RestaurantUpdate, Table, TableCreate, TableUpdate
from shared.exceptions import NotFoundException, ConflictException, BadRequestException

class RestaurantService:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create_restaurant(self, restaurant_create: RestaurantCreate) -> Restaurant:
        """Creates a new restaurant."""
        if restaurant_create.closing_time <= restaurant_create.opening_time:
            raise BadRequestException(detail="Closing time must be after opening time.")
        existing_restaurant = self.db_session.query(Restaurant).filter(Restaurant.name == restaurant_create.name).first()
        if existing_restaurant:
            raise ConflictException(detail="Restaurant with this name already exists.")

        db_restaurant = Restaurant.from_orm(restaurant_create)
        self.db_session.add(db_restaurant)
        self.db_session.commit()
        self.db_session.refresh(db_restaurant)
        return db_restaurant

    def get_restaurants(self) -> List[Restaurant]:
        """Retrieves all restaurants."""
        return self.db_session.exec(select(Restaurant)).all()

    def get_restaurant_by_id(self, restaurant_id: int) -> Optional[Restaurant]:
        """Retrieves a restaurant by its ID."""
        return self.db_session.get(Restaurant, restaurant_id)

    def update_restaurant(self, restaurant_id: int, restaurant_update: RestaurantUpdate) -> Restaurant:
        """Updates an existing restaurant."""
        restaurant = self.get_restaurant_by_id(restaurant_id)
        if not restaurant:
            raise NotFoundException(detail="Restaurant not found.")

        update_data = restaurant_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(restaurant, key, value)

        if restaurant.closing_time <= restaurant.opening_time:
             raise BadRequestException(detail="Closing time must be after opening time.")

        self.db_session.add(restaurant)
        self.db_session.commit()
        self.db_session.refresh(restaurant)
        return restaurant

    def delete_restaurant(self, restaurant_id: int):
        """Deletes a restaurant."""
        restaurant = self.get_restaurant_by_id(restaurant_id)
        if not restaurant:
            raise NotFoundException(detail="Restaurant not found.")
        if restaurant.tables: # Check if there are associated tables
            raise BadRequestException(detail="Cannot delete restaurant with associated tables. Delete tables first.")

        self.db_session.delete(restaurant)
        self.db_session.commit()

    def create_table(self, restaurant_id: int, table_create: TableCreate) -> Table:
        """Creates a new table for a restaurant."""
        restaurant = self.get_restaurant_by_id(restaurant_id)
        if not restaurant:
            raise NotFoundException(detail="Restaurant not found.")

        if not (2 <= table_create.capacity <= 12):
            raise BadRequestException(detail="Table capacity must be between 2 and 12.")

        existing_table = self.db_session.query(Table).filter(
            Table.restaurant_id == restaurant_id,
            Table.table_number == table_create.table_number
        ).first()
        if existing_table:
            raise ConflictException(detail="Table with this number already exists for this restaurant.")

        db_table = Table(restaurant_id=restaurant_id, **table_create.dict())
        self.db_session.add(db_table)
        self.db_session.commit()
        self.db_session.refresh(db_table)
        return db_table

    def get_tables_by_restaurant(self, restaurant_id: int) -> List[Table]:
        """Retrieves all tables for a given restaurant."""
        restaurant = self.get_restaurant_by_id(restaurant_id)
        if not restaurant:
            raise NotFoundException(detail="Restaurant not found.")
        return restaurant.tables

    def get_table_by_id(self, table_id: int) -> Optional[Table]:
        """Retrieves a table by its ID."""
        return self.db_session.get(Table, table_id)

    def update_table(self, table_id: int, table_update: TableUpdate) -> Table:
        """Updates an existing table."""
        table = self.get_table_by_id(table_id)
        if not table:
            raise NotFoundException(detail="Table not found.")

        update_data = table_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(table, key, value)

        if table.capacity is not None and not (2 <= table.capacity <= 12):
            raise BadRequestException(detail="Table capacity must be between 2 and 12.")

        self.db_session.add(table)
        self.db_session.commit()
        self.db_session.refresh(table)
        return table

    def delete_table(self, table_id: int):
        """Deletes a table."""
        table = self.get_table_by_id(table_id)
        if not table:
            raise NotFoundException(detail="Table not found.")
        # TODO: Add check for existing reservations for this table
        self.db_session.delete(table)
        self.db_session.commit()

    def filter_tables(self, restaurant_id: int, capacity: Optional[int] = None, location: Optional[str] = None) -> List[Table]:
        """Filters tables by capacity and/or location for a given restaurant."""
        query = select(Table).where(Table.restaurant_id == restaurant_id)
        if capacity is not None:
            query = query.where(Table.capacity >= capacity)
        if location:
            query = query.where(Table.location == location)
        return self.db_session.exec(query).all()