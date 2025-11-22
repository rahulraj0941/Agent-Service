# Medical Appointment Scheduling Agent

An intelligent conversational agent that helps patients schedule medical appointments through a natural language interface. The system integrates appointment booking capabilities with a RAG-based FAQ system to provide comprehensive patient support.

## Features

- **Intelligent Conversation Flow**: Natural, empathetic dialogue that guides patients through the scheduling process
- **Multi-type Appointment Scheduling**: Support for 4 appointment types with varying durations
  - General Consultation (30 minutes)
  - Follow-up (15 minutes)
  - Physical Exam (45 minutes)
  - Specialist Consultation (60 minutes)
- **RAG-based FAQ System**: Answers questions about clinic information, insurance, policies, and procedures
- **Smart Scheduling Logic**: Recommends time slots based on patient preferences (morning/afternoon, date flexibility, urgency)
- **Seamless Context Switching**: Handles transitions between FAQ questions and appointment booking
- **Comprehensive Edge Case Handling**: Gracefully manages no available slots, ambiguous dates, API failures, and user changes of mind
- **Mock Calendly Integration**: Full appointment booking system with availability checking and conflict prevention
- **Professional Chat Interface**: React-based UI with real-time messaging and typing indicators

## System Architecture

### Backend Architecture (FastAPI + Python)

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface (React)                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI REST API                           │
│  ┌────────────────┐           ┌─────────────────────┐      │
│  │  Chat Endpoint │           │ Calendly Mock API   │      │
│  └────────┬───────┘           └──────────┬──────────┘      │
└───────────┼──────────────────────────────┼─────────────────┘
            │                              │
            ▼                              ▼
┌───────────────────────┐      ┌──────────────────────┐
│  Scheduling Agent     │      │  Availability Check   │
│  (LangChain + Gemini) │◄────►│  Booking Management   │
│                       │      │  Conflict Prevention  │
└───────┬───────────────┘      └──────────────────────┘
        │
        ├──► ┌─────────────────────────────┐
        │    │  Tool: check_availability   │
        │    │  Tool: book_appointment     │
        │    └─────────────────────────────┘
        │
        └──► ┌─────────────────────────────┐
             │  RAG System (ChromaDB)      │
             │  - FAQ Embeddings           │
             │  - Semantic Search          │
             │  - Context Retrieval        │
             └─────────────────────────────┘
```

### Conversation Flow

1. **Understanding Phase**: Agent greets patient, understands reason for visit, determines appointment type
2. **Preference Gathering**: Asks about preferred date/time, morning vs afternoon, urgency level
3. **Slot Recommendation**: Uses availability tool to fetch open slots, presents 3-5 options
4. **Information Collection**: Gathers patient name, phone, email, reason for visit
5. **Confirmation**: Confirms all details before booking
6. **Booking**: Uses booking tool to create appointment, provides confirmation code

### RAG Pipeline for FAQs

1. **Knowledge Base Initialization**: 
   - Loads clinic information from `data/clinic_info.json`
   - Splits content into semantic chunks (clinic details, insurance, policies, etc.)
   - Generates embeddings using Google's embedding-001 model
   - Stores in ChromaDB vector database

2. **Query Processing**:
   - Detects FAQ-related keywords in user message
   - Generates query embedding
   - Retrieves top 3 most relevant documents using semantic similarity
   - Provides context to LLM for accurate response generation

3. **Context Switching**:
   - Agent maintains conversation state
   - Seamlessly answers FAQ questions during booking flow
   - Returns to scheduling after providing information
   - No context loss between switches

### Tool Calling Strategy

The agent uses LangChain's Google Gemini integration with tool calling for two primary tools:

1. **check_availability**: 
   - Input: Date (YYYY-MM-DD) and appointment type
   - Process: Queries mock Calendly API, checks working hours, existing bookings, lunch breaks
   - Output: List of available time slots

2. **book_appointment**:
   - Input: Appointment details + patient information
   - Process: Validates slot availability, prevents double-booking, generates confirmation code
   - Output: Booking ID, confirmation code, appointment details

## Scheduling Logic

### Available Slot Determination

1. **Working Hours Check**: Verifies date falls within doctor's working schedule
2. **Blocked Dates**: Excludes holidays and blocked dates
3. **Lunch Break Handling**: Automatically excludes 12:00-13:00 lunch period
4. **Appointment Duration Matching**: Ensures slot length matches appointment type
5. **Conflict Prevention**: Checks against existing appointments to prevent double-booking
6. **15-Minute Intervals**: Generates slots in 15-minute increments for flexibility

### Appointment Type Handling

Each appointment type has a specific duration:
- **consultation**: 30 minutes
- **followup**: 15 minutes  
- **physical**: 45 minutes
- **specialist**: 60 minutes

The system automatically calculates end times and ensures slots don't overlap.

### Conflict Prevention

- All booked appointments stored in `data/appointments.json`
- Combines pre-existing bookings from `doctor_schedule.json` with new bookings
- Checks time overlap before confirming: prevents booking if any part of requested slot conflicts with existing appointment

## Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 20+
- Google Gemini API Key (free tier available)

### Installation

1. **Install Python Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Install Frontend Dependencies**:
```bash
cd frontend
npm install
cd ..
```

3. **Configure Environment Variables**:

Create a `.env` file in the root directory (use `.env.example` as template):

```env
# LLM Configuration
LLM_PROVIDER=google
LLM_MODEL=gemini-2.5-flash
GOOGLE_API_KEY=your_google_api_key_here

# Vector Database
VECTOR_DB=chromadb
VECTOR_DB_PATH=./data/vectordb

# Server Configuration
BACKEND_PORT=8000
FRONTEND_PORT=5000
```

**Getting a Google Gemini API Key:**
1. Visit [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key and add it to your `.env` file

**Note:** The free tier includes 10 requests per minute and 250K tokens per minute, which is sufficient for development and testing.

### Running the Application

#### Option 1: Run Backend and Frontend Separately

**Terminal 1 - Backend**:
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm run dev
```

#### Option 2: Production Build

```bash
cd frontend
npm run build
```

Then serve the built files with your preferred static file server.

### Accessing the Application

- **Frontend**: http://localhost:5000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/api/health

## Testing

### Example Conversations

#### Successful Booking Flow

```
User: I need to see the doctor

Agent: I'd be happy to help you schedule an appointment! What's the main reason for your visit today?

User: I've been having headaches

Agent: I understand. For persistent headaches, I'd recommend a general consultation (30 minutes) where the doctor can assess your symptoms. Does that sound appropriate?

User: Yes, that works

Agent: Perfect. When would you like to come in? Do you have a preference for morning or afternoon appointments?

User: Afternoon tomorrow if possible

Agent: Let me check our afternoon availability for tomorrow...
[Uses check_availability tool]
I have these afternoon options for tomorrow:
- 2:00 PM
- 3:30 PM
- 4:00 PM

Which works best for you?

User: 3:30 PM

Agent: Excellent! Before I confirm, I'll need a few details:
- Your full name?

User: John Smith

Agent: - Best phone number to reach you?

User: 555-0100

Agent: - Email address for confirmation?

User: john@example.com

Agent: Perfect! Let me confirm the details:
- Wednesday, November 27th at 3:30 PM
- 30-minute General Consultation
- Reason: Headaches
- Name: John Smith
- Phone: 555-0100
- Email: john@example.com

Is everything correct?

User: Yes

Agent: [Uses book_appointment tool]
All set! Your appointment is confirmed for Wednesday, November 27th at 3:30 PM. Your confirmation code is ABC123. You'll receive a confirmation email at john@example.com.

Is there anything else you'd like to know about your visit?
```

#### FAQ During Booking

```
User: I want to book an appointment

Agent: I'd be happy to help! What brings you in today?

User: Actually, what insurance do you accept?

Agent: [Uses RAG system]
Great question! We accept most major insurance providers including:
- Blue Cross Blue Shield
- Aetna
- Cigna
- UnitedHealthcare
- Medicare
- Medicaid
- Humana
- Kaiser Permanente

We also accept self-pay patients. Do you have insurance with one of these providers?

User: Yes, I have Blue Cross. I'd like to schedule a checkup

Agent: Perfect, we accept Blue Cross Blue Shield. For your checkup, would this be your first visit with us, or are you an existing patient?

[Continues with scheduling...]
```

### Edge Cases Covered

1. **No Available Slots**: 
   - Clearly explains situation
   - Offers alternative dates
   - Suggests calling office for urgent needs

2. **Ambiguous Time References**:
   - "Tomorrow morning" → Asks for specific time preference
   - "Next week" → Confirms which day
   - "Around 3" → Confirms AM/PM

3. **Invalid Input**:
   - Past dates → Politely redirects to future dates
   - Non-existent dates → Validates and asks for correction
   - Outside business hours → Suggests available times

4. **API Failures**:
   - Graceful error handling
   - Informative error messages
   - Fallback to phone contact

5. **User Changes Mind**:
   - Handles gracefully mid-booking
   - Allows restart without confusion
   - No lost context

## Project Structure

```
appointment-scheduling-agent/
├── README.md
├── .env.example
├── requirements.txt
├── backend/
│   ├── main.py                      # FastAPI application entry point
│   ├── agent/
│   │   ├── scheduling_agent.py      # Main agent with LangChain integration
│   │   └── prompts.py               # System prompts and examples
│   ├── rag/
│   │   ├── faq_rag.py              # RAG implementation for FAQ
│   │   ├── embeddings.py            # OpenAI embedding service
│   │   └── vector_store.py          # ChromaDB vector store
│   ├── api/
│   │   ├── chat.py                  # Chat endpoint
│   │   └── calendly_integration.py  # Mock Calendly API
│   ├── tools/
│   │   ├── availability_tool.py     # Availability checking tool
│   │   └── booking_tool.py          # Appointment booking tool
│   └── models/
│       └── schemas.py               # Pydantic data models
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── App.css
│       ├── index.css
│       └── components/
│           ├── ChatInterface.jsx    # Main chat UI component
│           └── ChatInterface.css
├── data/
│   ├── clinic_info.json             # FAQ knowledge base
│   ├── doctor_schedule.json         # Doctor's schedule and bookings
│   └── appointments.json            # Stored appointments (generated)
└── tests/
    └── test_agent.py                # Unit tests (to be implemented)
```

## Technology Stack

### Backend
- **Framework**: FastAPI 0.121.3
- **LLM**: Google Gemini 2.5 Flash (free tier)
- **Agent Framework**: LangChain 1.0.8 with langchain-google-genai
- **Vector Database**: ChromaDB 1.3.5
- **Embeddings**: Google embedding-001 model
- **Data Validation**: Pydantic 2.11.1

### Frontend
- **Framework**: React 18.3.1
- **Build Tool**: Vite 6.0.7
- **HTTP Client**: Axios 1.7.2
- **Styling**: Custom CSS

## API Documentation

### POST /api/chat

Send a message to the scheduling agent.

**Request Body**:
```json
{
  "message": "I need to see the doctor",
  "conversation_history": [
    {"role": "user", "content": "previous message"},
    {"role": "assistant", "content": "previous response"}
  ]
}
```

**Response**:
```json
{
  "response": "I'd be happy to help you schedule an appointment...",
  "conversation_history": [...],
  "metadata": {
    "used_faq": false,
    "tools_used": 0
  }
}
```

### GET /api/calendly/availability

Check available time slots.

**Query Parameters**:
- `date`: YYYY-MM-DD format
- `appointment_type`: consultation | followup | physical | specialist

**Response**:
```json
{
  "date": "2025-11-25",
  "appointment_type": "consultation",
  "available_slots": [
    {"start_time": "09:00", "end_time": "09:30", "available": true},
    {"start_time": "09:30", "end_time": "10:00", "available": false}
  ]
}
```

### POST /api/calendly/book

Book an appointment.

**Request Body**:
```json
{
  "appointment_type": "consultation",
  "date": "2025-11-25",
  "start_time": "14:00",
  "patient": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-555-0100"
  },
  "reason": "Annual checkup"
}
```

**Response**:
```json
{
  "booking_id": "APPT-20251125-1234",
  "status": "confirmed",
  "confirmation_code": "ABC123",
  "details": {...},
  "message": "Appointment successfully booked..."
}
```

## Configuration

### Environment Variables

- `GOOGLE_API_KEY`: Your Google Gemini API key (required)
- `LLM_PROVIDER`: LLM provider to use (default: google)
- `LLM_MODEL`: Gemini model to use (default: gemini-2.5-flash)
- `BACKEND_PORT`: Backend server port (default: 8000)
- `FRONTEND_PORT`: Frontend dev server port (default: 5000)
- `VECTOR_DB`: Vector database type (default: chromadb)
- `VECTOR_DB_PATH`: ChromaDB storage path (default: ./data/vectordb)

**Environment Validation:**
Run the environment validator before starting the application:
```bash
python backend/utils/env_validator.py
```

### Clinic Configuration

Modify `data/clinic_info.json` to update:
- Clinic details and contact information
- Accepted insurance providers
- Policies and procedures
- FAQ content

Modify `data/doctor_schedule.json` to update:
- Working hours
- Blocked dates
- Pre-existing appointments

## Migration Notes

### OpenAI to Google Gemini (November 2025)

The application was migrated from OpenAI to Google Gemini API to leverage the free tier and avoid quota limitations.

**Key Changes:**
- **LLM Model**: Changed from `gpt-4o-mini` to `gemini-2.5-flash`
- **Embeddings**: Changed from `text-embedding-3-small` to `models/embedding-001`
- **Dependencies**: Replaced `langchain-openai` with `langchain-google-genai`
- **Environment Variables**: 
  - `OPENAI_API_KEY` → `GOOGLE_API_KEY`
  - Added `LLM_PROVIDER=google`
  - Updated `LLM_MODEL` to `gemini-2.5-flash`

**Response Format Handling:**
- Added `_extract_text_content()` helper in `SchedulingAgent` to handle Gemini's list-based response format
- Gemini returns content as `[{'type': 'text', 'text': '...'}]` instead of plain strings
- Helper function normalizes responses to strings for consistent serialization

**Free Tier Limits:**
- 10 requests per minute (RPM)
- 250,000 tokens per minute (TPM)
- 250 requests per day (RPD)

**Environment Validation:**
- Added `backend/utils/env_validator.py` to validate required Gemini environment variables
- Warns if deprecated model names (containing "1.5") are detected
- Run with: `python backend/utils/env_validator.py`

## Future Enhancements

1. **Real Calendly Integration**: Replace mock API with actual Calendly integration
2. **Multi-doctor Support**: Schedule with multiple healthcare providers
3. **SMS Notifications**: Send appointment reminders via Twilio
4. **Patient Portal**: View appointment history and reschedule
5. **Advanced RAG**: Multi-source knowledge base with improved retrieval
6. **Voice Interface**: Add voice input/output capabilities
7. **Analytics Dashboard**: Track booking patterns and agent performance
8. **Calendar Export**: Generate ICS files for calendar apps

## License

This project was created as a technical assessment demonstration.

## Support

For questions or issues, contact the development team or refer to the API documentation at `/docs`.
