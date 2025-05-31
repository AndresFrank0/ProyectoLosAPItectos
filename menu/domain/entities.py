# src/menu/domain/entities.py
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship

class MenuItemBase(SQLModel):
    name: str = Field(index=True)
    description: str
    category: str # "Entrada", "Principal", "Postre", "Bebida"
    image_url: Optional[str] = None
    is_available: bool = True # For soft deletion

class MenuItem(MenuItemBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    restaurant_id: int = Field(foreign_key="restaurant.id")

class MenuItemCreate(MenuItemBase):
    pass

class MenuItemUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    is_available: Optional[bool] = None

class MenuItemPublic(MenuItemBase):
    id: int
    restaurant_id: int