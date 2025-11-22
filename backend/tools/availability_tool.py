from langchain.tools import Tool
from typing import Dict, Any
import httpx
import json
from datetime import datetime, timedelta


async def check_availability(input_str: str) -> str:
    try:
        params = json.loads(input_str)
        date = params.get("date")
        appointment_type = params.get("appointment_type", "consultation")
        
        if not date:
            today = datetime.now()
            suggested_dates = [
                (today + timedelta(days=1)).strftime("%Y-%m-%d"),
                (today + timedelta(days=2)).strftime("%Y-%m-%d"),
                (today + timedelta(days=3)).strftime("%Y-%m-%d")
            ]
            return json.dumps({
                "error": "No date provided",
                "suggestion": "Please specify a date. Here are some upcoming dates: " + ", ".join(suggested_dates)
            })
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://localhost:8000/api/calendly/availability",
                params={"date": date, "appointment_type": appointment_type},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                available_slots = [
                    slot for slot in data.get("available_slots", []) 
                    if slot.get("available", False)
                ]
                
                if not available_slots:
                    return json.dumps({
                        "date": date,
                        "available": False,
                        "message": f"No available slots on {date}. Consider checking nearby dates."
                    })
                
                slots_list = [slot["start_time"] for slot in available_slots[:10]]
                
                return json.dumps({
                    "date": date,
                    "available": True,
                    "appointment_type": appointment_type,
                    "available_slots": slots_list,
                    "total_available": len(available_slots)
                })
            else:
                return json.dumps({
                    "error": "Failed to fetch availability",
                    "status_code": response.status_code,
                    "details": response.text
                })
    
    except json.JSONDecodeError:
        return json.dumps({
            "error": "Invalid input format. Expected JSON with 'date' and 'appointment_type' fields."
        })
    except Exception as e:
        return json.dumps({
            "error": f"Error checking availability: {str(e)}"
        })


availability_tool = Tool(
    name="check_availability",
    description="""
    Check doctor's availability for a specific date and appointment type.
    
    Input should be a JSON string with:
    - date: Date in YYYY-MM-DD format (required)
    - appointment_type: One of 'consultation', 'followup', 'physical', 'specialist' (default: 'consultation')
    
    Example: {"date": "2025-11-25", "appointment_type": "consultation"}
    
    Returns available time slots for the specified date and appointment type.
    Use this tool when the user asks about availability or wants to see open time slots.
    """,
    coroutine=check_availability
)
