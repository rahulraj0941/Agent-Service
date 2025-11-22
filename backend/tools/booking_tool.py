from langchain.tools import Tool
from typing import Dict, Any
import httpx
import json


async def book_appointment(input_str: str) -> str:
    try:
        booking_data = json.loads(input_str)
        
        required_fields = ["appointment_type", "date", "start_time", "patient_name", 
                          "patient_email", "patient_phone", "reason"]
        missing_fields = [field for field in required_fields if field not in booking_data]
        
        if missing_fields:
            return json.dumps({
                "success": False,
                "error": f"Missing required fields: {', '.join(missing_fields)}",
                "required_fields": required_fields
            })
        
        payload = {
            "appointment_type": booking_data["appointment_type"],
            "date": booking_data["date"],
            "start_time": booking_data["start_time"],
            "patient": {
                "name": booking_data["patient_name"],
                "email": booking_data["patient_email"],
                "phone": booking_data["patient_phone"]
            },
            "reason": booking_data["reason"]
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
    
    except json.JSONDecodeError:
        return json.dumps({
            "success": False,
            "error": "Invalid input format. Expected JSON with booking details."
        })
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Error booking appointment: {str(e)}"
        })


booking_tool = Tool(
    name="book_appointment",
    description="""
    Book a medical appointment with all required patient information.
    
    Input should be a JSON string with:
    - appointment_type: One of 'consultation', 'followup', 'physical', 'specialist' (required)
    - date: Appointment date in YYYY-MM-DD format (required)
    - start_time: Start time in HH:MM format (required)
    - patient_name: Patient's full name (required)
    - patient_email: Patient's email address (required)
    - patient_phone: Patient's phone number (required)
    - reason: Reason for visit (required)
    
    Example: {
        "appointment_type": "consultation",
        "date": "2025-11-25",
        "start_time": "14:00",
        "patient_name": "John Doe",
        "patient_email": "john@example.com",
        "patient_phone": "+1-555-0100",
        "reason": "Annual checkup"
    }
    
    Only use this tool after confirming all details with the patient.
    Returns booking confirmation with booking ID and confirmation code.
    """,
    coroutine=book_appointment
)
