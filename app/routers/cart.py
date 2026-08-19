from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import CartItem, MenuItem, User
from app.schemas import CartItemCreate, CartItemOut

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("/", response_model=List[CartItemOut])
def view_cart(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(CartItem).filter(CartItem.user_id == current_user.id).all()


@router.post("/", response_model=CartItemOut, status_code=status.HTTP_201_CREATED)
def add_to_cart(
    payload: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    menu_item = db.query(MenuItem).filter(MenuItem.id == payload.menu_item_id, MenuItem.is_available == True).first()  # noqa: E712
    if not menu_item:
        raise HTTPException(status_code=404, detail="Menu item not found or unavailable")

    # Enforce single-restaurant cart: clear cart if adding from a different restaurant
    existing_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    if existing_items:
        first_restaurant_id = existing_items[0].menu_item.restaurant_id
        if first_restaurant_id != menu_item.restaurant_id:
            raise HTTPException(
                status_code=400,
                detail="Your cart contains items from another restaurant. Clear it first or checkout.",
            )

    cart_item = (
        db.query(CartItem)
        .filter(CartItem.user_id == current_user.id, CartItem.menu_item_id == payload.menu_item_id)
        .first()
    )
    if cart_item:
        cart_item.quantity += payload.quantity
    else:
        cart_item = CartItem(user_id=current_user.id, menu_item_id=payload.menu_item_id, quantity=payload.quantity)
        db.add(cart_item)

    db.commit()
    db.refresh(cart_item)
    return cart_item


@router.delete("/{cart_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_cart(
    cart_item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart_item = (
        db.query(CartItem).filter(CartItem.id == cart_item_id, CartItem.user_id == current_user.id).first()
    )
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    db.delete(cart_item)
    db.commit()


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def clear_cart(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
    db.commit()
