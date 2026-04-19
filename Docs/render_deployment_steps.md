# Render Backend Deployment Steps

## Step 1: Prepare Your Repository

✅ **Already Done:**
- Repository initialized and pushed to GitHub
- Backend code is in `apps/api/` directory
- Health check endpoint exists at `/health`
- Requirements.txt is properly configured

## Step 2: Create Render Account

1. **Go to [render.com](https://render.com)**
2. **Sign up** with your GitHub account
3. **Verify your email address**

## Step 3: Create Web Service

### 3.1 Navigate to Dashboard
- Click **"New +"** in the Render dashboard
- Select **"Web Service"**

### 3.2 Connect Repository
- **Choose your GitHub repository**: `Akash1122-cl/Milestone-`
- **Select branch**: `main`
- **Set Root Directory**: `apps/api`

### 3.3 Configure Service Settings
```
Name: mutual-fund-api
Runtime: Python 3
Plan: Free (to start)
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
Health Check Path: /health
```

### 3.4 Advanced Settings (Optional)
- **Instance Type**: Free (512MB RAM, shared CPU)
- **Auto-Deploy**: ✅ Enabled (deploy on push to main)
- **Health Check**: Enabled (every 30 seconds)

## Step 4: Configure Environment Variables

In your Render service dashboard, go to **Environment** tab and add these variables:

```bash
# Required API Keys
CHROMA_API_KEY=your_chroma_cloud_api_key
CHROMA_TENANT=your_chroma_tenant
CHROMA_DATABASE=your_chroma_database
GOOGLE_API_KEY=your_google_gemini_api_key

# Python Configuration
PYTHON_VERSION=3.10
```

**Important Notes:**
- Don't use quotes around values
- Keep these secret and don't commit them to git
- Get these values from your Chroma Cloud and Google Gemini accounts

## Step 5: Deploy Backend

1. **Click "Create Web Service"**
2. **Wait for deployment** (2-3 minutes)
3. **Monitor build logs** for any errors

## Step 6: Test Deployment

### 6.1 Health Check
```bash
curl https://your-service-name.onrender.com/health
```
Expected response: `{"status": "healthy"}`

### 6.2 API Test
```bash
curl -X POST https://your-service-name.onrender.com/api/chat/query \
-H "Content-Type: application/json" \
-d '{"thread_id": "test", "query": "What is expense ratio?"}'
```

### 6.3 Documentation Test
Visit: `https://your-service-name.onrender.com/docs`
- Should show FastAPI auto-generated documentation
- Test the API endpoints from the UI

## Step 7: Update CORS Configuration

After deployment, update the CORS settings in `apps/api/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://your-vercel-app.vercel.app",  # Your Vercel frontend (add this later)
        "*"  # Remove this in production for better security
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Step 8: Troubleshooting Common Issues

### Issue 1: Build Fails
**Symptoms**: Build error during deployment
**Solutions**:
1. Check `requirements.txt` for correct dependencies
2. Verify all Python files have correct syntax
3. Review build logs in Render dashboard

### Issue 2: Health Check Fails
**Symptoms**: Service starts but health check fails
**Solutions**:
1. Verify `/health` endpoint exists
2. Check for import errors in main.py
3. Review service logs

### Issue 3: API Calls Fail
**Symptoms**: Health check passes but API calls fail
**Solutions**:
1. Check environment variables are set correctly
2. Verify Chroma Cloud connectivity
3. Check Google Gemini API key validity

### Issue 4: CORS Errors
**Symptoms**: Frontend can't connect to backend
**Solutions**:
1. Update CORS origins in main.py
2. Add your Vercel URL to allowed origins
3. Remove "*" from origins in production

## Step 9: Production Considerations

### Security
- ✅ Remove `"*"` from CORS origins
- ✅ Use HTTPS (automatic on Render)
- ✅ Keep API keys in environment variables
- ✅ Monitor API usage and costs

### Performance
- ✅ Monitor response times
- ✅ Consider upgrading to paid plan if needed
- ✅ Set up monitoring alerts
- ✅ Implement rate limiting if needed

### Monitoring
- ✅ Check Render dashboard logs
- ✅ Monitor API response times
- ✅ Track error rates
- ✅ Set up alerts for downtime

## Step 10: Save Your URLs

After successful deployment, save these URLs:

```bash
# Backend URLs
Backend URL: https://your-service-name.onrender.com
Health Check: https://your-service-name.onrender.com/health
API Documentation: https://your-service-name.onrender.com/docs
API Endpoint: https://your-service-name.onrender.com/api/chat/query
```

## Next Steps

After backend deployment is complete:

1. **Deploy frontend on Vercel** (using backend URL)
2. **Test end-to-end functionality**
3. **Set up GitHub Actions scheduler**
4. **Configure monitoring and alerts**

---

## Quick Reference Commands

```bash
# Test health check
curl https://your-service-name.onrender.com/health

# Test API endpoint
curl -X POST https://your-service-name.onrender.com/api/chat/query \
-H "Content-Type: application/json" \
-d '{"thread_id": "test", "query": "What is expense ratio?"}'

# Check service logs (in Render dashboard)
# Navigate to Service > Logs tab
```

---

*Last Updated: April 19, 2026*
*Version: 1.0*
