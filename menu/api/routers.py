# src/menu/api/routers.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List
from shared.dependencies import get_current_active_user, require_role
from menu.domain.entities import MenuItemCreate, MenuItemPublic, MenuItemUpdate
from menu.domain.services import MenuService
from shared.database import get_session
from auth.api.routers import require_role
from shared.exceptions import NotFoundException, ConflictException, BadRequestException

router = APIRouter(prefix="/menu", tags=["menu"])

@router.post("/{restaurant_id}/items", response_model=MenuItemPublic, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_role(["admin"]))])
def create_menu_item(restaurant_id: int, menu_item_create: MenuItemCreate, db: Session = Depends(get_session)):
    """Creates a new menu item for a restaurant (Admin only)."""
    service = MenuService(db)
    try:
        menu_item = service.create_menu_item(restaurant_id, menu_item_create)
        return menu_item
    except (BadRequestException, ConflictException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST if isinstance(e, BadRequestException) else status.HTTP_409_CONFLICT, detail=e.detail)

@router.get("/{restaurant_id}/items", response_model=List[MenuItemPublic])
def get_menu_items(restaurant_id: int, db: Session = Depends(get_session)):
    """Retrieves all menu items for a specific restaurant."""
    service = MenuService(db)
    return service.get_menu_items_by_restaurant(restaurant_id)

@router.put("/items/{item_id}", response_model=MenuItemPublic,
            dependencies=[Depends(require_role(["admin"]))])
def update_menu_item(item_id: int, menu_item_update: MenuItemUpdate, db: Session = Depends(get_session)):
    """Updates an existing menu item (Admin only)."""
    service = MenuService(db)
    try:
        menu_item = service.update_menu_item(item_id, menu_item_update)
        return menu_item
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except (BadRequestException, ConflictException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST if isinstance(e, BadRequestException) else status.HTTP_409_CONFLICT, detail=e.detail)

@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_role(["admin"]))])
def delete_menu_item(item_id: int, db: Session = Depends(get_session)):
    """Deletes (soft delete) a menu item (Admin only)."""
    service = MenuService(db)
    try:
        service.delete_menu_item(item_id)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except BadRequestException as e: # In case future reservations exist
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.detail)