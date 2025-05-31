# src/menu/domain/services.py
from typing import List, Optional
from sqlmodel import Session, select
from menu.domain.entities import MenuItem, MenuItemCreate, MenuItemUpdate
from shared.exceptions import NotFoundException, ConflictException, BadRequestException

VALID_MENU_CATEGORIES = ["Entrada", "Principal", "Postre", "Bebida"]

class MenuService:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create_menu_item(self, restaurant_id: int, menu_item_create: MenuItemCreate) -> MenuItem:
        """Creates a new menu item for a restaurant."""
        if menu_item_create.category not in VALID_MENU_CATEGORIES:
            raise BadRequestException(detail=f"Invalid category. Must be one of {VALID_MENU_CATEGORIES}")

        existing_item = self.db_session.query(MenuItem).filter(
            MenuItem.restaurant_id == restaurant_id,
            MenuItem.name == menu_item_create.name
        ).first()
        if existing_item:
            raise ConflictException(detail="Menu item with this name already exists for this restaurant.")

        db_menu_item = MenuItem(restaurant_id=restaurant_id, **menu_item_create.dict())
        self.db_session.add(db_menu_item)
        self.db_session.commit()
        self.db_session.refresh(db_menu_item)
        return db_menu_item

    def get_menu_items_by_restaurant(self, restaurant_id: int) -> List[MenuItem]:
        """Retrieves all menu items for a given restaurant."""
        return self.db_session.exec(select(MenuItem).where(MenuItem.restaurant_id == restaurant_id)).all()

    def get_menu_item_by_id(self, item_id: int) -> Optional[MenuItem]:
        """Retrieves a menu item by its ID."""
        return self.db_session.get(MenuItem, item_id)

    def update_menu_item(self, item_id: int, menu_item_update: MenuItemUpdate) -> MenuItem:
        """Updates an existing menu item."""
        menu_item = self.get_menu_item_by_id(item_id)
        if not menu_item:
            raise NotFoundException(detail="Menu item not found.")

        update_data = menu_item_update.dict(exclude_unset=True)
        if "category" in update_data and update_data["category"] not in VALID_MENU_CATEGORIES:
            raise BadRequestException(detail=f"Invalid category. Must be one of {VALID_MENU_CATEGORIES}")

        # Check for name uniqueness if name is being updated
        if "name" in update_data and update_data["name"] != menu_item.name:
            existing_item = self.db_session.query(MenuItem).filter(
                MenuItem.restaurant_id == menu_item.restaurant_id,
                MenuItem.name == update_data["name"]
            ).first()
            if existing_item and existing_item.id != item_id:
                raise ConflictException(detail="Menu item with this name already exists for this restaurant.")

        for key, value in update_data.items():
            setattr(menu_item, key, value)

        self.db_session.add(menu_item)
        self.db_session.commit()
        self.db_session.refresh(menu_item)
        return menu_item

    def delete_menu_item(self, item_id: int):
        """Deletes a menu item (soft delete by marking as unavailable)."""
        menu_item = self.get_menu_item_by_id(item_id)
        if not menu_item:
            raise NotFoundException(detail="Menu item not found.")

        # TODO: Check for associated future reservations. For now, just mark as unavailable.
        menu_item.is_available = False
        self.db_session.add(menu_item)
        self.db_session.commit()
        self.db_session.refresh(menu_item)
        # Or, if you truly want to delete and ensure no future reservations:
        # if not self.has_future_reservations(item_id):
        #    self.db_session.delete(menu_item)
        #    self.db_session.commit()
        # else:
        #    menu_item.is_available = False
        #    self.db_session.add(menu_item)
        #    self.db_session.commit()
        #    self.db_session.refresh(menu_item)
        #    raise BadRequestException(detail="Cannot delete menu item with future reservations. Marked as unavailable instead.")

    # Helper for checking if a menu item is part of future reservations
    # This would require integration with the Reservations module.
    # def has_future_reservations(self, item_id: int) -> bool:
    #     # Placeholder logic. Implement this after Reservations module is defined.
    #     # You would query the Reservation_MenuItem_Link table for this item with future reservation dates.
    #     return False