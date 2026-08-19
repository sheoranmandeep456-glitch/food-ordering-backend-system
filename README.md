# Food Ordering Backend (FastAPI)

A backend for a food ordering platform: user auth, restaurants, menus, cart, and order lifecycle management.

## Stack
- **FastAPI** — web framework
- **SQLAlchemy** — ORM (SQLite by default, swap to Postgres via `DATABASE_URL`)
- **Pydantic** — request/response validation
- **JWT (python-jose)** + **Passlib (bcrypt)** — authentication

## Project structure
```
app/
  main.py          # FastAPI app, router registration
  config.py        # settings (env vars)
  database.py      # SQLAlchemy engine/session
  models.py        # ORM models (User, Restaurant, MenuItem, CartItem, Order, OrderItem)
  schemas.py        # Pydantic request/response schemas
  auth.py          # password hashing, JWT create/decode
  dependencies.py  # get_current_user, role-based guards
  routers/
    auth.py         # POST /auth/register, /auth/login
    restaurants.py  # CRUD for restaurants
    menu.py         # CRUD for menu items (nested under restaurants)
    cart.py         # add/view/remove cart items
    orders.py       # checkout, order history, status transitions
```

## Data model
- **User**: role is one of `customer`, `restaurant_owner`, `admin`.
- **Restaurant**: owned by a `restaurant_owner`.
- **MenuItem**: belongs to a restaurant.
- **CartItem**: per-user, restricted to a single restaurant at a time (checkout clears it).
- **Order** / **OrderItem**: created at checkout; item name/price are snapshotted so historical orders stay accurate even if the menu changes later.

## Order status flow
```
pending -> confirmed -> preparing -> out_for_delivery -> delivered
   |            |
   v            v
cancelled   cancelled
```
Transitions are validated server-side (`orders.py::NEXT_STATUS`) so a restaurant owner can't skip states like `pending -> delivered`. Admins can override.

## Setup
```bash
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # edit SECRET_KEY at minimum
uvicorn app.main:app --reload
```
Visit `http://127.0.0.1:8000/docs` for interactive Swagger UI.

## Typical flow
1. `POST /auth/register` — create a customer and a restaurant_owner account.
2. `POST /auth/login` — get a JWT (`OAuth2PasswordRequestForm`: send `username`=email, `password`).
3. As the owner: `POST /restaurants/`, then `POST /restaurants/{id}/menu/` to add items.
4. As the customer: `GET /restaurants/`, `GET /restaurants/{id}/menu/`, `POST /cart/` to add items.
5. `POST /orders/checkout` with a delivery address — converts cart to an order.
6. As the owner: `PATCH /orders/{id}/status` to move the order through its lifecycle.
7. Customer polls `GET /orders/my` or `GET /orders/{id}` for status.

## What's included vs. what you'd add for production
**Included**: auth, role-based authorization, restaurant/menu CRUD, cart, checkout with price snapshotting, order status state machine.

**Not included (natural next steps)**:
- Payment gateway integration (Stripe/Razorpay webhook handling)
- Real-time order tracking (WebSockets or SSE for live status push to the customer)
- Alembic migrations (scaffolding present in `requirements.txt`, migration scripts not generated)
- Rate limiting, request logging, structured error responses
- Image uploads for menu items / restaurants (e.g. S3 + presigned URLs)
- Search/filtering (by cuisine, price range, rating) and pagination on list endpoints
- Reviews/ratings model
- Background job queue (Celery/RQ) for notification emails, order timeout handling
