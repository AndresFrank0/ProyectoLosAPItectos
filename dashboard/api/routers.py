# src/dashboard/api/routers.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import List, Dict, Any
from shared.dependencies import get_current_active_user, require_role
from dashboard.domain.services import DashboardService
from shared.database import get_session
from auth.api.routers import require_role

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/reservations", response_model=Dict[str, Any],
            dependencies=[Depends(require_role(["admin"]))])
def get_reservations_stats(db: Session = Depends(get_session)):
    """Provides total reservations by day/week (Admin only)."""
    service = DashboardService(db)
    try:
        daily_stats = service.get_reservations_by_period("day")
        weekly_stats = service.get_reservations_by_period("week")
        return {"daily_reservations": daily_stats, "weekly_reservations": weekly_stats}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/dishes", response_model=List[Dict[str, Any]],
            dependencies=[Depends(require_role(["admin"]))])
def get_top_dishes(db: Session = Depends(get_session)):
    """Provides the top 5 most pre-ordered dishes (Admin only)."""
    service = DashboardService(db)
    try:
        top_dishes = service.get_top_preordered_dishes()
        return top_dishes
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/occupancy", response_model=List[Dict[str, Any]],
            dependencies=[Depends(require_role(["admin"]))])
def get_occupancy_stats(db: Session = Depends(get_session)):
    """Provides occupancy percentage per restaurant (Admin only)."""
    service = DashboardService(db)
    try:
        occupancy_data = service.get_restaurant_occupancy()
        return occupancy_data
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))