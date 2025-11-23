# Quick Setup and Run Guide

## 🚀 Get Started in 5 Minutes

### Option 1: Run on Replit (Easiest - Recommended)

This project is already configured for Replit. Just follow these steps:

#### Step 1: Set Up API Key
1. Click on the **"Secrets"** tab (🔒 icon on left sidebar)
2. Add a new secret:
   - **Key**: `GOOGLE_API_KEY`
   - **Value**: Your Google Gemini API key
3. Get your API key from: https://makersuite.google.com/app/apikey

#### Step 2: Run the Application
1. The application should start automatically
2. If not, click the **"Run"** button at the top
3. Wait for the workflow to complete (30-60 seconds)
4. The frontend will open automatically

#### Step 3: Test the Application
1. Click on the chat interface
2. Type: "I need to see a doctor"
3. Follow the conversation!

**That's it! You're done! 🎉**

---

### Option 2: Run Locally (Advanced)

If you want to run this on your own computer:

#### Prerequisites
- Python 3.10 or higher installed
- Node.js 18 or higher installed
- Terminal/Command Prompt access

#### Step 1: Install Python Dependencies

```bash
# Navigate to project directory
cd appointment-scheduling-agent

# Install Python packages
pip install -r requirements.txt
```

#### Step 2: Set Up Environment Variables

```bash
# Create .env file
echo "GOOGLE_API_KEY=your_api_key_here" > .env
echo "LLM_PROVIDER=google" >> .env
echo "LLM_MODEL=gemini-2.5-flash" >> .env
```

Replace `your_api_key_here` with your actual Google API key.

#### Step 3: Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

#### Step 4: Start Backend Server

**Open Terminal 1:**
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
```

#### Step 5: Start Frontend Server

**Open Terminal 2:**
```bash
cd frontend
npm run dev
```

You should see:
```
  VITE v6.0.1  ready in 500 ms

  ➜  Local:   http://localhost:5000/
  ➜  Network: http://0.0.0.0:5000/
```

#### Step 6: Open Application

Open your browser and go to: **http://localhost:5000**

---

## 📱 Using the Application

### Starting a Conversation

**Example 1: Schedule an Appointment**
```
You: I need to see a doctor
Bot: I'd be happy to help you schedule an appointment! What's the main reason for your visit today?
You: I've been having headaches
Bot: I understand. For persistent headaches, I'd recommend a general consultation...
[Continues with booking flow]
```

**Example 2: Ask a Question**
```
You: What insurance do you accept?
Bot: We accept most major insurance providers including Blue Cross Blue Shield, Aetna, Cigna...
You: Great! Can I schedule an appointment?
Bot: Absolutely! What brings you in?
[Starts booking flow]
```

**Example 3: Mixed Conversation**
```
You: I want to book an appointment
Bot: I'd be happy to help! What brings you in today?
You: Wait, where are you located?
Bot: [Answers location question]
Bot: Now, what brings you in today?
You: Annual checkup
[Continues booking]
```

### Appointment Types

The bot will recommend the right type based on your needs:

| Type | Duration | Best For |
|------|----------|----------|
| **General Consultation** | 30 min | New issues, checkups, general concerns |
| **Follow-up** | 15 min | Quick follow-up on previous visit |
| **Physical Exam** | 45 min | Annual physical, comprehensive exam |
| **Specialist Consultation** | 60 min | Complex issues needing specialist |

### Time Preferences

You can specify:
- **Specific dates**: "tomorrow", "next Monday", "December 25th"
- **Time of day**: "morning", "afternoon", "evening"
- **Urgency**: "as soon as possible", "this week"

---

## 🧪 Testing the Application

### Quick Functional Test

1. **Start a booking:**
   ```
   Message: "I need an appointment"
   Expected: Bot asks reason for visit
   ```

2. **Provide reason:**
   ```
   Message: "Annual checkup"
   Expected: Bot recommends consultation type, asks for date
   ```

3. **Request time:**
   ```
   Message: "Tomorrow afternoon"
   Expected: Bot shows 3-5 available slots
   ```

4. **Select slot:**
   ```
   Message: "2:00 PM"
   Expected: Bot asks for patient details
   ```

5. **Provide details:**
   ```
   Message: "John Doe, john@email.com, 555-0100, annual checkup"
   Expected: Bot confirms booking with ID and code
   ```

### Test FAQ System

```
Message: "What are your hours?"
Expected: Bot provides clinic hours from knowledge base

Message: "What should I bring to my first visit?"
Expected: Bot lists required documents

Message: "Do you accept Medicare?"
Expected: Bot confirms Medicare acceptance
```

### Test Edge Cases

```
Test 1 - No availability:
Message: "Can I see the doctor right now?"
Expected: Bot explains no slots available, offers alternatives

Test 2 - Past date:
Message: "Can I book for yesterday?"
Expected: Bot politely explains cannot book past dates

Test 3 - Ambiguous time:
Message: "I want to come at 3"
Expected: Bot clarifies AM/PM
```

---

## 🔧 Troubleshooting

### Problem: Backend won't start

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**:
```bash
pip install -r requirements.txt
```

---

**Error**: `Address already in use`

**Solution**:
```bash
# Kill process on port 8000
lsof -i :8000  # Find PID
kill -9 <PID>  # Kill process
```

---

### Problem: Frontend won't start

**Error**: `Cannot find module`

**Solution**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

---

**Error**: `Port 5000 is already allocated`

**Solution**: Edit `frontend/vite.config.js`:
```javascript
server: {
  port: 3000,  // Change from 5000 to 3000
  ...
}
```

---

### Problem: Chat not responding

**Error**: `Failed to fetch` or network error

**Solution**:
1. Check backend is running (http://localhost:8000/docs should work)
2. Check console for errors (F12 in browser)
3. Verify proxy config in `vite.config.js`

---

**Error**: `API key not found`

**Solution**:
1. Check `.env` file exists
2. Verify `GOOGLE_API_KEY` is set
3. Restart backend server
4. Test API key: https://makersuite.google.com/app/apikey

---

### Problem: Vector database error

**Error**: `Failed to load vector database`

**Solution**:
```bash
# Delete and recreate
rm -rf data/vectordb
# Restart application - it will recreate automatically
```

---

### Problem: Appointments not saving

**Error**: `Permission denied` on appointments.json

**Solution**:
```bash
# Fix permissions
chmod 664 data/appointments.json

# Or recreate file
rm data/appointments.json
echo "[]" > data/appointments.json
```

---

## 📊 Verifying Everything Works

### Health Check Endpoints

**1. Backend Health:**
```bash
curl http://localhost:8000/health
```
Expected response:
```json
{"status": "healthy", "version": "1.0.0"}
```

**2. API Documentation:**
Open: http://localhost:8000/docs

You should see interactive API documentation.

**3. Frontend:**
Open: http://localhost:5000

You should see the chat interface.

---

### Run Automated Tests

```bash
# Run all tests
pytest tests/test_agent.py -v

# Should show all tests passing
# ✓ 25+ comprehensive tests passed
```

---

## 🎯 Quick Reference

### Backend Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Frontend or API info |
| `/health` | GET | Health check |
| `/api/chat` | POST | Main chat endpoint |
| `/api/calendly/availability` | GET | Check available slots |
| `/api/calendly/book` | POST | Book appointment |
| `/docs` | GET | API documentation |

### Frontend Routes

| Route | Purpose |
|-------|---------|
| `/` | Main chat interface |

### Data Files

| File | Purpose |
|------|---------|
| `data/clinic_info.json` | FAQ knowledge base |
| `data/doctor_schedule.json` | Doctor's working hours |
| `data/appointments.json` | Booked appointments |
| `data/vectordb/` | Vector database for RAG |

---

## 🔑 Environment Variables

Required variables in `.env`:

```bash
# LLM Configuration
GOOGLE_API_KEY=your_google_api_key_here
LLM_PROVIDER=google
LLM_MODEL=gemini-2.5-flash

# Optional - with defaults
VECTOR_DB=chromadb
VECTOR_DB_PATH=./data/vectordb
CLINIC_NAME=HealthCare Plus Clinic
CLINIC_PHONE=+1-555-123-4567
BACKEND_PORT=8000
FRONTEND_PORT=5000
```

---

## 📞 Getting Help

### Check Logs

**Backend logs** (Terminal 1):
- Shows API requests
- Shows agent decisions
- Shows tool calls
- Shows errors

**Frontend logs** (Browser Console - F12):
- Shows API calls
- Shows UI errors
- Shows network issues

### Common Log Messages

✅ **Good Signs:**
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Started reloader process
```

❌ **Problem Signs:**
```
ERROR:    [Errno 48] Address already in use
WARNING:  Invalid API key
ERROR:    Failed to connect to vector database
```

---

## 🚀 Next Steps

Once you have the application running:

1. ✅ **Test all features** (see Testing section above)
2. ✅ **Review code** (see CODE_WALKTHROUGH.md)
3. ✅ **Read architecture** (see COMPLETE_IMPLEMENTATION_GUIDE.md)
4. ✅ **Prepare submission** (see SUBMISSION_CHECKLIST.md)

---

## 💡 Tips for Best Experience

1. **Use clear, natural language**
   - Good: "I need to see a doctor tomorrow afternoon for headaches"
   - Works: "appointment tomorrow"

2. **Provide complete information**
   - Good: "John Doe, john@email.com, 555-1234"
   - Works but slower: "John Doe" [bot asks for more]

3. **Be specific about dates**
   - Good: "next Monday", "December 25th"
   - Works: "soon", "next week"

4. **Ask questions anytime**
   - The bot can switch between scheduling and FAQs seamlessly

---

**Ready to start? Let's go! 🎉**
