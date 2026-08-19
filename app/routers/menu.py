from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models import MenuItem, Restaurant, User, UserRole
from app.schemas import MenuItemCreate, MenuItemOut

router = APIRouter(prefix="/restaurants/{restaurant_id}/menu", tags=["Menu"])


def _get_owned_restaurant(restaurant_id: int, current_user: User, db: Session) -> Restaurant:
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if restaurant.owner_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not your restaurant")
    return restaurant


@router.get("/", response_model=List[MenuItemOut])
def list_menu(restaurant_id: int, category: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(MenuItem).filter(MenuItem.restaurant_id == restaurant_id, MenuItem.is_available == True)  # noqa: E712
    if category:
        query = query.filter(MenuItem.category == category)
    return query.all()


@router.post("/", response_model=MenuItemOut, status_code=status.HTTP_201_CREATED)
def add_menu_item(
    restaurant_id: int,
    payload: MenuItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.restaurant_owner, UserRole.admin)),
):
    _get_owned_restaurant(restaurant_id, current_user, db)
    item = MenuItem(**payload.model_dump(), restaurant_id=restaurant_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=MenuItemOut)
def update_menu_item(
    restaurant_id: int,
    item_id: int,
    payload: MenuItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.restaurant_owner, UserRole.admin)),
):
    _get_owned_restaurant(restaurant_id, current_user, db)
    item = db.query(MenuItem).filter(MenuItem.id == item_id, MenuItem.restaurant_id == restaurant_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    for field, value in payload.model_dump().items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu_item(
    restaurant_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.restaurant_owner, UserRole.admin)),
):
    _get_owned_restaurant(restaurant_id, current_user, db)
    item = db.query(MenuItem).filter(MenuItem.id == item_id, MenuItem.restaurant_id == restaurant_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    db.delete(item)
    db.commit()
