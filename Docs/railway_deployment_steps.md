# Railway Backend Deployment Steps

## Step 1: Prepare Your Repository

### 1.1 Check Current Status
- Repository: https://github.com/Akash1122-cl/Milestone-
- Backend code in: `apps/api/`
- Health check endpoint: `/health`
- Requirements.txt: Configured

### 1.2 Railway Configuration Files
- `railway.toml` - Root configuration
- `apps/api/railway.json` - Service-specific configuration

## Step 2: Create Railway Account

1. **Go to [railway.app](https://railway.app)**
2. **Sign up** with your GitHub account
3. **Verify your email address**
4. **Install Railway CLI** (optional but recommended):
   ```bash
   npm install -g @railway/cli
   railway login
   ```

## Step 3: Create New Project

### 3.1 Using Railway Dashboard
1. **Click "New Project"** in Railway dashboard
2. **Choose "Deploy from GitHub repo"**
3. **Select your repository**: `Akash1122-cl/Milestone-`

### 3.2 Using Railway CLI (Alternative)
```bash
railway login
railway new
# Select your repository when prompted
```

## Step 4: Configure Service

### 4.1 Service Settings
```
Service Name: mutual-fund-api
Environment: Production
Root Directory: apps/api
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
Health Check: /health
```

### 4.2 Python Configuration
- **Runtime**: Python 3.10
- **Region**: Choose nearest (US East, EU West, etc.)
- **Plan**: Free tier to start

## Step 5: Configure Environment Variables

In your Railway service dashboard, go to **Variables** tab and add:

```bash
# Required API Keys
CHROMA_API_KEY=your_chroma_cloud_api_key
CHROMA_TENANT=your_chroma_tenant
CHROMA_DATABASE=your_chroma_database
GOOGLE_API_KEY=your_google_gemini_api_key

# Python Configuration
PYTHON_VERSION=3.10
PORT=8000
```

**Important Notes:**
- Get these values from your Chroma Cloud and Google Gemini accounts
- Don't use quotes around values
- Railway automatically sets PORT variable

## Step 6: Deploy Backend

### 6.1 Automatic Deployment
- Railway will automatically deploy when you push to main branch
- Monitor build logs in Railway dashboard
- Wait for deployment to complete (2-3 minutes)

### 6.2 Manual Deployment (if needed)
```bash
railway up
# Or use dashboard to trigger redeploy
```

## Step 7: Test Deployment

### 7.1 Get Your Railway URL
After deployment, Railway will provide a URL like:
```
https://your-service-name.up.railway.app
```

### 7.2 Health Check Test
```bash
curl https://your-service-name.up.railway.app/health
```
Expected response: `{"status": "healthy"}`

### 7.3 API Documentation Test
Visit: `https://your-service-name.up.railway.app/docs`
- Should show FastAPI auto-generated documentation
- Test API endpoints from the UI

### 7.4 API Endpoint Test
```bash
curl -X POST https://your-service-name.up.railway.app/api/chat/query \
-H "Content-Type: application/json" \
-d '{"thread_id": "test", "query": "What is expense ratio?"}'
```

## Step 8: Update CORS Configuration

After deployment, update CORS settings in `apps/api/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://your-vercel-app.vercel.app",  # Your Vercel frontend (add this later)
        "https://*.up.railway.app",  # Allow all Railway subdomains
        "*"  # Remove this in production for better security
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Step 9: Troubleshooting Common Issues

### Issue 1: Build Fails
**Symptoms**: Build error during deployment
**Solutions**:
1. Check `requirements.txt` for correct dependencies
2. Verify all Python files have correct syntax
3. Review build logs in Railway dashboard
4. Check `railway.toml` configuration

### Issue 2: Health Check Fails
**Symptoms**: Service starts but health check fails
**Solutions**:
1. Verify `/health` endpoint exists and returns JSON
2. Check for import errors in main.py
3. Review service logs
4. Ensure PORT variable is correctly used

### Issue 3: API Calls Fail
**Symptoms**: Health check passes but API calls fail
**Solutions**:
1. Check environment variables are set correctly
2. Verify Chroma Cloud connectivity
3. Check Google Gemini API key validity
4. Review service logs for errors

### Issue 4: CORS Errors
**Symptoms**: Frontend can't connect to backend
**Solutions**:
1. Update CORS origins in main.py
2. Add your Vercel URL to allowed origins
3. Remove "*" from origins in production
4. Check if Railway URL is correctly added

### Issue 5: Service Not Starting
**Symptoms**: Service fails to start completely
**Solutions**:
1. Check start command in Railway settings
2. Verify Python version compatibility
3. Review build logs for dependency issues
4. Check if all required files are present

## Step 10: Railway CLI Commands

### Common Commands
```bash
# Login to Railway
railway login

# Create new project
railway new

# Deploy current code
railway up

# View logs
railway logs

# View service status
railway status

# Open service in browser
railway open

# Set environment variables
railway variables set CHROMA_API_KEY=your_key

# View environment variables
railway variables
```

### Service Management
```bash
# List all services
railway services

# Scale service
railway scale mutual-fund-api 1

# Restart service
railway restart mutual-fund-api
```

## Step 11: Production Considerations

### Security
- Remove `"*"` from CORS origins in production
- Use HTTPS (automatic on Railway)
- Keep API keys in environment variables
- Monitor API usage and costs

### Performance
- Monitor response times in Railway dashboard
- Consider upgrading to paid plan if needed
- Set up monitoring alerts
- Implement rate limiting if needed

### Monitoring
- Check Railway dashboard logs
- Monitor API response times
- Track error rates
- Set up alerts for downtime

### Scaling
- Free tier: 500 hours/month, 512MB RAM
- Upgrade plans available for higher usage
- Automatic scaling on paid plans
- Custom domains on paid plans

## Step 12: Save Your URLs

After successful deployment, save these URLs:

```bash
# Backend URLs
Backend URL: https://your-service-name.up.railway.app
Health Check: https://your-service-name.up.railway.app/health
API Documentation: https://your-service-name.up.railway.app/docs
API Endpoint: https://your-service-name.up.railway.app/api/chat/query
```

## Step 13: Next Steps

After backend deployment is complete:

1. **Deploy frontend on Vercel** (using Railway backend URL)
2. **Test end-to-end functionality**
3. **Set up GitHub Actions scheduler**
4. **Configure monitoring and alerts**
5. **Set up custom domains** (optional)

---

## Quick Reference Commands

```bash
# Test health check
curl https://your-service-name.up.railway.app/health

# Test API endpoint
curl -X POST https://your-service-name.up.railway.app/api/chat/query \
-H "Content-Type: application/json" \
-d '{"thread_id": "test", "query": "What is expense ratio?"}'

# Deploy using CLI
railway up

# View logs
railway logs

# Open in browser
railway open
```

---

## Railway vs Render Comparison

| Feature | Railway | Render |
|---------|---------|--------|
| Free Tier | 500 hours/month | 750 hours/month |
| URL Format | *.up.railway.app | *.onrender.com |
| CLI Support | Excellent | Basic |
| Auto-Deploy | Yes | Yes |
| Custom Domains | Paid plans | Free tier |
| Database | Built-in | Separate service |

---

*Last Updated: April 19, 2026*
*Version: 1.0*
