from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from enum import Enum


class AppointmentType(str, Enum):
    CONSULTATION = "consultation"
    FOLLOWUP = "followup"
    PHYSICAL = "physical"
    SPECIALIST = "specialist"


class TimeSlot(BaseModel):
    start_time: str = Field(..., description="Start time in HH:MM format")
    end_time: str = Field(..., description="End time in HH:MM format")
    available: bool = Field(..., description="Whether the slot is available")


class AvailabilityRequest(BaseModel):
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    appointment_type: AppointmentType


class AvailabilityResponse(BaseModel):
    date: str
    available_slots: List[TimeSlot]
    appointment_type: AppointmentType


class PatientInfo(BaseModel):
    name: str = Field(..., min_length=2, description="Patient's full name")
    email: EmailStr = Field(..., description="Patient's email address")
    phone: str = Field(..., pattern=r"^\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$", 
                       description="Patient's phone number")


class BookingRequest(BaseModel):
    appointment_type: AppointmentType
    date: str = Field(..., description="Appointment date in YYYY-MM-DD format")
    start_time: str = Field(..., description="Start time in HH:MM format")
    patient: PatientInfo
    reason: str = Field(..., min_length=5, description="Reason for visit")


class BookingResponse(BaseModel):
    booking_id: str
    status: str
    confirmation_code: str
    details: Dict[str, Any]
    message: str


class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User's message")
    conversation_history: Optional[List[ChatMessage]] = Field(
        default=[], 
        description="Previous conversation messages"
    )


class ChatResponse(BaseModel):
    response: str = Field(..., description="Agent's response")
    conversation_history: List[ChatMessage] = Field(..., description="Updated conversation history")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Additional metadata about the response"
    )


class AppointmentDuration(BaseModel):
    consultation: int = 30
    followup: int = 15
    physical: int = 45
    specialist: int = 60
