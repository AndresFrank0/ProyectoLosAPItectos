# src/main.py
from fastapi import FastAPI, Depends
from sqlmodel import Session
from contextlib import asynccontextmanager
from auth.api import routers
from shared.database import SQLModel, engine # Import SQLModel and engine
from shared.database import create_db_and_tables, get_session, engine
from auth.api import routers as auth_routers
from restaurants.api import routers as restaurants_routers
from menu.api import routers as menu_routers
from reservations.api import routers as reservations_routers
from dashboard.api import routers as dashboard_routers


# Event handler for application startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (for development)
    print("Creating database tables...")
    create_db_and_tables()
    print("Database tables created.")
    yield
    # Clean up resources on shutdown (if needed)
    print("Application shutdown.")

app = FastAPI(
    title="El Buen Sabor API",
    description="Backend for a restaurant reservation system.",
    version="0.1.0",
    lifespan=lifespan # Attach the lifespan context manager
)

# Include routers from each module
app.include_router(auth_routers.router)
app.include_router(restaurants_routers.router)
app.include_router(menu_routers.router)
app.include_router(reservations_routers.router)
app.include_router(dashboard_routers.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to El Buen Sabor API!"}