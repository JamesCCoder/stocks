from fastapi import APIRouter
from app.utils.globals import (
    total_stocks,
    completed_count,
    success_count,
    failure_count,
    no_update_needed_count,
)

router = APIRouter()

@router.get("/summary")
async def summary():
    return {
        "total_completed": completed_count,
        "successful_downloads": success_count,
        "failed_downloads": failure_count,
        "no_update_needed": no_update_needed_count
    }
