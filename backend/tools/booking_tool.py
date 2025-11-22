from langchain_core.tools import StructuredTool
from typing import Dict, Any
import httpx
import json
from pydantic import BaseModel, Field


class BookingInput(BaseModel):
    appointment_type: str = Field(description="One of 'consultation', 'followup', 'physical', 'specialist'")
    date: str = Field(description="Appointment date in YYYY-MM-DD format")
    start_time: str = Field(description="Start time in HH:MM format")
    patient_name: str = Field(description="Patient's full name")
    patient_email: str = Field(description="Patient's email address")
    patient_phone: str = Field(description="Patient's phone number")
    reason: str = Field(description="Reason for visit")


async def book_appointment(
    appointment_type: str,
    date: str,
    start_time: str,
    patient_name: str,
    patient_email: str,
    patient_phone: str,
    reason: str
) -> str:
    try:
        payload = {
            "appointment_type": appointment_type,
            "date": date,
            "start_time": start_time,
            "patient": {
                "name": patient_name,
                "email": patient_email,
                "phone": patient_phone
            },
            "reason": reason
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/calendly/book",
                json=payload,
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return json.dumps({
                    "success": True,
                    "booking_id": data.get("booking_id"),
                    "confirmation_code": data.get("confirmation_code"),
                    "status": data.get("status"),
                    "details": data.get("details"),
                    "message": data.get("message")
                })
            else:
                error_detail = response.json().get("detail", "Unknown error") if response.text else "Unknown error"
                return json.dumps({
                    "success": False,
                    "error": error_detail,
                    "status_code": response.status_code
                })
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Error booking appointment: {str(e)}"
        })


booking_tool = StructuredTool.from_function(
    coroutine=book_appointment,
    name="book_appointment",
    description="Book a medical appointment with all required patient information. Only use this tool after confirming all details with the patient. Returns booking confirmation with booking ID and confirmation code.",
    args_schema=BookingInput
)
