# Deployment Guide - Medical Appointment Scheduling Agent

## Pre-Deployment Checklist

### 1. Environment Variables
Ensure the following environment variables are set in your production environment:

```bash
OPENAI_API_KEY=your-openai-api-key-here
LLM_MODEL=gpt-4o-mini  # Optional, defaults to gpt-4o-mini
BACKEND_PORT=8000      # Optional, defaults to 8000
```

### 2. Dependencies

**Backend (Python):**
All dependencies are listed in `requirements.txt`. Install with:
```bash
pip install -r requirements.txt
```

**Frontend (Node.js):**
```bash
cd frontend
npm install
```

### 3. Data Files
Ensure these data files exist in the `data/` directory:
- `clinic_info.json` - Clinic information, FAQ data, insurance details
- `doctor_schedule.json` - Doctor working hours and pre-booked appointments

The system will automatically create:
- `appointments.json` - Runtime storage for new bookings
- `vectordb/` - ChromaDB vector database for FAQ embeddings

### 4. Running the Application

**Development Mode:**

Terminal 1 - Backend:
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

**Production Mode:**

Backend (with production-ready settings):
```bash
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

Frontend (build and serve):
```bash
cd frontend
npm run build
# Serve the dist/ folder with your preferred static file server
```

### 5. Health Checks

Verify the backend is running:
```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Medical Appointment Scheduling Agent",
  "version": "1.0.0"
}
```

### 6. API Quota Management

The system implements graceful degradation for OpenAI API quota limitations:

- **Lazy Initialization**: RAG system only initializes when first FAQ query is made
- **Fallback Mechanism**: If embeddings fail, system falls back to keyword-based search in JSON data
- **Error Handling**: Users receive friendly fallback messages with phone contact information

**Best Practices:**
- Monitor OpenAI usage in your dashboard
- Consider pre-generating embeddings in a separate initialization step
- Implement caching for frequently asked questions
- Use environment variable to toggle between OpenAI and local embeddings if needed

### 7. Security Considerations

**For Production:**
- [ ] Use HTTPS for all communications
- [ ] Restrict CORS origins to your production domain
- [ ] Implement rate limiting on API endpoints
- [ ] Use environment variables for all secrets (never commit to git)
- [ ] Enable authentication/authorization if needed
- [ ] Regularly rotate API keys
- [ ] Monitor for unusual usage patterns

**Update CORS Settings** in `backend/main.py`:
```python
# Change from:
origins = ["*"]

# To:
origins = [
    "https://yourdomain.com",
    "https://www.yourdomain.com"
]
```

### 8. Monitoring & Logging

**Key Metrics to Monitor:**
- API response times
- OpenAI API usage and costs
- Error rates
- User conversation completion rates
- Appointment booking success rates

**Logging:**
- Backend logs are written to stdout by uvicorn
- Consider implementing structured logging (e.g., using Python's `logging` module with JSON formatter)
- Set up log aggregation (e.g., CloudWatch, Datadog, ELK stack)

### 9. Database Backups

Although this implementation uses file-based storage, ensure regular backups:

```bash
# Backup data files
tar -czf backup-$(date +%Y%m%d).tar.gz data/clinic_info.json data/doctor_schedule.json data/appointments.json

# Backup vector database
tar -czf vectordb-backup-$(date +%Y%m%d).tar.gz data/vectordb/
```

### 10. Testing Before Deployment

Run the following tests:

1. **FAQ Functionality:**
   - Ask about insurance
   - Ask about clinic hours
   - Ask about what to bring

2. **Appointment Booking:**
   - Book a 30-minute consultation
   - Book a 15-minute follow-up
   - Book a 45-minute physical exam
   - Book a 60-minute specialist consultation

3. **Edge Cases:**
   - Try to book in the past
   - Try to book during lunch (12:00-13:00)
   - Try to book on Sunday (closed)
   - Ask for slots when none are available

4. **Context Switching:**
   - Start booking, ask FAQ mid-flow, continue booking
   - Ensure conversation history is maintained

## Scaling Considerations

### Horizontal Scaling
- Use a load balancer (e.g., nginx, AWS ALB) to distribute traffic
- Run multiple backend instances
- Share data files via network storage or migrate to a database

### Database Migration
For production scale, consider migrating from file-based storage to:
- **PostgreSQL** for appointments and schedules
- **Redis** for caching frequently accessed data
- **Pinecone** or **Weaviate** for vector storage (instead of ChromaDB)

### Performance Optimization
- Implement response caching for common FAQ queries
- Pre-generate embeddings during deployment
- Use connection pooling for database connections
- Implement request queuing for high traffic

## Troubleshooting

### Backend Won't Start
1. Check environment variables are set
2. Verify OPENAI_API_KEY is valid
3. Check port 8000 is not in use: `lsof -i :8000`
4. Review logs for errors

### Frontend Shows Connection Error
1. Verify backend is running on port 8000
2. Check CORS configuration in backend
3. Verify axios baseURL in frontend code
4. Check browser console for detailed errors

### Embeddings Fail
1. Check OpenAI API quota in dashboard
2. Verify API key has embedding permissions
3. System should fall back gracefully - check logs for fallback messages
4. Consider pre-generating embeddings offline

### Appointments Not Saving
1. Check write permissions on `data/` directory
2. Verify `data/appointments.json` exists and is writable
3. Check backend logs for file I/O errors

## Support & Maintenance

### Regular Maintenance Tasks
- [ ] Weekly: Review appointment data and archive old appointments
- [ ] Weekly: Check OpenAI API usage and costs
- [ ] Monthly: Update clinic information and FAQ data
- [ ] Monthly: Review and update doctor schedules
- [ ] Quarterly: Update dependencies and security patches

### Updating FAQ Knowledge Base
1. Edit `data/clinic_info.json` with new information
2. Delete `data/vectordb/` directory
3. Restart backend - embeddings will be regenerated on first FAQ query

### Adding New Appointment Types
1. Update `backend/api/calendly_integration.py` with new type and duration
2. Update frontend to display new type if needed
3. Update `data/clinic_info.json` with information about new type
4. Test thoroughly before deploying

## Contact & Support
For technical issues or questions, contact the development team or refer to README.md for detailed system documentation.
