# Deploying Medical Appointment Scheduling Agent on Render

This guide will help you deploy your Medical Appointment Scheduling Agent on Render.com.

## Prerequisites

- A Render account (sign up at https://dashboard.render.com/)
- Your code in a Git repository (GitHub, GitLab, or Bitbucket)
- Google API Key (for Gemini AI)

## Deployment Steps

### Step 1: Push Your Code to Git

Make sure all your code is committed and pushed to your Git repository:

```bash
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### Step 2: Create a New Web Service on Render

1. Log in to your Render account at https://dashboard.render.com/
2. Click the **"New +"** button in the top right
3. Select **"Web Service"**

### Step 3: Connect Your Repository

1. Choose your Git provider (GitHub, GitLab, or Bitbucket)
2. Authorize Render to access your repositories
3. Select the repository containing your app
4. Click **"Connect"**

### Step 4: Configure Your Service

Fill in the following settings:

**Basic Settings:**
- **Name**: `medical-appointment-agent` (or your preferred name)
- **Region**: Choose the closest region to your users
- **Branch**: `main` (or your default branch)
- **Runtime**: **Python 3**

**Build & Deploy:**
- **Root Directory**: Leave blank (unless your app is in a subdirectory)
- **Build Command**: 
  ```bash
  chmod +x build.sh && ./build.sh
  ```
- **Start Command**:
  ```bash
  uvicorn backend.main:app --host 0.0.0.0 --port $PORT
  ```

**Instance Type:**
- Select **Free** plan (or choose a paid plan for better performance)

### Step 5: Add Environment Variables

In the **Environment** section, add the following environment variables:

| Key | Value | Notes |
|-----|-------|-------|
| `PYTHON_VERSION` | `3.11.0` | Python runtime version |
| `NODE_VERSION` | `20.11.0` | **Required**: Node.js for building frontend |
| `LLM_MODEL` | `gemini-2.5-flash` | AI model to use |
| `LLM_PROVIDER` | `google` | LLM provider |
| `GOOGLE_API_KEY` | `your-actual-api-key` | **CRITICAL**: Your Google Gemini API key - app won't work without this! |

**⚠️ CRITICAL**: You MUST add your actual Google API Key for the app to work! Without it, deployment will fail or the app won't function.

**⚠️ IMPORTANT**: Add `NODE_VERSION=20.11.0` to ensure Node.js is available during build. This is required to build the React frontend.

### Step 6: Deploy

1. Review all settings
2. Click **"Create Web Service"**
3. Render will start building and deploying your app

The deployment process will:
- Install Node.js dependencies
- Build your React frontend
- Install Python dependencies
- Start your FastAPI server

This typically takes 3-5 minutes for the first deployment.

### Step 7: Access Your App

Once deployment is complete:
- Your app will be live at: `https://medical-appointment-agent.onrender.com`
- You can view logs in the **Logs** tab
- Check deployment status in the **Events** tab

## Using render.yaml (Blueprint Method - Recommended)

The included `render.yaml` file provides automatic configuration. This is the EASIEST method:

1. **Push the `render.yaml` file to your repository**
   ```bash
   git add render.yaml build.sh
   git commit -m "Add Render deployment config"
   git push origin main
   ```

2. **Create Blueprint in Render**
   - In Render dashboard, click **"New +"** → **"Blueprint"**
   - Connect your repository
   - Render will automatically read the configuration from `render.yaml`

3. **⚠️ CRITICAL: Add GOOGLE_API_KEY**
   - **BEFORE clicking "Apply"**, you MUST add your Google API Key:
   - In the Blueprint setup page, find the environment variables section
   - Add: `GOOGLE_API_KEY` = `your-actual-google-gemini-api-key`
   - Without this, your deployment will fail or the app won't function!

4. **Click "Apply" to deploy**
   - Render will build and deploy your app
   - All other settings are pre-configured in `render.yaml`

## Troubleshooting

### Build Fails
- Check the **Logs** tab for error messages
- Ensure all dependencies are listed in `requirements.txt` and `frontend/package.json`
- Verify your build command is correct
- **If you see "npm: command not found"**: Add `NODE_VERSION=20.11.0` to your environment variables
- **If frontend build fails**: Ensure `NODE_VERSION` is set in environment variables

### App Doesn't Start
- Check that your `GOOGLE_API_KEY` is set correctly
- Review logs for startup errors
- Ensure the start command uses the correct port: `$PORT`

### Slow Performance (Free Tier)
- Free tier instances spin down after 15 minutes of inactivity
- First request after inactivity may take 30-60 seconds (cold start)
- Consider upgrading to a paid plan for production use

### API Errors
- Verify your Google API Key is valid and has quota
- Check that all required environment variables are set
- Review application logs for specific error messages

## Monitoring Your Deployment

Render provides several monitoring tools:

- **Logs**: Real-time application logs
- **Metrics**: CPU, memory, and bandwidth usage
- **Events**: Deployment history and status
- **Shell**: Access to your service's shell (paid plans)

## Updating Your App

To deploy updates:

1. Push changes to your Git repository
2. Render will automatically detect changes and redeploy
3. Or manually trigger a deploy from the Render dashboard

## Environment Variables Management

You can update environment variables without redeploying:

1. Go to your service in Render dashboard
2. Navigate to **Environment** tab
3. Add/edit/remove variables
4. Changes take effect immediately (may require a restart)

## Custom Domain (Optional)

To use a custom domain:

1. Go to **Settings** → **Custom Domain**
2. Add your domain name
3. Update your DNS records as instructed
4. Render will automatically provision SSL certificate

## Cost Information

- **Free Tier**: 
  - 750 hours per month
  - Spins down after 15 minutes of inactivity
  - 512 MB RAM, shared CPU

- **Paid Plans**: Start at $7/month for always-on service with more resources

## Support

If you need help:
- Render Documentation: https://render.com/docs
- Community Forum: https://community.render.com
- Email Support: support@render.com

## Next Steps

After successful deployment:

1. Test all functionality on your live URL
2. Set up custom domain (optional)
3. Monitor logs and performance
4. Consider upgrading to paid plan for production use

---

**Your Medical Appointment Scheduling Agent is now live on Render! 🚀**
