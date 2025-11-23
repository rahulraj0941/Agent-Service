# Complete Code Walkthrough

## 📚 Understanding Every Component

This document walks through every major piece of code in the project, explaining what it does and why it's important.

---

## Table of Contents

1. [Backend Entry Point](#backend-entry-point)
2. [Data Models](#data-models)
3. [Calendly Integration](#calendly-integration)
4. [RAG System](#rag-system)
5. [Agent Logic](#agent-logic)
6. [Tools](#tools)
7. [API Endpoints](#api-endpoints)
8. [Frontend Components](#frontend-components)
9. [Data Files](#data-files)

---

## Backend Entry Point

### File: `backend/main.py`

This is where the FastAPI application starts.

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

# Import API routers
from backend.api import chat, calendly_integration
from backend.utils.env_validator import validate_environment

# Create FastAPI application
app = FastAPI(
    title="Medical Appointment Scheduling Agent",
    description="AI-powered appointment scheduling with RAG-based FAQ answering",
    version="1.0.0"
)
```

**What's happening:**
- Creates a FastAPI application
- Sets title and description (appears in API docs)
- Version tracking

```python
# CORS - allows frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**What's happening:**
- CORS = Cross-Origin Resource Sharing
- Allows frontend (port 5000) to call backend (port 8000)
- In production, replace `["*"]` with specific allowed origins

```python
# Include API routes
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(calendly_integration.router, prefix="/api/calendly", tags=["calendly"])
```

**What's happening:**
- Registers the chat endpoint at `/api/chat`
- Registers Calendly endpoints at `/api/calendly/*`
- Tags help organize API documentation

```python
# Serve frontend static files
static_dir = Path(__file__).parent.parent / "frontend" / "dist"
if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")
```

**What's happening:**
- After building frontend (`npm run build`), serves static files
- Allows single-server deployment
- `/assets` route serves JS, CSS, images

```python
@app.get("/")
async def root():
    """Serve frontend or show API info"""
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "message": "Medical Appointment Scheduling Agent API",
        "version": "1.0.0",
        "docs": "/docs"
    }
```

**What's happening:**
- If frontend is built, serve `index.html` at root
- Otherwise, show API information
- Directs to `/docs` for API documentation

---

## Data Models

### File: `backend/models/schemas.py`

These define the shape of data in our application.

```python
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from enum import Enum

class AppointmentType(str, Enum):
    """Appointment types with specific durations"""
    CONSULTATION = "consultation"     # 30 minutes
    FOLLOWUP = "followup"              # 15 minutes
    PHYSICAL = "physical"              # 45 minutes
    SPECIALIST = "specialist"          # 60 minutes
```

**Why Enum?**
- Restricts values to valid appointment types
- Prevents typos (can't accidentally use "consulation")
- Type-safe throughout application
- Auto-validates in API requests

```python
class PatientInfo(BaseModel):
    """Patient contact information"""
    name: str = Field(..., min_length=2, description="Patient's full name")
    email: EmailStr = Field(..., description="Patient's email address")
    phone: str = Field(
        ..., 
        pattern=r"^\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$",
        description="Patient's phone number"
    )
```

**What's happening:**
- `BaseModel` = Pydantic model (auto-validates)
- `Field(...)` = required field
- `min_length=2` = name must be at least 2 characters
- `EmailStr` = validates email format automatically
- `pattern=r"..."` = regex validation for phone numbers
- Accepts formats: 555-1234, (555) 555-1234, +1-555-555-1234

```python
class BookingRequest(BaseModel):
    """Request to book an appointment"""
    appointment_type: AppointmentType
    date: str = Field(..., description="Appointment date in YYYY-MM-DD format")
    start_time: str = Field(..., description="Start time in HH:MM format")
    patient: PatientInfo
    reason: str = Field(..., min_length=5, description="Reason for visit")
```

**What's happening:**
- Combines all booking information
- Nests `PatientInfo` inside
- Validates all fields automatically
- If validation fails, returns clear error message

**Example Valid Request:**
```json
{
  "appointment_type": "consultation",
  "date": "2024-01-15",
  "start_time": "14:30",
  "patient": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "555-1234"
  },
  "reason": "Annual checkup"
}
```

```python
class ChatRequest(BaseModel):
    """Request to chat endpoint"""
    message: str = Field(..., min_length=1, description="User's message")
    conversation_history: Optional[List[ChatMessage]] = Field(
        default=[], 
        description="Previous conversation messages"
    )
```

**What's happening:**
- `message` = current user message (required)
- `conversation_history` = previous messages (optional)
- Maintains context across conversation
- Empty list by default for first message

---

## Calendly Integration

### File: `backend/api/calendly_integration.py`

This simulates Calendly's API for appointment management.

```python
import json
from datetime import datetime, timedelta, date, time as dt_time
from typing import List, Dict, Optional
from pathlib import Path

class CalendlyIntegration:
    def __init__(self):
        """Load doctor schedule and appointment data"""
        # Load schedule
        schedule_path = Path("data/doctor_schedule.json")
        with open(schedule_path, "r") as f:
            self.schedule_data = json.load(f)
        
        # Load booked appointments
        self.appointments_file = Path("data/appointments.json")
        self._ensure_appointments_file()
```

**What's happening:**
- Loads doctor's schedule from JSON file
- Loads existing appointments
- Creates appointments file if it doesn't exist
- All data persists between runs

#### Understanding `get_available_slots()`

```python
def get_available_slots(
    self, 
    date_str: str, 
    appointment_type: str
) -> List[Dict[str, Any]]:
    """
    Get available time slots for a specific date
    
    Args:
        date_str: Date in YYYY-MM-DD format (e.g., "2024-01-15")
        appointment_type: Type of appointment (consultation, followup, etc.)
    
    Returns:
        List of time slots with availability status
    """
```

**Step 1: Validate date**

```python
    try:
        appointment_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")
    
    # Can't book in the past
    if appointment_date < date.today():
        raise ValueError("Cannot book appointments in the past")
```

**Step 2: Get working hours**

```python
    # Get day of week
    day_name = appointment_date.strftime("%A").lower()  # "monday", "tuesday", etc.
    
    # Check if doctor works this day
    if day_name not in self.schedule_data["working_hours"]:
        return []  # No working hours = no slots
    
    working_hours = self.schedule_data["working_hours"][day_name]
    if not working_hours:  # Day off (Sunday = null)
        return []
```

**Step 3: Generate all possible slots**

```python
    # Convert times to minutes for easier calculation
    start_minutes = time_to_minutes(working_hours["start"])  # e.g., "08:00" → 480
    end_minutes = time_to_minutes(working_hours["end"])      # e.g., "18:00" → 1080
    
    # Get slot interval (usually 15 minutes)
    interval = self.schedule_data["appointment_slot_interval"]
    
    # Generate slots
    slots = []
    current_minutes = start_minutes
    
    while current_minutes < end_minutes:
        slot_time = minutes_to_time(current_minutes)  # 480 → "08:00"
        end_time = minutes_to_time(current_minutes + interval)
        
        slots.append({
            "start_time": slot_time,
            "end_time": end_time,
            "available": True  # Assume available, will check later
        })
        
        current_minutes += interval
```

**Example:** If working hours are 8:00 AM - 6:00 PM with 15-min intervals:
```
08:00-08:15
08:15-08:30
08:30-08:45
...
17:45-18:00
```

**Step 4: Filter out lunch break**

```python
    lunch = self.schedule_data["lunch_break"]
    lunch_start = time_to_minutes(lunch["start"])  # "12:00" → 720
    lunch_end = time_to_minutes(lunch["end"])      # "13:00" → 780
    
    # Remove lunch slots
    slots = [
        slot for slot in slots
        if not (time_to_minutes(slot["start_time"]) >= lunch_start and
                time_to_minutes(slot["start_time"]) < lunch_end)
    ]
```

**Step 5: Check booked appointments**

```python
    # Get appointment duration
    durations = {
        "consultation": 30,
        "followup": 15,
        "physical": 45,
        "specialist": 60
    }
    required_duration = durations[appointment_type]
    
    # Load all booked appointments for this date
    booked_appointments = self._get_booked_appointments(date_str)
    
    # Mark unavailable slots
    for slot in slots:
        if self._is_slot_booked(
            date_str, 
            slot["start_time"], 
            required_duration,
            booked_appointments
        ):
            slot["available"] = False
```

**Step 6: Group consecutive slots**

For a 30-minute consultation, we need 2 consecutive 15-minute slots:

```python
    # Group slots by required duration
    final_slots = []
    i = 0
    
    while i < len(slots):
        # Check if we have enough consecutive available slots
        consecutive_available = True
        required_slots = required_duration // interval  # 30 min / 15 min = 2 slots
        
        # Check next N slots
        for j in range(required_slots):
            if i + j >= len(slots) or not slots[i + j]["available"]:
                consecutive_available = False
                break
        
        if consecutive_available:
            # Create combined slot
            final_slots.append({
                "start_time": slots[i]["start_time"],
                "end_time": slots[i + required_slots - 1]["end_time"],
                "available": True
            })
        
        i += 1
    
    return final_slots
```

**Result:** Returns slots that match the appointment duration:
```json
[
  {"start_time": "08:00", "end_time": "08:30", "available": true},
  {"start_time": "08:15", "end_time": "08:45", "available": true},
  {"start_time": "09:00", "end_time": "09:30", "available": false},
  ...
]
```

#### Understanding `create_booking()`

```python
def create_booking(self, booking_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new appointment booking
    
    Validates availability and saves appointment
    """
    # Extract data
    appointment_type = booking_data["appointment_type"]
    date_str = booking_data["date"]
    start_time = booking_data["start_time"]
    
    # Double-check slot is still available
    if not self._is_slot_available(date_str, start_time, appointment_type):
        raise ValueError("Selected time slot is no longer available")
```

**Why double-check?**
- User might take time filling form
- Another user might book the same slot
- Prevents double-booking

```python
    # Generate unique booking ID
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    booking_id = f"APPT-{timestamp}"
    
    # Generate confirmation code
    import random
    import string
    confirmation_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
```

**Example:**
- booking_id: "APPT-20240115-143022"
- confirmation_code: "A7K3B9"

```python
    # Create appointment record
    appointment = {
        "booking_id": booking_id,
        "appointment_type": appointment_type,
        "date": date_str,
        "start_time": start_time,
        "patient": booking_data["patient"],
        "reason": booking_data["reason"],
        "status": "confirmed",
        "confirmation_code": confirmation_code,
        "created_at": datetime.now().isoformat()
    }
    
    # Save to file
    self._save_appointment(appointment)
    
    return {
        "booking_id": booking_id,
        "status": "confirmed",
        "confirmation_code": confirmation_code,
        "details": appointment,
        "message": f"Appointment confirmed for {date_str} at {start_time}"
    }
```

---

## RAG System

### Understanding RAG (Retrieval Augmented Generation)

**Problem:** LLMs can hallucinate or provide outdated information.

**Solution:** Give LLM actual information from a knowledge base.

```
┌─────────────┐
│   User Q:   │
│ "What are   │
│  your hrs?" │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Convert to      │
│ embedding       │ [0.23, 0.87, -0.45, ...]
│ (vector)        │
└──────┬──────────┘
       │
       ▼
┌──────────────────┐
│ Search Vector DB │ Finds similar vectors
│ (ChromaDB)       │ 
└──────┬───────────┘
       │
       ▼
┌────────────────────────┐
│ Retrieve top 3 chunks: │
│ 1. "Hours: Mon-Fri..." │
│ 2. "We're open..."     │
│ 3. "Saturday 9-1..."   │
└──────┬─────────────────┘
       │
       ▼
┌────────────────────────┐
│ Give context to LLM:   │
│ "Using this info:      │
│  [retrieved chunks]    │
│  Answer: What are      │
│  your hours?"          │
└──────┬─────────────────┘
       │
       ▼
┌────────────────────────┐
│ LLM Response:          │
│ "We're open Monday     │
│  through Friday 8-6,   │
│  Saturday 9-1, and     │
│  closed Sunday."       │
└────────────────────────┘
```

### File: `backend/rag/vector_store.py`

```python
import chromadb
from chromadb.config import Settings

class VectorStore:
    def __init__(self, persist_directory: str = "data/vectordb"):
        """Initialize ChromaDB vector database"""
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False
            )
        )
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="clinic_faq",
            metadata={"hnsw:space": "cosine"}  # Similarity metric
        )
```

**What's happening:**
- `PersistentClient` = saves database to disk
- `get_or_create_collection` = creates if new, loads if exists
- `cosine` = measures similarity between vectors (0 = identical, 2 = opposite)

```python
    def add_documents(
        self, 
        texts: List[str], 
        metadatas: List[Dict] = None,
        ids: List[str] = None
    ):
        """Add documents to vector database"""
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(texts))]
        
        self.collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
```

**What's happening:**
- Stores text chunks in database
- Auto-generates embeddings (vectors)
- Metadata = additional info (category, source, etc.)
- IDs must be unique

```python
    def search(
        self, 
        query: str, 
        n_results: int = 3
    ) -> Dict[str, Any]:
        """Search for similar documents"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        return results
```

**What's happening:**
- Converts query to embedding
- Finds most similar documents
- Returns top N results with distance scores
- Lower distance = more similar

### File: `backend/rag/faq_rag.py`

```python
class FAQRAG:
    def __init__(self):
        self.vector_store = VectorStore()
        self.clinic_info_path = Path("data/clinic_info.json")
        
        # Load clinic info if vector DB is empty
        if self.vector_store.collection.count() == 0:
            self._load_clinic_info()
    
    def _load_clinic_info(self):
        """Load and index clinic information"""
        with open(self.clinic_info_path, "r") as f:
            data = json.load(f)
        
        # Convert JSON to searchable text chunks
        chunks = self._create_text_chunks(data)
        
        # Add to vector database
        self.vector_store.add_documents(
            texts=[chunk["text"] for chunk in chunks],
            metadatas=[chunk["metadata"] for chunk in chunks]
        )
```

**What's happening:**
- Loads `clinic_info.json`
- Converts structured JSON to text
- Creates embeddings
- Stores in vector database

**Example chunk:**
```python
{
    "text": "We accept most major insurance providers including Blue Cross Blue Shield, Aetna, Cigna, UnitedHealthcare, Medicare, Medicaid, Humana, and Kaiser Permanente.",
    "metadata": {
        "category": "insurance",
        "source": "clinic_info.json"
    }
}
```

```python
    def get_relevant_context(self, question: str) -> str:
        """Retrieve relevant information for a question"""
        # Search vector database
        results = self.vector_store.search(question, n_results=3)
        
        # Extract documents
        if results and results["documents"]:
            docs = results["documents"][0]  # Top results
            
            # Combine into single context
            context = "\n\n".join(docs)
            return context
        
        return "No relevant information found."
```

**Example:**
```python
question = "What insurance do you accept?"
context = get_relevant_context(question)

# Returns:
# "We accept most major insurance providers including Blue Cross Blue Shield...
#  
#  Payment is due at the time of service. We will file insurance claims...
#  
#  For patients without insurance, we offer a self-pay discount of 15%..."
```

---

## Agent Logic

### File: `backend/agent/scheduling_agent.py`

This is the brain of the application.

```python
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool

class SchedulingAgent:
    def __init__(self):
        """Initialize the intelligent agent"""
        # Load configuration
        self.llm_provider = os.getenv("LLM_PROVIDER", "google")
        self.llm_model = os.getenv("LLM_MODEL", "gemini-2.5-flash")
        
        # Initialize LLM
        self.llm = self._initialize_llm()
        
        # Initialize tools
        self.calendly = CalendlyIntegration()
        self.rag = FAQRAG()
        
        # Create agent
        self.agent_executor = self._create_agent()
```

**What's happening:**
- Loads configuration from environment variables
- Initializes LLM (Google Gemini)
- Sets up tools (Calendly, RAG)
- Creates agent with tools

```python
    def _initialize_llm(self):
        """Initialize LLM based on provider"""
        if self.llm_provider == "google":
            return ChatGoogleGenerativeAI(
                model=self.llm_model,
                temperature=0.7,  # Creativity vs consistency
                google_api_key=os.getenv("GOOGLE_API_KEY")
            )
```

**Temperature explained:**
- 0.0 = Deterministic (same input = same output)
- 0.7 = Balanced (creative but consistent)
- 1.0 = Very creative (unpredictable)

For healthcare, 0.7 is good: professional but not robotic.

```python
    def _create_tools(self) -> List[Tool]:
        """Create tools the agent can use"""
        return [
            Tool(
                name="check_availability",
                func=self._check_availability_wrapper,
                description="""
                Check available appointment slots for a specific date.
                
                Use this when user wants to:
                - Schedule an appointment
                - See available times
                - Find open slots
                
                Args (as JSON string):
                - date: YYYY-MM-DD or natural language (tomorrow, next Monday)
                - appointment_type: consultation|followup|physical|specialist
                - time_preference: morning|afternoon|evening (optional)
                
                Returns: List of available time slots
                """
            ),
            # ... more tools
        ]
```

**Why detailed descriptions?**
- LLM uses description to decide when to call tool
- Clear args help LLM format calls correctly
- Examples prevent errors

```python
    def _create_agent(self) -> AgentExecutor:
        """Create the agent with tools and prompt"""
        # Load system prompt
        from backend.agent.prompts import get_system_prompt
        system_prompt = get_system_prompt()
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create agent
        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=self._create_tools(),
            prompt=prompt
        )
        
        # Create executor
        return AgentExecutor(
            agent=agent,
            tools=self._create_tools(),
            verbose=True,  # Log tool calls
            max_iterations=5,  # Prevent infinite loops
            return_intermediate_steps=True
        )
```

**What's happening:**
- Combines system prompt, chat history, user input
- Creates agent that can call tools
- `AgentExecutor` manages tool calling loop
- `max_iterations=5` prevents runaway loops

**Agent loop:**
```
1. User: "I need an appointment tomorrow"
2. Agent thinks: "Need to check availability"
3. Agent calls: check_availability(date="tomorrow", type="consultation")
4. Tool returns: [list of slots]
5. Agent thinks: "Format these nicely"
6. Agent responds: "I have these times available..."
```

### File: `backend/agent/prompts.py`

```python
def get_system_prompt() -> str:
    """Get system prompt for the agent"""
    current_date = datetime.now().strftime("%A, %B %d, %Y")
    
    return f"""You are a warm, professional medical appointment scheduling assistant for HealthCare Plus Clinic.

CURRENT DATE: {current_date}

YOUR PERSONALITY:
- Empathetic and caring (healthcare context)
- Professional but friendly
- Patient and understanding
- Clear communicator

YOUR CAPABILITIES:
You have access to these tools:
1. check_availability - Find available appointment slots
2. book_appointment - Book an appointment after collecting all info
3. answer_faq - Answer questions about the clinic using RAG

APPOINTMENT TYPES & DURATIONS:
- consultation (30 min): General health concerns, new issues, checkups
- followup (15 min): Quick follow-up on previous visit
- physical (45 min): Annual physical exam, comprehensive checkup
- specialist (60 min): Complex issues requiring specialist attention

BOOKING CONVERSATION FLOW:
1. Greet warmly
2. Ask reason for visit
3. Recommend appropriate appointment type
4. Ask date/time preferences
5. Check availability and show 3-5 options
6. Collect patient information:
   - Full name
   - Email address
   - Phone number
   - Reason for visit (if not already mentioned)
7. Confirm ALL details before booking
8. Book appointment
9. Provide confirmation with booking ID and code

FAQ HANDLING:
- If user asks about clinic (hours, location, insurance, policies):
  * Use answer_faq tool
  * Provide accurate information from knowledge base
  * Don't make up information
- Seamlessly switch between FAQs and scheduling:
  * User asks FAQ during booking → Answer, then return to booking
  * User asks to schedule after FAQ → Smoothly transition

IMPORTANT RULES:
- Always confirm details before booking
- Be conversational, not robotic
- Show options (don't just give one choice)
- Handle ambiguity gracefully:
  * "tomorrow" → Calculate actual date
  * "morning" → Clarify specific time if needed
  * "around 3" → Confirm AM/PM
- If no slots available:
  * Explain situation clearly
  * Offer alternative dates
  * Suggest calling office for urgency
- Never hallucinate information:
  * Use answer_faq for clinic questions
  * Use tools for availability/booking
  
EXAMPLES:

Good opening: "Hello! I'd be happy to help you schedule an appointment. What brings you in today?"
Bad opening: "State your reason for visit."

Good slot presentation: "I have these afternoon slots available tomorrow:
- 2:00 PM
- 3:30 PM  
- 4:00 PM
Which works best for you?"
Bad: "2:00 available."

Good confirmation: "Perfect! Let me confirm:
- Wednesday, January 17 at 3:30 PM
- 30-minute consultation
- Patient: John Doe
- Reason: Headaches
Is this correct?"
Bad: "Booking now."

Remember: You're helping people with their health - be warm, clear, and supportive!
"""
```

**Why this works:**
- Sets clear personality
- Defines exact flow
- Provides examples
- Includes edge cases
- Emphasizes accuracy (no hallucinations)

---

## Tools

### File: `backend/tools/availability_tool.py`

```python
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

def check_availability_tool(
    date: str,
    appointment_type: str,
    time_preference: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check available appointment slots
    
    Handles natural language dates like:
    - "today", "tomorrow"
    - "next Monday", "next week"
    - "2024-01-15"
    """
    from backend.api.calendly_integration import CalendlyIntegration
    
    calendly = CalendlyIntegration()
    
    # Parse natural language dates
    parsed_date = _parse_date(date)
    
    # Get available slots
    slots = calendly.get_available_slots(
        parsed_date.strftime("%Y-%m-%d"),
        appointment_type
    )
    
    # Filter by time preference
    if time_preference:
        slots = _filter_by_time_preference(slots, time_preference)
    
    return {
        "date": parsed_date.strftime("%Y-%m-%d"),
        "day_of_week": parsed_date.strftime("%A"),
        "appointment_type": appointment_type,
        "available_slots": slots,
        "total_available": len([s for s in slots if s["available"]])
    }

def _parse_date(date_str: str) -> datetime:
    """Convert natural language to actual date"""
    date_str_lower = date_str.lower().strip()
    today = datetime.now()
    
    if date_str_lower == "today":
        return today
    elif date_str_lower == "tomorrow":
        return today + timedelta(days=1)
    elif "next" in date_str_lower:
        # "next Monday", "next Friday", etc.
        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for i, day in enumerate(day_names):
            if day in date_str_lower:
                # Calculate days until next occurrence
                days_ahead = i - today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                return today + timedelta(days=days_ahead)
    
    # Try parsing as YYYY-MM-DD
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Could not parse date: {date_str}")

def _filter_by_time_preference(slots: List[Dict], preference: str) -> List[Dict]:
    """Filter slots by time of day"""
    if preference.lower() == "morning":
        # Before 12:00
        return [s for s in slots if int(s["start_time"].split(":")[0]) < 12]
    elif preference.lower() == "afternoon":
        # 12:00 - 17:00
        return [s for s in slots if 12 <= int(s["start_time"].split(":")[0]) < 17]
    elif preference.lower() == "evening":
        # After 17:00
        return [s for s in slots if int(s["start_time"].split(":")[0]) >= 17]
    return slots
```

### File: `backend/tools/booking_tool.py`

```python
def book_appointment_tool(
    appointment_type: str,
    date: str,
    start_time: str,
    patient_name: str,
    patient_email: str,
    patient_phone: str,
    reason: str
) -> Dict[str, Any]:
    """
    Book an appointment
    
    Validates all inputs before booking
    """
    from backend.api.calendly_integration import CalendlyIntegration
    from backend.models.schemas import PatientInfo, BookingRequest, AppointmentType
    
    # Validate appointment type
    try:
        apt_type = AppointmentType(appointment_type)
    except ValueError:
        raise ValueError(f"Invalid appointment type: {appointment_type}")
    
    # Create and validate patient info
    try:
        patient = PatientInfo(
            name=patient_name,
            email=patient_email,
            phone=patient_phone
        )
    except Exception as e:
        raise ValueError(f"Invalid patient information: {str(e)}")
    
    # Create booking request
    booking_data = {
        "appointment_type": appointment_type,
        "date": date,
        "start_time": start_time,
        "patient": patient.dict(),
        "reason": reason
    }
    
    # Create booking
    calendly = CalendlyIntegration()
    result = calendly.create_booking(booking_data)
    
    return result
```

---

## API Endpoints

### File: `backend/api/chat.py`

```python
from fastapi import APIRouter, HTTPException
from backend.models.schemas import ChatRequest, ChatResponse
from backend.agent.scheduling_agent import SchedulingAgent

router = APIRouter()

# Initialize agent (singleton - one instance for all requests)
agent = SchedulingAgent()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint
    
    Handles all user messages and returns agent responses
    """
    try:
        # Process message with agent
        result = await agent.process_message(
            message=request.message,
            conversation_history=request.conversation_history
        )
        
        # Format response
        return ChatResponse(
            response=result["response"],
            conversation_history=result["conversation_history"],
            metadata=result.get("metadata", {})
        )
    
    except Exception as e:
        # Log error
        print(f"Error in chat endpoint: {str(e)}")
        
        # Return friendly error message
        return ChatResponse(
            response="I apologize, but I encountered an error. Could you please rephrase your message or try again?",
            conversation_history=request.conversation_history,
            metadata={"error": str(e)}
        )
```

---

## Frontend Components

### File: `frontend/src/components/ChatInterface.jsx`

```javascript
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './ChatInterface.css';

function ChatInterface() {
  // State management
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Auto-scroll reference
  const messagesEndRef = useRef(null);
  
  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // Send message to backend
  const sendMessage = async () => {
    if (!input.trim()) return;  // Don't send empty messages
    
    // Add user message to UI immediately
    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');  // Clear input
    setLoading(true);  // Show loading indicator
    setError(null);  // Clear any previous errors
    
    try {
      // Call backend API
      const response = await axios.post('/api/chat', {
        message: input,
        conversation_history: messages
      });
      
      // Add assistant response
      const assistantMessage = {
        role: 'assistant',
        content: response.data.response
      };
      setMessages(prev => [...prev, assistantMessage]);
      
    } catch (err) {
      console.error('Error sending message:', err);
      setError('Failed to get response. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  // Handle Enter key press
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };
  
  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>Medical Appointment Scheduler</h2>
        <p>Ask me anything or schedule an appointment</p>
      </div>
      
      <div className="messages-container">
        {messages.length === 0 && (
          <div className="welcome-message">
            <h3>Welcome! How can I help you today?</h3>
            <p>I can help you:</p>
            <ul>
              <li>Schedule an appointment</li>
              <li>Answer questions about our clinic</li>
              <li>Check available time slots</li>
            </ul>
          </div>
        )}
        
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`message ${msg.role}`}
          >
            <div className="message-content">
              {msg.content}
            </div>
          </div>
        ))}
        
        {loading && (
          <div className="message assistant">
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <div className="input-container">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message..."
          rows="2"
          disabled={loading}
        />
        <button
          onClick={sendMessage}
          disabled={loading || !input.trim()}
        >
          {loading ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
  );
}

export default ChatInterface;
```

**Key features:**
- Real-time message updates
- Auto-scroll to latest message
- Loading indicator while waiting
- Error handling and display
- Enter key support (Shift+Enter for new line)
- Disabled state while loading

---

## Data Files

### File: `data/clinic_info.json`

```json
{
  "clinic_details": {
    "name": "HealthCare Plus Clinic",
    "address": "456 Medical Center Drive...",
    "phone": "+1-555-123-4567",
    "hours": {
      "monday": "8:00 AM - 6:00 PM",
      ...
    }
  },
  "insurance_and_billing": {
    "accepted_insurance": ["Blue Cross", "Aetna", ...],
    "payment_methods": ["Cash", "Credit Card", ...],
    "billing_policy": "..."
  },
  "visit_preparation": {
    "first_visit_documents": [...],
    "what_to_bring": [...],
    "arrival_time": "..."
  },
  "policies": {
    "cancellation_policy": "...",
    "late_arrival_policy": "...",
    "covid_protocols": "..."
  }
}
```

**Purpose:**
- Knowledge base for RAG system
- Indexed in vector database
- Source of truth for all clinic information

### File: `data/doctor_schedule.json`

```json
{
  "doctor_info": {
    "name": "Dr. Sarah Mitchell",
    "specialty": "Family Medicine"
  },
  "working_hours": {
    "monday": {"start": "08:00", "end": "18:00"},
    "tuesday": {"start": "08:00", "end": "18:00"},
    ...
    "sunday": null
  },
  "appointment_slot_interval": 15,
  "lunch_break": {
    "start": "12:00",
    "end": "13:00"
  },
  "booked_appointments": [
    {
      "date": "2025-11-23",
      "start_time": "09:00",
      "end_time": "09:30",
      "appointment_type": "consultation",
      "patient_name": "John Smith"
    }
  ]
}
```

**Purpose:**
- Defines when doctor is available
- Pre-existing appointments
- Used to calculate available slots

### File: `data/appointments.json`

```json
[
  {
    "booking_id": "APPT-20250123-143022",
    "appointment_type": "consultation",
    "date": "2025-01-24",
    "start_time": "14:30",
    "patient": {
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "555-0100"
    },
    "reason": "Annual checkup",
    "status": "confirmed",
    "confirmation_code": "A7K3B9",
    "created_at": "2025-01-23T14:30:22.123456"
  }
]
```

**Purpose:**
- Stores all booked appointments
- Prevents double-booking
- Provides booking history

---

## Summary

This walkthrough covered:

✅ **Backend Entry Point** - How FastAPI starts and serves the app
✅ **Data Models** - How Pydantic validates all data
✅ **Calendly Integration** - How slots are calculated and bookings created
✅ **RAG System** - How knowledge retrieval works
✅ **Agent Logic** - How the AI makes decisions
✅ **Tools** - How the agent checks availability and books appointments
✅ **API Endpoints** - How frontend communicates with backend
✅ **Frontend Components** - How the UI works
✅ **Data Files** - Where information is stored

**Next steps:**
1. Review COMPLETE_IMPLEMENTATION_GUIDE.md for architecture
2. Check SETUP_AND_RUN_GUIDE.md to run the project
3. Use SUBMISSION_CHECKLIST.md before submitting

**Questions?** Check the comments in the actual code files - they contain even more detailed explanations!
