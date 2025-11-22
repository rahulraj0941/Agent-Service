# Medical Appointment Scheduling Agent

## Overview

An intelligent conversational agent that helps patients schedule medical appointments through natural language interaction. The system combines appointment booking capabilities with a RAG-based FAQ system to answer clinic-related questions. Built with FastAPI backend, React frontend, and powered by OpenAI's GPT-4 with LangChain for agent orchestration.

**Latest Updates (Nov 22, 2025):**
- Fixed LangChain 1.0.8 compatibility issues with StructuredTool API
- Implemented lazy initialization for RAG system to prevent startup crashes
- Added graceful error handling for OpenAI API quota limitations
- Both frontend and backend servers running successfully
- All core features tested and working

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Technology Stack**: React 18 with Vite as build tool
- **Key Components**:
  - ChatInterface: Real-time messaging UI with typing indicators
  - App: Main application container with header and layout
- **Styling**: CSS with gradient backgrounds and modern card-based design
- **Communication**: Axios for HTTP requests to backend API
- **Development Server**: Runs on port 5000 with proxy to backend port 8000

### Backend Architecture
- **Framework**: FastAPI with async/await support
- **Port**: 8000
- **Key Components**:
  1. **Scheduling Agent** (LangChain 1.0.8 + OpenAI GPT-4o-mini):
     - Multi-turn conversation management
     - Context-aware dialogue handling
     - Seamless switching between FAQ and scheduling modes
     - Tool-calling capabilities using StructuredTool with Pydantic schemas
     - Lazy initialization for FAQ retrieval (prevents startup crashes)
  
  2. **RAG System**:
     - Vector database: ChromaDB for persistent storage
     - Embeddings: OpenAI text-embedding-3-small
     - Knowledge base: Clinic information, insurance policies, visit preparation
     - FAQ retrieval with semantic search
     - Graceful degradation: Falls back to JSON data when embeddings unavailable
  
  3. **Mock Calendly Integration**:
     - Appointment availability checking
     - Booking creation with conflict prevention
     - Confirmation code generation
     - Persistent storage in JSON files
     - Supports 4 appointment types with different durations

### Data Storage
- **File-based storage** for MVP implementation:
  - `data/clinic_info.json`: Clinic details, insurance, policies, FAQ content
  - `data/doctor_schedule.json`: Working hours, lunch breaks, booked appointments
  - `data/appointments.json`: Runtime storage of new bookings
  - `data/vectordb/`: ChromaDB persistent vector store for embeddings

### Appointment Types
System supports 4 appointment types with varying durations:
- General Consultation: 30 minutes
- Follow-up: 15 minutes  
- Physical Exam: 45 minutes
- Specialist Consultation: 60 minutes

### Agent Tools
The LangChain agent has access to two primary tools:
1. **check_availability**: Queries available time slots for a given date and appointment type
2. **book_appointment**: Creates confirmed appointments with patient information validation

### API Endpoints
- `POST /api/chat`: Main conversational endpoint for user interactions
- `GET /api/health`: Health check endpoint
- `GET /api/calendly/availability`: Check available appointment slots
- `POST /api/calendly/book`: Book new appointments

### Conversation Flow
The agent handles:
- Natural language understanding of scheduling intents
- Date/time preference extraction (morning/afternoon, urgency, flexibility)
- Patient information collection (name, email, phone)
- Appointment type recommendation based on reason for visit
- Graceful handling of unavailable slots with alternatives
- Context switching between FAQ queries and appointment booking
- Confirmation before finalizing bookings

## External Dependencies

### Third-Party APIs
- **OpenAI API**: 
  - GPT-4o-mini for conversational agent
  - text-embedding-3-small for RAG embeddings
  - Requires `OPENAI_API_KEY` environment variable

### Python Libraries
- **FastAPI**: Web framework for REST API
- **LangChain**: Agent orchestration and tool calling (langchain, langchain-openai, langchain-community)
- **ChromaDB**: Vector database for FAQ embeddings
- **Pydantic**: Data validation and schema definitions
- **uvicorn**: ASGI server
- **httpx**: Async HTTP client
- **python-dotenv**: Environment variable management

### Frontend Libraries
- **React**: UI framework
- **Vite**: Build tool and dev server
- **Axios**: HTTP client for API calls
- **date-fns**: Date manipulation utilities

### Environment Configuration
Required environment variables:
- `OPENAI_API_KEY`: OpenAI API key for LLM and embeddings
- `LLM_MODEL`: Optional, defaults to "gpt-4o-mini"
- `BACKEND_PORT`: Optional, defaults to 8000

### CORS Configuration
Backend configured to accept requests from all origins for development purposes.