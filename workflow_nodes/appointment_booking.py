"""Appointment booking nodes.

Note:
For maximum backward-compatibility (no behavior change), we currently re-export the
existing implementations from `nodes_booking.py`.
"""

from nodes_booking import book_appointment_node, select_appointment_slot_node

__all__ = [
    "book_appointment_node",
    "select_appointment_slot_node",
]
