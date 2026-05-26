from itertools import count
import logging

logger = logging.getLogger(__name__)
appointment_id_counter = count(102)

AVAILABLE_SLOTS = {
    "cardiology": ["Monday 10:00", "Wednesday 14:30"],
    "orthopedics": ["Tuesday 09:00", "Thursday 12:00"],
    "dermatology": ["Sunday 11:30", "Tuesday 16:00"],
    "family": ["Today 18:00", "Tomorrow 09:30"],
    "children": ["Today 17:00", "Tomorrow 10:30"],
}

APPOINTMENTS = [
    {
        "appointment_id": "100",
        "patient_id": "demo-patient-123",
        "specialty": "cardiology",
        "slot": "Wednesday 14:30",
        "status": "active",
    },
    {
        "appointment_id": "101",
        "patient_id": "demo-patient-123",
        "specialty": "family",
        "slot": "Tomorrow 09:30",
        "status": "active",
    },
]

REFERRALS = {
    "700": "Referral approved.",
    "701": "Referral pending review.",
    "702": "Referral rejected. Please contact the clinic.",
}

FORM17_REQUESTS = {
    "800": "Form 17 approved.",
    "801": "Form 17 waiting for documents.",
    "802": "Form 17 rejected.",
}


def get_available_appointments(specialty: str) -> list[str]:
    return AVAILABLE_SLOTS.get(specialty.lower(), [])


def book_appointment(patient_id: str, specialty: str, slot: str) -> str:
    available_slots = AVAILABLE_SLOTS.get(specialty.lower(), [])

    if slot not in available_slots:
        return "המועד שבחרת כבר לא זמין."

    appointment_id = str(next(appointment_id_counter))

    APPOINTMENTS.append({
        "appointment_id": appointment_id,
        "patient_id": patient_id,
        "specialty": specialty,
        "slot": slot,
        "status": "active",
    })

    AVAILABLE_SLOTS[specialty.lower()] = [
        available_slot
        for available_slot in available_slots
        if available_slot != slot
    ]

    return f"התור נקבע בהצלחה. מספר התור הוא {appointment_id}."


def cancel_appointment(appointment_id: str) -> str:
    for appointment in APPOINTMENTS:
        if appointment["appointment_id"] == appointment_id:
            if appointment["status"] == "cancelled":
                return "התור כבר מבוטל."

            appointment["status"] = "cancelled"
            return f"תור {appointment_id} בוטל בהצלחה."

    return "התור לא נמצא."


def get_patient_appointments(patient_id: str):
    logger.info(f"GET PATIENT APPOINTMENTS | patient_id={patient_id}")
    logger.info(f"CURRENT APPOINTMENTS | appointments={APPOINTMENTS}")
    return [
        appointment
        for appointment in APPOINTMENTS
        if appointment["patient_id"] == patient_id
        and appointment["status"] == "active"
    ]


def get_referral_status(referral_id: str) -> str:
    return REFERRALS.get(referral_id, "Referral not found.")


def get_form17_status(form17_id: str) -> str:
    return FORM17_REQUESTS.get(form17_id, "Form 17 not found.")