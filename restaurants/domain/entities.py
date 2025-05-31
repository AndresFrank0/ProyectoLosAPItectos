# src/restaurants/domain/entities.py
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from datetime import time

class RestaurantBase(SQLModel):
    name: str = Field(index=True, unique=True)
    location: str
    opening_time: time
    closing_time: time

class Restaurant(RestaurantBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tables: List["Table"] = Relationship(back_populates="restaurant")

class RestaurantCreate(RestaurantBase):
    pass

class RestaurantUpdate(SQLModel):
    name: Optional[str] = None
    location: Optional[str] = None
    opening_time: Optional[time] = None
    closing_time: Optional[time] = None

class RestaurantPublic(RestaurantBase):
    id: int

class TableBase(SQLModel):
    capacity: int
    location: str # e.g., "terraza", "interior"
    table_number: int

class Table(TableBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    restaurant_id: int = Field(foreign_key="restaurant.id")
    restaurant: Restaurant = Relationship(back_populates="tables")

class TableCreate(TableBase):
    pass

class TableUpdate(SQLModel):
    capacity: Optional[int] = None
    location: Optional[str] = None

class TablePublic(TableBase):
    id: int
    restaurant_id: int