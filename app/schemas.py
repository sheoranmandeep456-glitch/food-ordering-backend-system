from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from app.models import OrderStatus, UserRole


# ---------- Auth / Users ----------
class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(min_length=8)
    role: UserRole = UserRole.customer
    phone: Optional[str] = None


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: UserRole
    phone: Optional[str] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Restaurants ----------
class RestaurantCreate(BaseModel):
    name: str
    description: Optional[str] = None
    address: Optional[str] = None


class RestaurantOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    address: Optional[str]
    is_open: bool

    class Config:
        from_attributes = True


# ---------- Menu items ----------
class MenuItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(gt=0)
    category: Optional[str] = None
    is_available: bool = True


class MenuItemOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    category: Optional[str]
    is_available: bool
    restaurant_id: int

    class Config:
        from_attributes = True


# ---------- Cart ----------
class CartItemCreate(BaseModel):
    menu_item_id: int
    quantity: int = Field(gt=0, default=1)


class CartItemOut(BaseModel):
    id: int
    menu_item: MenuItemOut
    quantity: int

    class Config:
        from_attributes = True


# ---------- Orders ----------
class OrderCreate(BaseModel):
    delivery_address: str


class OrderItemOut(BaseModel):
    item_name: str
    unit_price: float
    quantity: int

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    restaurant_id: int
    status: OrderStatus
    delivery_address: str
    total_amount: float
    created_at: datetime
    items: List[OrderItemOut]

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
