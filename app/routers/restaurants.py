from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models import Restaurant, User, UserRole
from app.schemas import RestaurantCreate, RestaurantOut

router = APIRouter(prefix="/restaurants", tags=["Restaurants"])


@router.get("/", response_model=List[RestaurantOut])
def list_restaurants(db: Session = Depends(get_db)):
    return db.query(Restaurant).filter(Restaurant.is_open == True).all()  # noqa: E712


@router.get("/{restaurant_id}", response_model=RestaurantOut)
def get_restaurant(restaurant_id: int, db: Session = Depends(get_db)):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant


@router.post("/", response_model=RestaurantOut, status_code=status.HTTP_201_CREATED)
def create_restaurant(
    payload: RestaurantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.restaurant_owner, UserRole.admin)),
):
    restaurant = Restaurant(**payload.model_dump(), owner_id=current_user.id)
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    return restaurant


@router.patch("/{restaurant_id}/toggle-open", response_model=RestaurantOut)
def toggle_open(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.restaurant_owner, UserRole.admin)),
):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if restaurant.owner_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not your restaurant")

    restaurant.is_open = not restaurant.is_open
    db.commit()
    db.refresh(restaurant)
    return restaurant
