"""Carousel Device - 10-slot chip feed module."""

from typing import Any, Dict

from devices.base_device import BaseDevice


class CarouselDevice(BaseDevice):
    """Carousel feeder that accepts a slot number and performs feed action."""

    def __init__(self, slot_count: int = 10):
        super().__init__("Carousel Feeder")
        self.slot_count = slot_count
        self.last_requested_slot: int | None = None
        self.last_fed_slot: int | None = None
        self.feed_count = 0
        self.is_busy = False

    def get_device_type(self) -> str:
        return "carousel"

    def feed_from_slot(self, slot_number: int) -> Dict[str, Any]:
        """Queue/process a feed from one slot.

        This currently updates software state only. Hardware integration can be
        added later in this method without changing API contracts.
        """
        if not isinstance(slot_number, int):
            raise ValueError("slot_number must be an integer")
        if slot_number < 1 or slot_number > self.slot_count:
            raise ValueError(f"slot_number must be between 1 and {self.slot_count}")

        with self.lock:
            self.is_busy = True
            self.last_requested_slot = slot_number
            self.status_message = f"Feeding chip from slot {slot_number}"

        # Placeholder for future hardware feed command.
        with self.lock:
            self.last_fed_slot = slot_number
            self.feed_count += 1
            self.is_busy = False
            self.is_on = True
            self.status_message = f"Feed complete from slot {slot_number}"
            return {
                "slot_number": slot_number,
                "feed_count": self.feed_count,
                "message": self.status_message,
            }

    def get_device_status(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "device_type": self.get_device_type(),
                "name": self.name,
                "is_on": self.is_on,
                "status": self.status_message,
                "slot_count": self.slot_count,
                "is_busy": self.is_busy,
                "last_requested_slot": self.last_requested_slot,
                "last_fed_slot": self.last_fed_slot,
                "feed_count": self.feed_count,
            }
