# Render Deployment Checklist

Follow these steps to deploy your Medical Appointment Scheduling Agent on Render:

## ✅ Pre-Deployment Checklist

- [ ] **Git Repository**: Your code must be in a Git repository (GitHub, GitLab, or Bitbucket)
- [ ] **Google API Key**: Have your Google Gemini API key ready
- [ ] **Render Account**: Sign up at https://dashboard.render.com/

## 📋 Required Files (Already Created!)

- [x] `build.sh` - Build script for frontend and backend
- [x] `render.yaml` - Render configuration file
- [x] `requirements.txt` - Python dependencies
- [x] `frontend/package.json` - Node.js dependencies
- [x] `data/clinic_info.json` - Clinic information
- [x] `data/doctor_schedule.json` - Doctor availability

## 🚀 Deployment Steps

### Option 1: Using render.yaml (Recommended)

1. **Push your code to Git**
   ```bash
   git add .
   git commit -m "Ready for Render deployment"
   git push origin main
   ```

2. **Create Blueprint on Render**
   - Go to https://dashboard.render.com/
   - Click **"New +"** → **"Blueprint"**
   - Connect your repository
   - Render will automatically read `render.yaml`

3. **⚠️ CRITICAL: Add Environment Variables**
   - **BEFORE clicking "Apply"**, you MUST add:
     - Key: `GOOGLE_API_KEY` / Value: Your actual Google Gemini API key
     - **Without this, deployment will fail!**
   - Verify that `NODE_VERSION` is set (should be in render.yaml)

4. **Deploy**
   - Click **"Apply"** or **"Deploy"**
   - Wait 3-5 minutes for first deployment

### Option 2: Manual Setup

1. **Push your code to Git** (same as above)

2. **Create Web Service**
   - Go to https://dashboard.render.com/
   - Click **"New +"** → **"Web Service"**
   - Connect your repository

3. **Configure Settings**
   - **Name**: `medical-appointment-agent`
   - **Runtime**: Python 3
   - **Build Command**: 
     ```bash
     chmod +x build.sh && ./build.sh
     ```
   - **Start Command**: 
     ```bash
     uvicorn backend.main:app --host 0.0.0.0 --port $PORT
     ```

4. **Add Environment Variables** (⚠️ CRITICAL STEP)
   - `PYTHON_VERSION`: `3.11.0`
   - `NODE_VERSION`: `20.11.0` (Required for frontend build!)
   - `LLM_MODEL`: `gemini-2.5-flash`
   - `LLM_PROVIDER`: `google`
   - `GOOGLE_API_KEY`: Your actual API key (MUST ADD THIS!)

5. **Select Plan**: Free or Paid

6. **Deploy**: Click **"Create Web Service"**

## 🔍 Post-Deployment Verification

After deployment completes:

1. **Check Logs**
   - Go to the **Logs** tab
   - Look for "Application startup complete"
   - Verify no errors

2. **Test Your App**
   - Visit your app URL: `https://your-app-name.onrender.com`
   - Try booking an appointment
   - Ask some FAQ questions

3. **Monitor Performance**
   - Check the **Metrics** tab for resource usage
   - Review the **Events** tab for deployment history

## ⚠️ Important Notes

- **Free Tier Limitation**: Free tier spins down after 15 minutes of inactivity
- **Cold Starts**: First request after inactivity may take 30-60 seconds
- **API Key**: Make sure your Google API key has sufficient quota
- **Port**: Always use `$PORT` environment variable (Render assigns this automatically)

## 🐛 Troubleshooting

### Build Fails
- Check Logs tab for specific errors
- Verify all files are committed to git
- Ensure `build.sh` is executable

### App Won't Start
- Verify `GOOGLE_API_KEY` is set correctly
- Check that start command uses `$PORT`
- Review logs for Python/Node errors

### API Errors
- Confirm Google API key is valid
- Check API quota hasn't been exceeded
- Verify network connectivity in logs

## 📚 Detailed Instructions

For complete step-by-step instructions with screenshots and troubleshooting, see:
- **[RENDER_DEPLOYMENT.md](./RENDER_DEPLOYMENT.md)**

## 🆘 Need Help?

- **Render Docs**: https://render.com/docs
- **Render Community**: https://community.render.com
- **Support**: support@render.com

---

**Ready to deploy? Follow Option 1 above for the easiest deployment! 🚀**
