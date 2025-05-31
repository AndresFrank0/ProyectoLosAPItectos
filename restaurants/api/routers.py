# src/restaurants/api/routers.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List, Optional
from shared.dependencies import get_current_active_user, require_role
from restaurants.domain.entities import (
    RestaurantCreate, RestaurantPublic, RestaurantUpdate,
    TableCreate, TablePublic, TableUpdate
)
from restaurants.domain.services import RestaurantService
from shared.database import get_session
from auth.api.routers import require_role
from shared.exceptions import NotFoundException, ConflictException, BadRequestException

router = APIRouter(prefix="/restaurants", tags=["restaurants"])

@router.post("/", response_model=RestaurantPublic, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_role(["admin"]))])
def create_restaurant(restaurant_create: RestaurantCreate, db: Session = Depends(get_session)):
    """Creates a new restaurant (Admin only)."""
    service = RestaurantService(db)
    try:
        restaurant = service.create_restaurant(restaurant_create)
        return restaurant
    except (BadRequestException, ConflictException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST if isinstance(e, BadRequestException) else status.HTTP_409_CONFLICT, detail=e.detail)

@router.get("/", response_model=List[RestaurantPublic])
def get_restaurants(db: Session = Depends(get_session)):
    """Retrieves all restaurants."""
    service = RestaurantService(db)
    return service.get_restaurants()

@router.get("/{restaurant_id}", response_model=RestaurantPublic)
def get_restaurant(restaurant_id: int, db: Session = Depends(get_session)):
    """Retrieves a single restaurant by ID."""
    service = RestaurantService(db)
    restaurant = service.get_restaurant_by_id(restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    return restaurant

@router.put("/{restaurant_id}", response_model=RestaurantPublic,
            dependencies=[Depends(require_role(["admin"]))])
def update_restaurant(restaurant_id: int, restaurant_update: RestaurantUpdate, db: Session = Depends(get_session)):
    """Updates an existing restaurant (Admin only)."""
    service = RestaurantService(db)
    try:
        restaurant = service.update_restaurant(restaurant_id, restaurant_update)
        return restaurant
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except BadRequestException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.detail)

@router.delete("/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_role(["admin"]))])
def delete_restaurant(restaurant_id: int, db: Session = Depends(get_session)):
    """Deletes a restaurant (Admin only)."""
    service = RestaurantService(db)
    try:
        service.delete_restaurant(restaurant_id)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except BadRequestException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.detail)


@router.post("/{restaurant_id}/tables", response_model=TablePublic, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_role(["admin"]))])
def create_table(restaurant_id: int, table_create: TableCreate, db: Session = Depends(get_session)):
    """Creates a new table for a restaurant (Admin only)."""
    service = RestaurantService(db)
    try:
        table = service.create_table(restaurant_id, table_create)
        return table
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except (BadRequestException, ConflictException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST if isinstance(e, BadRequestException) else status.HTTP_409_CONFLICT, detail=e.detail)

@router.get("/{restaurant_id}/tables", response_model=List[TablePublic])
def get_tables_by_restaurant(restaurant_id: int, db: Session = Depends(get_session),
                             capacity: Optional[int] = None, location: Optional[str] = None):
    """Retrieves tables for a restaurant, with optional filtering by capacity and location."""
    service = RestaurantService(db)
    try:
        if capacity or location:
            tables = service.filter_tables(restaurant_id, capacity, location)
        else:
            tables = service.get_tables_by_restaurant(restaurant_id)
        return tables
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)

@router.put("/tables/{table_id}", response_model=TablePublic,
            dependencies=[Depends(require_role(["admin"]))])
def update_table(table_id: int, table_update: TableUpdate, db: Session = Depends(get_session)):
    """Updates an existing table (Admin only)."""
    service = RestaurantService(db)
    try:
        table = service.update_table(table_id, table_update)
        return table
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except BadRequestException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.detail)

@router.delete("/tables/{table_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_role(["admin"]))])
def delete_table(table_id: int, db: Session = Depends(get_session)):
    """Deletes a table (Admin only)."""
    service = RestaurantService(db)
    try:
        service.delete_table(table_id)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    # TODO: Add check for existing reservations for this table when implementing reservations module.