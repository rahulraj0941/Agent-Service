import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture(scope="function", autouse=True)
def clean_test_appointments():
    """Clean up appointments.json before each test to prevent conflicts"""
    appointments_file = "data/appointments.json"
    
    original_content = []
    if os.path.exists(appointments_file):
        with open(appointments_file, 'r') as f:
            original_content = json.load(f)
    
    with open(appointments_file, 'w') as f:
        json.dump([], f)
    
    yield
    
    with open(appointments_file, 'w') as f:
        json.dump(original_content, f, indent=2)


class TestSchedulingLogic:
    """
    Direct tests for scheduling logic functions without external dependencies.
    Tests availability calculations, conflict detection, and time utilities.
    """
    
    def test_time_to_minutes_conversion(self):
        """Test time string to minutes conversion"""
        from backend.api.calendly_integration import time_to_minutes
        
        assert time_to_minutes("00:00") == 0
        assert time_to_minutes("08:00") == 480
        assert time_to_minutes("12:30") == 750
        assert time_to_minutes("18:00") == 1080
        assert time_to_minutes("23:59") == 1439
    
    def test_minutes_to_time_conversion(self):
        """Test minutes to time string conversion"""
        from backend.api.calendly_integration import minutes_to_time
        
        assert minutes_to_time(0) == "00:00"
        assert minutes_to_time(480) == "08:00"
        assert minutes_to_time(750) == "12:30"
        assert minutes_to_time(1080) == "18:00"
        assert minutes_to_time(1439) == "23:59"
    
    def test_conflict_detection_no_overlap(self):
        """Test that non-overlapping appointments don't conflict"""
        from backend.api.calendly_integration import is_slot_booked
        
        booked_appointments = [
            {
                "date": "2025-11-25",
                "start_time": "09:00",
                "end_time": "10:00"
            },
            {
                "date": "2025-11-25",
                "start_time": "14:00",
                "end_time": "15:00"
            }
        ]
        
        # Test slot before first appointment
        assert is_slot_booked("2025-11-25", "08:00", "09:00", booked_appointments) is False
        
        # Test slot between appointments
        assert is_slot_booked("2025-11-25", "10:00", "14:00", booked_appointments) is False
        
        # Test slot after last appointment
        assert is_slot_booked("2025-11-25", "15:00", "16:00", booked_appointments) is False
    
    def test_conflict_detection_with_overlap(self):
        """Test that overlapping appointments are detected"""
        from backend.api.calendly_integration import is_slot_booked
        
        booked_appointments = [
            {
                "date": "2025-11-25",
                "start_time": "09:00",
                "end_time": "10:00"
            }
        ]
        
        # Exact overlap
        assert is_slot_booked("2025-11-25", "09:00", "10:00", booked_appointments) is True
        
        # Partial overlap - starts before, ends during
        assert is_slot_booked("2025-11-25", "08:30", "09:30", booked_appointments) is True
        
        # Partial overlap - starts during, ends after
        assert is_slot_booked("2025-11-25", "09:30", "10:30", booked_appointments) is True
        
        # Complete overlap - encompasses the booked slot
        assert is_slot_booked("2025-11-25", "08:00", "11:00", booked_appointments) is True
        
        # Inside the booked slot
        assert is_slot_booked("2025-11-25", "09:15", "09:45", booked_appointments) is True
    
    def test_conflict_detection_different_dates(self):
        """Test that appointments on different dates don't conflict"""
        from backend.api.calendly_integration import is_slot_booked
        
        booked_appointments = [
            {
                "date": "2025-11-25",
                "start_time": "09:00",
                "end_time": "10:00"
            }
        ]
        
        # Same time, different date - should not conflict
        assert is_slot_booked("2025-11-26", "09:00", "10:00", booked_appointments) is False
    
    def test_get_day_of_week(self):
        """Test day of week calculation"""
        from backend.api.calendly_integration import get_day_of_week
        
        # Test known dates
        assert get_day_of_week("2025-11-23") == "sunday"
        assert get_day_of_week("2025-11-24") == "monday"
        assert get_day_of_week("2025-11-25") == "tuesday"


@pytest.mark.asyncio
class TestCalendlyAPILogic:
    """
    Direct tests for Calendly API logic without requiring server to be running.
    Tests the availability and booking functions directly.
    """
    
    async def test_availability_on_working_day(self):
        """Test availability calculation for a normal working day"""
        from backend.api.calendly_integration import get_availability
        from backend.models.schemas import AppointmentType
        
        # Use a future Monday (working day)
        future_monday = (datetime.now() + timedelta(days=(7 - datetime.now().weekday()) % 7 + 7)).strftime("%Y-%m-%d")
        
        response = await get_availability(future_monday, AppointmentType.CONSULTATION)
        
        assert response.date == future_monday
        assert response.appointment_type == AppointmentType.CONSULTATION
        assert isinstance(response.available_slots, list)
        
        # Working day should have some slots
        if response.available_slots:
            # Verify slot structure
            slot = response.available_slots[0]
            assert hasattr(slot, 'start_time')
            assert hasattr(slot, 'end_time')
            assert hasattr(slot, 'available')
            
            # Verify time format
            assert ":" in slot.start_time
            assert ":" in slot.end_time
    
    async def test_availability_on_sunday(self):
        """Test that Sunday returns no availability (clinic closed)"""
        from backend.api.calendly_integration import get_availability
        from backend.models.schemas import AppointmentType
        
        # Find next Sunday
        days_until_sunday = (6 - datetime.now().weekday()) % 7
        if days_until_sunday == 0:
            days_until_sunday = 7
        next_sunday = (datetime.now() + timedelta(days=days_until_sunday)).strftime("%Y-%m-%d")
        
        response = await get_availability(next_sunday, AppointmentType.CONSULTATION)
        
        assert response.date == next_sunday
        assert response.available_slots == []
    
    async def test_availability_excludes_lunch_break(self):
        """Test that lunch break times are not included in available slots"""
        from backend.api.calendly_integration import get_availability
        from backend.models.schemas import AppointmentType
        
        future_monday = (datetime.now() + timedelta(days=(7 - datetime.now().weekday()) % 7 + 7)).strftime("%Y-%m-%d")
        
        response = await get_availability(future_monday, AppointmentType.CONSULTATION)
        
        # Check that no slots overlap with lunch (12:00-13:00)
        for slot in response.available_slots:
            start_minutes = int(slot.start_time.split(':')[0]) * 60 + int(slot.start_time.split(':')[1])
            end_minutes = int(slot.end_time.split(':')[0]) * 60 + int(slot.end_time.split(':')[1])
            
            lunch_start = 12 * 60
            lunch_end = 13 * 60
            
            # Slot should not overlap with lunch
            assert end_minutes <= lunch_start or start_minutes >= lunch_end
    
    async def test_booking_with_valid_data(self):
        """Test booking creation with valid data"""
        from backend.api.calendly_integration import book_appointment, load_appointments
        from backend.models.schemas import BookingRequest, PatientInfo, AppointmentType
        
        # Use far future date to avoid conflicts (365 days = 1 year)
        future_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
        
        booking_request = BookingRequest(
            appointment_type=AppointmentType.CONSULTATION,
            date=future_date,
            start_time="14:37",
            patient=PatientInfo(
                name="Test Patient",
                email="test@example.com",
                phone="555-123-4567"
            ),
            reason="Test appointment"
        )
        
        response = await book_appointment(booking_request)
        
        assert response.status == "confirmed"
        assert response.booking_id is not None
        assert response.confirmation_code is not None
        assert len(response.confirmation_code) == 6
        assert response.details["date"] == future_date
        assert response.details["time"] == "14:37"
    
    async def test_booking_prevents_double_booking(self):
        """Test that booking the same slot twice fails"""
        from backend.api.calendly_integration import book_appointment
        from backend.models.schemas import BookingRequest, PatientInfo, AppointmentType
        from fastapi import HTTPException
        
        # Use far future date (400 days) to avoid conflicts
        future_date = (datetime.now() + timedelta(days=400)).strftime("%Y-%m-%d")
        
        booking_request = BookingRequest(
            appointment_type=AppointmentType.FOLLOWUP,
            date=future_date,
            start_time="16:23",
            patient=PatientInfo(
                name="First Patient",
                email="first@example.com",
                phone="555-234-5678"
            ),
            reason="First booking"
        )
        
        # First booking should succeed
        response1 = await book_appointment(booking_request)
        assert response1.status == "confirmed"
        
        # Second booking at same time should fail
        booking_request2 = BookingRequest(
            appointment_type=AppointmentType.FOLLOWUP,
            date=future_date,
            start_time="16:23",
            patient=PatientInfo(
                name="Second Patient",
                email="second@example.com",
                phone="555-345-6789"
            ),
            reason="Second booking"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await book_appointment(booking_request2)
        
        assert exc_info.value.status_code == 409


@pytest.mark.asyncio
class TestAvailabilityTool:
    """
    Tests for availability_tool with mocked HTTP calls.
    """
    
    async def test_check_availability_with_mock(self):
        """Test availability tool with mocked HTTP response"""
        from backend.tools.availability_tool import check_availability
        
        mock_response = {
            "date": "2025-11-30",
            "available_slots": [
                {"start_time": "09:00", "end_time": "09:30", "available": True},
                {"start_time": "10:00", "end_time": "10:30", "available": True},
                {"start_time": "14:00", "end_time": "14:30", "available": False}
            ],
            "appointment_type": "consultation"
        }
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = AsyncMock(
                status_code=200,
                json=Mock(return_value=mock_response)
            )
            
            result = await check_availability(date="2025-11-30", appointment_type="consultation")
            data = json.loads(result)
            
            assert data["available"] is True
            assert data["date"] == "2025-11-30"
            assert data["appointment_type"] == "consultation"
            assert "available_slots" in data
            assert len(data["available_slots"]) == 2  # Only available slots
            assert data["available_slots"][0] == "09:00"
            assert data["available_slots"][1] == "10:00"
    
    async def test_check_availability_no_slots(self):
        """Test availability when no slots are available"""
        from backend.tools.availability_tool import check_availability
        
        mock_response = {
            "date": "2025-11-30",
            "available_slots": [],
            "appointment_type": "consultation"
        }
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = AsyncMock(
                status_code=200,
                json=Mock(return_value=mock_response)
            )
            
            result = await check_availability(date="2025-11-30", appointment_type="consultation")
            data = json.loads(result)
            
            assert data["available"] is False
            assert "message" in data


@pytest.mark.asyncio
class TestBookingTool:
    """
    Tests for booking_tool with mocked HTTP calls.
    """
    
    async def test_book_appointment_success(self):
        """Test successful booking with mocked HTTP response"""
        from backend.tools.booking_tool import book_appointment
        
        mock_response = {
            "booking_id": "APPT-20251130-1234",
            "status": "confirmed",
            "confirmation_code": "ABC123",
            "details": {
                "date": "2025-11-30",
                "time": "10:00",
                "duration_minutes": 30,
                "appointment_type": "consultation"
            },
            "message": "Appointment confirmed"
        }
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = AsyncMock(
                status_code=200,
                json=Mock(return_value=mock_response)
            )
            
            result = await book_appointment(
                appointment_type="consultation",
                date="2025-11-30",
                start_time="10:00",
                patient_name="John Doe",
                patient_email="john@example.com",
                patient_phone="+1-555-0123",
                reason="Regular checkup"
            )
            
            data = json.loads(result)
            
            assert data["success"] is True
            assert data["booking_id"] == "APPT-20251130-1234"
            assert data["confirmation_code"] == "ABC123"
            assert data["status"] == "confirmed"
    
    async def test_book_appointment_conflict(self):
        """Test booking failure due to conflict"""
        from backend.tools.booking_tool import book_appointment
        
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = AsyncMock(
                status_code=409,
                json=Mock(return_value={"detail": "This time slot is no longer available"}),
                text="error"
            )
            
            result = await book_appointment(
                appointment_type="consultation",
                date="2025-11-30",
                start_time="10:00",
                patient_name="John Doe",
                patient_email="john@example.com",
                patient_phone="+1-555-0123",
                reason="Regular checkup"
            )
            
            data = json.loads(result)
            
            assert data["success"] is False
            assert "error" in data


@pytest.mark.asyncio
class TestRAGSystem:
    """
    Tests for RAG-based FAQ system with mocked embeddings.
    """
    
    async def test_faq_retrieval_with_mock(self):
        """Test FAQ retrieval with mocked embeddings and vector store"""
        
        # Mock the EmbeddingService
        mock_embedding_service = Mock()
        mock_embedding_service.embed_text.return_value = [0.1] * 768
        mock_embedding_service.embed_documents.return_value = [[0.1] * 768] * 10
        
        # Mock the VectorStore
        mock_vector_store = Mock()
        mock_vector_store.count.return_value = 10
        mock_vector_store.query.return_value = {
            "documents": [
                "Accepted Insurance Providers: Blue Cross Blue Shield, Aetna, Cigna",
                "Payment Methods: Cash, Credit Card, HSA/FSA cards"
            ],
            "metadatas": [
                {"category": "insurance_billing"},
                {"category": "insurance_billing"}
            ],
            "distances": [0.2, 0.3]
        }
        
        with patch('backend.rag.faq_rag.EmbeddingService', return_value=mock_embedding_service), \
             patch('backend.rag.faq_rag.VectorStore', return_value=mock_vector_store):
            
            from backend.rag.faq_rag import FAQRetrieval
            
            faq = FAQRetrieval()
            context = faq.get_context_for_query("What insurance do you accept?")
            
            assert context is not None
            assert len(context) > 0
            assert "insurance" in context.lower() or "Insurance" in context
    
    async def test_faq_retrieval_returns_relevant_content(self):
        """Test that FAQ retrieval returns expected content types"""
        
        mock_embedding_service = Mock()
        mock_embedding_service.embed_text.return_value = [0.1] * 768
        mock_embedding_service.embed_documents.return_value = [[0.1] * 768] * 10
        
        mock_vector_store = Mock()
        mock_vector_store.count.return_value = 10
        
        # Test insurance query
        mock_vector_store.query.return_value = {
            "documents": [
                "Accepted Insurance Providers: Blue Cross Blue Shield, Aetna, Cigna, UnitedHealthcare",
                "Payment Methods: Cash, Credit Card, HSA/FSA cards"
            ],
            "metadatas": [{"category": "insurance_billing"}, {"category": "insurance_billing"}],
            "distances": [0.1, 0.2]
        }
        
        with patch('backend.rag.faq_rag.EmbeddingService', return_value=mock_embedding_service), \
             patch('backend.rag.faq_rag.VectorStore', return_value=mock_vector_store):
            
            from backend.rag.faq_rag import FAQRetrieval
            
            faq = FAQRetrieval()
            docs = faq.retrieve_relevant_info("What insurance do you accept?", top_k=3)
            
            assert isinstance(docs, list)
            assert len(docs) > 0
            assert any("Insurance" in doc or "insurance" in doc for doc in docs)
    
    async def test_faq_context_formatting(self):
        """Test that FAQ context is properly formatted"""
        
        mock_embedding_service = Mock()
        mock_embedding_service.embed_text.return_value = [0.1] * 768
        mock_embedding_service.embed_documents.return_value = [[0.1] * 768] * 10
        
        mock_vector_store = Mock()
        mock_vector_store.count.return_value = 10
        mock_vector_store.query.return_value = {
            "documents": [
                "Clinic Hours: Monday-Friday 8:00 AM - 6:00 PM",
                "Location: 456 Medical Center Drive, New York, NY"
            ],
            "metadatas": [{"category": "clinic_details"}, {"category": "clinic_details"}],
            "distances": [0.1, 0.2]
        }
        
        with patch('backend.rag.faq_rag.EmbeddingService', return_value=mock_embedding_service), \
             patch('backend.rag.faq_rag.VectorStore', return_value=mock_vector_store):
            
            from backend.rag.faq_rag import FAQRetrieval
            
            faq = FAQRetrieval()
            context = faq.get_context_for_query("What are your hours?")
            
            # Verify formatting
            assert "clinic" in context.lower() or "Clinic" in context
            assert "1." in context or "2." in context  # Numbered list


@pytest.mark.asyncio
class TestSchedulingAgent:
    """
    Tests for SchedulingAgent with mocked LLM responses.
    """
    
    async def test_faq_query_detection(self):
        """Test that FAQ queries are properly detected"""
        
        # Mock to avoid needing GOOGLE_API_KEY
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'fake-key-for-testing'}):
            with patch('backend.agent.scheduling_agent.ChatGoogleGenerativeAI'):
                from backend.agent.scheduling_agent import SchedulingAgent
                
                agent = SchedulingAgent()
                
                # Should detect FAQ queries
                assert agent._check_if_faq_query("What insurance do you accept?") is True
                assert agent._check_if_faq_query("Where is the clinic located?") is True
                assert agent._check_if_faq_query("What are your hours?") is True
                assert agent._check_if_faq_query("How much does it cost?") is True
                assert agent._check_if_faq_query("What should I bring?") is True
                
                # Queries with booking intent (even if they contain FAQ keywords)
                # Note: "need" is a FAQ keyword, so this will be detected as FAQ
                assert agent._check_if_faq_query("I need to book an appointment") is True
                
                # Pure scheduling queries without FAQ keywords
                assert agent._check_if_faq_query("Book appointment for tomorrow") is False
                assert agent._check_if_faq_query("Schedule me for next week") is False
    
    async def test_chat_workflow_with_mock_llm(self):
        """Test complete chat workflow with mocked LLM response"""
        
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'fake-key-for-testing'}):
            # Mock the LLM
            mock_llm = Mock()
            mock_response = Mock()
            mock_response.content = "I'd be happy to help you schedule an appointment. What type of appointment do you need?"
            mock_response.tool_calls = None
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            
            with patch('backend.agent.scheduling_agent.ChatGoogleGenerativeAI') as mock_llm_class:
                mock_llm_instance = Mock()
                mock_llm_instance.bind_tools.return_value = mock_llm
                mock_llm_class.return_value = mock_llm_instance
                
                from backend.agent.scheduling_agent import SchedulingAgent
                
                agent = SchedulingAgent()
                agent.llm = mock_llm
                
                result = await agent.process_message("I need to book an appointment")
                
                assert "response" in result
                assert "conversation_history" in result
                assert "metadata" in result
                assert isinstance(result["response"], str)
                assert len(result["conversation_history"]) == 2
                assert result["conversation_history"][0]["role"] == "user"
                assert result["conversation_history"][1]["role"] == "assistant"
    
    async def test_chat_workflow_with_faq(self):
        """Test chat workflow with FAQ query (should include RAG context)"""
        
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'fake-key-for-testing'}):
            # Mock LLM
            mock_llm = Mock()
            mock_response = Mock()
            mock_response.content = "We accept Blue Cross Blue Shield, Aetna, Cigna, and several other major insurance providers."
            mock_response.tool_calls = None
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            
            # Mock FAQ retrieval
            mock_faq = Mock()
            mock_faq.get_context_for_query.return_value = "Accepted Insurance: Blue Cross Blue Shield, Aetna, Cigna"
            
            with patch('backend.agent.scheduling_agent.ChatGoogleGenerativeAI') as mock_llm_class:
                mock_llm_instance = Mock()
                mock_llm_instance.bind_tools.return_value = mock_llm
                mock_llm_class.return_value = mock_llm_instance
                
                with patch('backend.agent.scheduling_agent.FAQRetrieval', return_value=mock_faq):
                    from backend.agent.scheduling_agent import SchedulingAgent
                    
                    agent = SchedulingAgent()
                    agent.llm = mock_llm
                    
                    result = await agent.process_message("What insurance do you accept?")
                    
                    assert result["metadata"]["used_faq"] is True
                    assert "response" in result
    
    async def test_chat_workflow_with_tool_calls(self):
        """Test chat workflow when LLM decides to use tools"""
        
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'fake-key-for-testing'}):
            # Mock LLM initial response with tool call
            mock_response_with_tool = Mock()
            mock_response_with_tool.tool_calls = [
                {
                    "name": "check_availability",
                    "args": {"date": "2025-11-30", "appointment_type": "consultation"},
                    "id": "call_123"
                }
            ]
            
            # Mock LLM final response after tool execution
            mock_final_response = Mock()
            mock_final_response.content = "I found available slots on November 30th at 9:00 AM, 10:00 AM, and 2:00 PM."
            mock_final_response.tool_calls = None
            
            mock_llm = Mock()
            mock_llm.ainvoke = AsyncMock(side_effect=[mock_response_with_tool, mock_final_response])
            
            # Mock the availability tool
            mock_tool = Mock()
            mock_tool.ainvoke = AsyncMock(return_value=json.dumps({
                "available": True,
                "date": "2025-11-30",
                "available_slots": ["09:00", "10:00", "14:00"]
            }))
            
            with patch('backend.agent.scheduling_agent.ChatGoogleGenerativeAI') as mock_llm_class:
                mock_llm_instance = Mock()
                mock_llm_instance.bind_tools.return_value = mock_llm
                mock_llm_class.return_value = mock_llm_instance
                
                from backend.agent.scheduling_agent import SchedulingAgent
                
                agent = SchedulingAgent()
                agent.llm = mock_llm
                agent.tools["check_availability"] = mock_tool
                
                result = await agent.process_message("Check availability for November 30th")
                
                assert result["metadata"]["tools_used"] == 1
                assert "response" in result
                mock_tool.ainvoke.assert_called_once()


class TestDataIntegrity:
    """Tests for data files and configuration"""
    
    def test_clinic_info_structure(self):
        """Test that clinic_info.json has all required sections"""
        assert os.path.exists("data/clinic_info.json")
        with open("data/clinic_info.json", "r") as f:
            data = json.load(f)
            
            # Verify main sections
            assert "clinic_details" in data
            assert "insurance_and_billing" in data
            assert "policies" in data
            assert "appointment_types" in data
            assert "visit_preparation" in data
            
            # Verify clinic details
            clinic = data["clinic_details"]
            assert "name" in clinic
            assert "address" in clinic
            assert "phone" in clinic
            assert "hours" in clinic
            
            # Verify appointment types
            apt_types = data["appointment_types"]
            assert "general_consultation" in apt_types
            assert "followup" in apt_types
            assert "physical_exam" in apt_types
            assert "specialist_consultation" in apt_types
            
            # Verify each appointment type has required fields
            for apt_type in apt_types.values():
                assert "duration" in apt_type
                assert "description" in apt_type
    
    def test_doctor_schedule_structure(self):
        """Test that doctor_schedule.json has correct structure"""
        assert os.path.exists("data/doctor_schedule.json")
        with open("data/doctor_schedule.json", "r") as f:
            data = json.load(f)
            
            assert "doctor_info" in data
            assert "working_hours" in data
            assert "lunch_break" in data
            assert "booked_appointments" in data
            
            # Verify working hours structure
            hours = data["working_hours"]
            assert "monday" in hours
            assert "sunday" in hours
            
            # Verify lunch break
            lunch = data["lunch_break"]
            assert "start" in lunch
            assert "end" in lunch
            
            # Verify booked appointments structure
            if data["booked_appointments"]:
                appt = data["booked_appointments"][0]
                assert "date" in appt
                assert "start_time" in appt
                assert "end_time" in appt
                assert "appointment_type" in appt
    
    def test_appointment_types_have_valid_durations(self):
        """Test that all appointment types have valid duration values"""
        with open("data/clinic_info.json", "r") as f:
            data = json.load(f)
            apt_types = data["appointment_types"]
            
            for apt_name, apt_info in apt_types.items():
                duration = apt_info["duration"]
                assert isinstance(duration, int)
                assert duration > 0
                assert duration <= 120  # Reasonable max duration


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
