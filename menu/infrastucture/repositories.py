# src/menu/infrastructure/repositories.py
from abc import ABC, abstractmethod
from typing import List, Optional
from sqlmodel import Session, select
from menu.domain.entities import MenuItem

class AbstractMenuRepository(ABC):
    @abstractmethod
    def get_by_id(self, item_id: int) -> Optional[MenuItem]:
        pass

    @abstractmethod
    def get_by_restaurant_id_and_name(self, restaurant_id: int, name: str) -> Optional[MenuItem]:
        pass

    @abstractmethod
    def get_all_by_restaurant_id(self, restaurant_id: int) -> List[MenuItem]:
        pass

    @abstractmethod
    def create(self, menu_item: MenuItem) -> MenuItem:
        pass

    @abstractmethod
    def update(self, menu_item: MenuItem) -> MenuItem:
        pass

    @abstractmethod
    def delete(self, item_id: int):
        pass

class SqlAlchemyMenuRepository(AbstractMenuRepository):
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, item_id: int) -> Optional[MenuItem]:
        return self.session.get(MenuItem, item_id)

    def get_by_restaurant_id_and_name(self, restaurant_id: int, name: str) -> Optional[MenuItem]:
        return self.session.exec(
            select(MenuItem).where(
                MenuItem.restaurant_id == restaurant_id,
                MenuItem.name == name
            )
        ).first()

    def get_all_by_restaurant_id(self, restaurant_id: int) -> List[MenuItem]:
        return self.session.exec(select(MenuItem).where(MenuItem.restaurant_id == restaurant_id)).all()

    def create(self, menu_item: MenuItem) -> MenuItem:
        self.session.add(menu_item)
        self.session.commit()
        self.session.refresh(menu_item)
        return menu_item

    def update(self, menu_item: MenuItem) -> MenuItem:
        self.session.add(menu_item)
        self.session.commit()
        self.session.refresh(menu_item)
        return menu_item

    def delete(self, item_id: int):
        menu_item = self.get_by_id(item_id)
        if menu_item:
            self.session.delete(menu_item)
            self.session.commit()