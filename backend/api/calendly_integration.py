from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta, date as dt_date, time as dt_time
from typing import List, Dict, Any
import json
from pathlib import Path
import random
import string

from backend.models.schemas import (
    AvailabilityRequest, 
    AvailabilityResponse, 
    BookingRequest, 
    BookingResponse,
    TimeSlot,
    AppointmentType,
    AppointmentDuration
)

router = APIRouter(prefix="/api/calendly", tags=["calendly"])

DOCTOR_SCHEDULE_PATH = Path("data/doctor_schedule.json")
APPOINTMENTS_STORAGE_PATH = Path("data/appointments.json")

APPOINTMENT_DURATIONS = AppointmentDuration()


def load_doctor_schedule() -> Dict[str, Any]:
    with open(DOCTOR_SCHEDULE_PATH, 'r') as f:
        return json.load(f)


def load_appointments() -> List[Dict[str, Any]]:
    if APPOINTMENTS_STORAGE_PATH.exists():
        with open(APPOINTMENTS_STORAGE_PATH, 'r') as f:
            return json.load(f)
    return []


def save_appointment(appointment: Dict[str, Any]) -> None:
    appointments = load_appointments()
    appointments.append(appointment)
    APPOINTMENTS_STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(APPOINTMENTS_STORAGE_PATH, 'w') as f:
        json.dump(appointments, f, indent=2)


def generate_confirmation_code() -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def generate_booking_id() -> str:
    timestamp = datetime.now().strftime("%Y%m%d")
    random_suffix = ''.join(random.choices(string.digits, k=4))
    return f"APPT-{timestamp}-{random_suffix}"


def get_day_of_week(date_str: str) -> str:
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return date_obj.strftime("%A").lower()


def time_to_minutes(time_str: str) -> int:
    hours, minutes = map(int, time_str.split(':'))
    return hours * 60 + minutes


def minutes_to_time(minutes: int) -> str:
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


def is_slot_booked(date_str: str, start_time: str, end_time: str, 
                   booked_appointments: List[Dict[str, Any]]) -> bool:
    start_minutes = time_to_minutes(start_time)
    end_minutes = time_to_minutes(end_time)
    
    for appt in booked_appointments:
        if appt['date'] != date_str:
            continue
        
        appt_start = time_to_minutes(appt['start_time'])
        appt_end = time_to_minutes(appt['end_time'])
        
        if not (end_minutes <= appt_start or start_minutes >= appt_end):
            return True
    
    return False


@router.get("/availability", response_model=AvailabilityResponse)
async def get_availability(date: str, appointment_type: AppointmentType):
    try:
        request_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    if request_date < dt_date.today():
        raise HTTPException(status_code=400, detail="Cannot book appointments in the past")
    
    schedule = load_doctor_schedule()
    day_of_week = get_day_of_week(date)
    
    if day_of_week not in schedule['working_hours'] or schedule['working_hours'][day_of_week] is None:
        return AvailabilityResponse(
            date=date,
            available_slots=[],
            appointment_type=appointment_type
        )
    
    if date in schedule.get('blocked_dates', []):
        return AvailabilityResponse(
            date=date,
            available_slots=[],
            appointment_type=appointment_type
        )
    
    work_hours = schedule['working_hours'][day_of_week]
    start_time = time_to_minutes(work_hours['start'])
    end_time = time_to_minutes(work_hours['end'])
    
    lunch_start = time_to_minutes(schedule['lunch_break']['start'])
    lunch_end = time_to_minutes(schedule['lunch_break']['end'])
    
    slot_interval = schedule['appointment_slot_interval']
    duration = getattr(APPOINTMENT_DURATIONS, appointment_type.value)
    
    all_booked = schedule['booked_appointments'] + load_appointments()
    
    available_slots = []
    current_time = start_time
    
    while current_time + duration <= end_time:
        slot_start = current_time
        slot_end = current_time + duration
        
        is_during_lunch = not (slot_end <= lunch_start or slot_start >= lunch_end)
        
        if not is_during_lunch:
            start_time_str = minutes_to_time(slot_start)
            end_time_str = minutes_to_time(slot_end)
            
            is_available = not is_slot_booked(date, start_time_str, end_time_str, all_booked)
            
            available_slots.append(TimeSlot(
                start_time=start_time_str,
                end_time=end_time_str,
                available=is_available
            ))
        
        current_time += slot_interval
    
    return AvailabilityResponse(
        date=date,
        available_slots=available_slots,
        appointment_type=appointment_type
    )


@router.post("/book", response_model=BookingResponse)
async def book_appointment(booking: BookingRequest):
    try:
        request_date = datetime.strptime(booking.date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    if request_date < dt_date.today():
        raise HTTPException(status_code=400, detail="Cannot book appointments in the past")
    
    schedule = load_doctor_schedule()
    day_of_week = get_day_of_week(booking.date)
    
    if day_of_week not in schedule['working_hours'] or schedule['working_hours'][day_of_week] is None:
        raise HTTPException(status_code=400, detail=f"Clinic is closed on {day_of_week}s")
    
    if booking.date in schedule.get('blocked_dates', []):
        raise HTTPException(status_code=400, detail="This date is not available for appointments")
    
    duration = getattr(APPOINTMENT_DURATIONS, booking.appointment_type.value)
    start_minutes = time_to_minutes(booking.start_time)
    end_time_str = minutes_to_time(start_minutes + duration)
    
    all_booked = schedule['booked_appointments'] + load_appointments()
    
    if is_slot_booked(booking.date, booking.start_time, end_time_str, all_booked):
        raise HTTPException(status_code=409, detail="This time slot is no longer available")
    
    booking_id = generate_booking_id()
    confirmation_code = generate_confirmation_code()
    
    appointment_record = {
        "booking_id": booking_id,
        "date": booking.date,
        "start_time": booking.start_time,
        "end_time": end_time_str,
        "appointment_type": booking.appointment_type.value,
        "patient_name": booking.patient.name,
        "patient_email": booking.patient.email,
        "patient_phone": booking.patient.phone,
        "reason": booking.reason,
        "confirmation_code": confirmation_code,
        "status": "confirmed",
        "booked_at": datetime.now().isoformat()
    }
    
    save_appointment(appointment_record)
    
    return BookingResponse(
        booking_id=booking_id,
        status="confirmed",
        confirmation_code=confirmation_code,
        details={
            "date": booking.date,
            "time": booking.start_time,
            "duration_minutes": duration,
            "appointment_type": booking.appointment_type.value,
            "patient_name": booking.patient.name,
            "patient_email": booking.patient.email,
            "reason": booking.reason
        },
        message=f"Appointment successfully booked for {booking.patient.name} on {booking.date} at {booking.start_time}"
    )


@router.get("/appointments")
async def get_all_appointments():
    schedule = load_doctor_schedule()
    stored_appointments = load_appointments()
    all_appointments = schedule['booked_appointments'] + stored_appointments
    return {"appointments": all_appointments}
