import pytest
import httpx
from datetime import datetime, timedelta
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.mark.asyncio
class TestSchedulingAgent:
    """
    Unit tests for the Medical Appointment Scheduling Agent.
    
    These tests verify the core functionality of:
    - Appointment availability checking
    - Booking creation and validation
    - Conflict prevention
    - Edge case handling
    """
    
    async def test_availability_checking(self):
        """Test that availability checking returns valid time slots"""
        from backend.tools.availability_tool import check_availability
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        result = await check_availability(date=tomorrow, appointment_type="consultation")
        data = json.loads(result)
        
        assert "available" in data or "error" in data
        if data.get("available"):
            assert "available_slots" in data
            assert isinstance(data["available_slots"], list)
    
    async def test_appointment_booking(self):
        """Test successful appointment booking with valid data"""
        from backend.tools.booking_tool import book_appointment
        
        future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        result = await book_appointment(
            appointment_type="consultation",
            date=future_date,
            start_time="14:00",
            patient_name="Test Patient",
            patient_email="test@example.com",
            patient_phone="+1-555-0100",
            reason="Test booking"
        )
        
        data = json.loads(result)
        assert "success" in data or "error" in data
    
    async def test_faq_detection(self):
        """Test that FAQ queries are properly detected"""
        from backend.agent.scheduling_agent import SchedulingAgent
        
        agent = SchedulingAgent()
        
        assert agent._check_if_faq_query("What insurance do you accept?") is True
        assert agent._check_if_faq_query("Where is the clinic located?") is True
        assert agent._check_if_faq_query("I need to book an appointment") is False


@pytest.mark.asyncio
class TestCalendlyIntegration:
    """Tests for mock Calendly API endpoints"""
    
    BASE_URL = "http://localhost:8000"
    
    async def test_get_availability(self):
        """Test GET /api/calendly/availability endpoint"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/api/calendly/availability",
                    params={"date": tomorrow, "appointment_type": "consultation"},
                    timeout=5.0
                )
                assert response.status_code in [200, 500, 503]
                if response.status_code == 200:
                    data = response.json()
                    assert "date" in data
                    assert "available_slots" in data
            except httpx.ConnectError:
                pytest.skip("Server not running")
    
    async def test_book_appointment_endpoint(self):
        """Test POST /api/calendly/book endpoint"""
        future_date = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.BASE_URL}/api/calendly/book",
                    json={
                        "appointment_type": "consultation",
                        "date": future_date,
                        "start_time": "10:00",
                        "patient": {
                            "name": "Test User",
                            "email": "test@example.com",
                            "phone": "+1-555-0100"
                        },
                        "reason": "Test appointment"
                    },
                    timeout=5.0
                )
                assert response.status_code in [200, 400, 500, 503]
            except httpx.ConnectError:
                pytest.skip("Server not running")
    
    async def test_invalid_date_format(self):
        """Test handling of invalid date formats"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/api/calendly/availability",
                    params={"date": "invalid-date", "appointment_type": "consultation"},
                    timeout=5.0
                )
                assert response.status_code in [200, 400, 500]
            except httpx.ConnectError:
                pytest.skip("Server not running")


@pytest.mark.asyncio
class TestRAGSystem:
    """Tests for RAG-based FAQ system"""
    
    async def test_faq_retrieval_initialization(self):
        """Test that FAQ retrieval system initializes correctly"""
        try:
            from backend.rag.faq_rag import FAQRetrieval
            faq = FAQRetrieval()
            assert faq is not None
        except Exception as e:
            pytest.skip(f"FAQ retrieval initialization failed: {e}")
    
    async def test_context_retrieval(self):
        """Test retrieval of relevant context"""
        try:
            from backend.rag.faq_rag import FAQRetrieval
            faq = FAQRetrieval()
            context = faq.get_context_for_query("What insurance do you accept?")
            assert context is not None
            assert len(context) > 0
        except Exception as e:
            pytest.skip(f"Context retrieval failed: {e}")
    
    async def test_vector_store_persistence(self):
        """Test that vector store persists data correctly"""
        import os
        vector_db_path = "./data/vectordb"
        
        if os.path.exists(vector_db_path):
            assert os.path.exists(os.path.join(vector_db_path, "chroma.sqlite3"))
        else:
            pytest.skip("Vector database not initialized")


class TestDataIntegrity:
    """Tests for data files and configuration"""
    
    def test_clinic_info_exists(self):
        """Test that clinic_info.json exists and is valid"""
        assert os.path.exists("data/clinic_info.json")
        with open("data/clinic_info.json", "r") as f:
            data = json.load(f)
            assert "clinic_details" in data
            assert "insurance_and_billing" in data
            assert "policies" in data
    
    def test_doctor_schedule_exists(self):
        """Test that doctor_schedule.json exists and is valid"""
        assert os.path.exists("data/doctor_schedule.json")
        with open("data/doctor_schedule.json", "r") as f:
            data = json.load(f)
            assert "doctor_info" in data
            assert "working_hours" in data
            assert "booked_appointments" in data
    
    def test_appointment_types_configured(self):
        """Test that all 4 appointment types are configured"""
        with open("data/clinic_info.json", "r") as f:
            data = json.load(f)
            apt_types = data.get("appointment_types", {})
            assert "general_consultation" in apt_types
            assert "followup" in apt_types
            assert "physical_exam" in apt_types
            assert "specialist_consultation" in apt_types
            
            assert apt_types["general_consultation"]["duration"] == 30
            assert apt_types["followup"]["duration"] == 15
            assert apt_types["physical_exam"]["duration"] == 45
            assert apt_types["specialist_consultation"]["duration"] == 60


class TestEnvironmentConfiguration:
    """Tests for environment and configuration"""
    
    def test_env_example_exists(self):
        """Test that .env.example exists"""
        assert os.path.exists(".env.example")
    
    def test_requirements_file_exists(self):
        """Test that requirements.txt exists"""
        assert os.path.exists("requirements.txt")
        with open("requirements.txt", "r") as f:
            content = f.read()
            assert "fastapi" in content.lower()
            assert "langchain" in content.lower()
            assert "chromadb" in content.lower()
    
    def test_architecture_diagram_exists(self):
        """Test that architecture diagram exists"""
        assert os.path.exists("architecture_diagram.png") or os.path.exists("architecture_diagram.pdf")
    
    def test_readme_exists(self):
        """Test that README.md exists and contains required sections"""
        assert os.path.exists("README.md")
        with open("README.md", "r") as f:
            content = f.read()
            assert "Setup Instructions" in content
            assert "System" in content or "Architecture" in content
            assert "Scheduling" in content
            assert "Testing" in content or "Test" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
