"""Carousel Control Router.
Provides API endpoints for slot-based chip feeding.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from devices.carousel import CarouselDevice

router = APIRouter(prefix="/api/carousel", tags=["carousel"])
carousel_device = CarouselDevice(slot_count=10)


class FeedSlotRequest(BaseModel):
    """Request model for feeding a chip from one carousel slot."""

    slot_number: int = Field(..., ge=1, le=10, description="Carousel slot number")


@router.get("/status")
async def get_carousel_status() -> dict:
    """Get current carousel status."""
    status = carousel_device.get_device_status()
    return {
        "ok": True,
        "implemented": True,
        "message": "Carousel module ready for slot-based feeding",
        **status,
    }


@router.post("/feed")
async def feed_slot(request: FeedSlotRequest) -> dict:
    """Feed one chip from the given slot number."""
    result = carousel_device.feed_from_slot(request.slot_number)
    status = carousel_device.get_device_status()
    return {
        "ok": True,
        "implemented": True,
        "message": result["message"],
        "slot_number": result["slot_number"],
        "feed_count": result["feed_count"],
        "last_fed_slot": status["last_fed_slot"],
    }
