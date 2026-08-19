from fastapi import FastAPI

from app.database import Base, engine
from app.routers import auth, cart, menu, orders, restaurants

# Create tables (use Alembic migrations in production instead)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Food Ordering API",
    description="Backend for a food ordering platform: restaurants, menus, cart, and orders.",
    version="1.0.0",
)

app.include_router(auth.router)
app.include_router(restaurants.router)
app.include_router(menu.router)
app.include_router(cart.router)
app.include_router(orders.router)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok"}
