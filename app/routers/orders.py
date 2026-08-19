from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models import CartItem, Order, OrderItem, OrderStatus, Restaurant, User, UserRole
from app.schemas import OrderCreate, OrderOut, OrderStatusUpdate

router = APIRouter(prefix="/orders", tags=["Orders"])

# Valid forward transitions for order status
NEXT_STATUS = {
    OrderStatus.pending: {OrderStatus.confirmed, OrderStatus.cancelled},
    OrderStatus.confirmed: {OrderStatus.preparing, OrderStatus.cancelled},
    OrderStatus.preparing: {OrderStatus.out_for_delivery},
    OrderStatus.out_for_delivery: {OrderStatus.delivered},
    OrderStatus.delivered: set(),
    OrderStatus.cancelled: set(),
}


@router.post("/checkout", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def checkout(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    restaurant_id = cart_items[0].menu_item.restaurant_id
    total = sum(ci.menu_item.price * ci.quantity for ci in cart_items)

    order = Order(
        customer_id=current_user.id,
        restaurant_id=restaurant_id,
        delivery_address=payload.delivery_address,
        total_amount=total,
        status=OrderStatus.pending,
    )
    db.add(order)
    db.flush()  # get order.id before adding items

    for ci in cart_items:
        db.add(
            OrderItem(
                order_id=order.id,
                menu_item_id=ci.menu_item_id,
                item_name=ci.menu_item.name,
                unit_price=ci.menu_item.price,
                quantity=ci.quantity,
            )
        )

    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
    db.commit()
    db.refresh(order)
    return order


@router.get("/my", response_model=List[OrderOut])
def my_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Order).filter(Order.customer_id == current_user.id).order_by(Order.created_at.desc()).all()


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    is_owner_of_restaurant = order.restaurant.owner_id == current_user.id
    if order.customer_id != current_user.id and not is_owner_of_restaurant and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not authorized to view this order")
    return order


@router.get("/restaurant/{restaurant_id}", response_model=List[OrderOut])
def restaurant_orders(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.restaurant_owner, UserRole.admin)),
):
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    if restaurant.owner_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not your restaurant")

    return (
        db.query(Order)
        .filter(Order.restaurant_id == restaurant_id)
        .order_by(Order.created_at.desc())
        .all()
    )


@router.patch("/{order_id}/status", response_model=OrderOut)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.restaurant_owner, UserRole.admin)),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.restaurant.owner_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not your restaurant's order")

    if payload.status not in NEXT_STATUS[order.status] and current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from {order.status.value} to {payload.status.value}",
        )

    order.status = payload.status
    db.commit()
    db.refresh(order)
    return order
