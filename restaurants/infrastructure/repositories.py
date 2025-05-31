# src/restaurants/infrastructure/repositories.py
from abc import ABC, abstractmethod
from typing import List, Optional
from sqlmodel import Session, select
from restaurants.domain.entities import Restaurant, Table

class AbstractRestaurantRepository(ABC):
    @abstractmethod
    def get_all(self) -> List[Restaurant]:
        pass

    @abstractmethod
    def get_by_id(self, restaurant_id: int) -> Optional[Restaurant]:
        pass

    @abstractmethod
    def create(self, restaurant: Restaurant) -> Restaurant:
        pass

    @abstractmethod
    def update(self, restaurant: Restaurant) -> Restaurant:
        pass

    @abstractmethod
    def delete(self, restaurant_id: int):
        pass

    @abstractmethod
    def get_tables_by_restaurant_id(self, restaurant_id: int) -> List[Table]:
        pass

    @abstractmethod
    def get_table_by_id(self, table_id: int) -> Optional[Table]:
        pass

    @abstractmethod
    def create_table(self, table: Table) -> Table:
        pass

    @abstractmethod
    def update_table(self, table: Table) -> Table:
        pass

    @abstractmethod
    def delete_table(self, table_id: int):
        pass

    @abstractmethod
    def get_table_by_restaurant_id_and_table_number(self, restaurant_id: int, table_number: int) -> Optional[Table]:
        pass


class SqlAlchemyRestaurantRepository(AbstractRestaurantRepository):
    def __init__(self, session: Session):
        self.session = session

    def get_all(self) -> List[Restaurant]:
        return self.session.exec(select(Restaurant)).all()

    def get_by_id(self, restaurant_id: int) -> Optional[Restaurant]:
        return self.session.get(Restaurant, restaurant_id)

    def create(self, restaurant: Restaurant) -> Restaurant:
        self.session.add(restaurant)
        self.session.commit()
        self.session.refresh(restaurant)
        return restaurant

    def update(self, restaurant: Restaurant) -> Restaurant:
        self.session.add(restaurant) # SQLModel handles updates by adding existing objects
        self.session.commit()
        self.session.refresh(restaurant)
        return restaurant

    def delete(self, restaurant_id: int):
        restaurant = self.get_by_id(restaurant_id)
        if restaurant:
            self.session.delete(restaurant)
            self.session.commit()

    def get_tables_by_restaurant_id(self, restaurant_id: int) -> List[Table]:
        return self.session.exec(select(Table).where(Table.restaurant_id == restaurant_id)).all()

    def get_table_by_id(self, table_id: int) -> Optional[Table]:
        return self.session.get(Table, table_id)

    def create_table(self, table: Table) -> Table:
        self.session.add(table)
        self.session.commit()
        self.session.refresh(table)
        return table

    def update_table(self, table: Table) -> Table:
        self.session.add(table)
        self.session.commit()
        self.session.refresh(table)
        return table

    def delete_table(self, table_id: int):
        table = self.get_table_by_id(table_id)
        if table:
            self.session.delete(table)
            self.session.commit()

    def get_table_by_restaurant_id_and_table_number(self, restaurant_id: int, table_number: int) -> Optional[Table]:
        return self.session.exec(
            select(Table).where(
                Table.restaurant_id == restaurant_id,
                Table.table_number == table_number
            )
        ).first()