# Railway Deployment Guide - Stock Evaluator Pro

## 🚀 Quick Start: Deploy to Railway in 5 Minutes

### Step 1: Prepare Your Repository

1. **Create a new GitHub repository**
   ```bash
   # Create a new directory
   mkdir stock-evaluator-pro
   cd stock-evaluator-pro
   
   # Initialize git
   git init
   git add .
   git commit -m "Initial commit: Stock Evaluator Pro"
   ```

2. **Push to GitHub**
   ```bash
   # Add your GitHub repository as remote
   git remote add origin https://github.com/yourusername/stock-evaluator-pro.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy to Railway

1. **Go to Railway.app**
   - Visit [railway.app](https://railway.app)
   - Sign up/Login with your GitHub account

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `stock-evaluator-pro` repository

3. **Configure Environment Variables**
   In your Railway project dashboard, add these variables:
   ```bash
   PORT=8000
   SECRET_KEY=your-super-secret-key-here-change-this
   FLASK_ENV=production
   ```

4. **Deploy**
   - Railway will automatically detect it's a Python app
   - It will install dependencies from `requirements.txt`
   - Start the app using `python web_app.py`

### Step 3: Access Your Application

- Railway will provide a URL like: `https://your-app-name.railway.app`
- Your app is now live and accessible worldwide!

## 📁 Repository Structure

Your GitHub repository should look like this:

```
stock-evaluator-pro/
├── .github/
│   └── workflows/
│       └── test.yml
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── evaluate.html
│   ├── result.html
│   ├── docs.html
│   ├── about.html
│   └── 404.html
├── modules/
│   ├── __init__.py
│   ├── data_fetcher.py
│   ├── evaluator.py
│   ├── llm_orchestrator.py
│   ├── models.py
│   └── scoring.py
├── config/
│   └── settings.py
├── .gitignore
├── .dockerignore
├── Dockerfile
├── Dockerfile.railway
├── Procfile
├── railway.json
├── runtime.txt
├── requirements.txt
├── main.py
├── web_app.py
├── monitor.py
├── README.md
├── SECURITY_GUIDE.md
├── DEPLOYMENT_GUIDE.md
└── test_aapl.py
```

## 🔧 Railway Configuration Files

### `railway.json`
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "python web_app.py",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 300,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### `Procfile`
```
web: python web_app.py
```

### `runtime.txt`
```
python-3.11.7
```

## 🌍 Environment Variables

### Required Variables
| Variable | Description | Example |
|----------|-------------|---------|
| `PORT` | Port for the application | `8000` |
| `SECRET_KEY` | Flask secret key | `your-super-secret-key` |

### Optional Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Environment mode | `development` |
| `API_BASE_URL` | Backend API URL | `localhost:8000` |

## 🔄 Continuous Deployment

### GitHub Actions Setup

1. **Add Railway Token to GitHub Secrets**
   - Go to your Railway project settings
   - Copy your Railway token
   - Go to your GitHub repository settings
   - Add secret: `RAILWAY_TOKEN`
   - Add secret: `RAILWAY_SERVICE` (your service name)

2. **Automatic Deployment**
   - Every push to `main` branch triggers deployment
   - Railway automatically redeploys your app
   - Zero-downtime deployments

## 📊 Monitoring Your Deployment

### Railway Dashboard
- **Logs**: Real-time application logs
- **Metrics**: CPU, memory, network usage
- **Deployments**: Deployment history and status
- **Environment**: Environment variables management

### Health Checks
```bash
# Check if your app is running
curl https://your-app.railway.app/health

# Expected response:
{
  "status": "healthy",
  "api": "connected"
}
```

### Custom Domain (Optional)
1. Go to your Railway project settings
2. Click "Custom Domains"
3. Add your domain (e.g., `stock-evaluator.yourdomain.com`)
4. Update DNS records as instructed

## 🚨 Troubleshooting

### Common Issues

#### 1. **Build Fails**
```bash
# Check build logs in Railway dashboard
# Common causes:
# - Missing requirements.txt
# - Python version mismatch
# - Missing dependencies
```

#### 2. **App Won't Start**
```bash
# Check start command in railway.json
# Ensure web_app.py exists
# Verify PORT environment variable
```

#### 3. **Health Check Fails**
```bash
# Ensure /health endpoint exists
# Check if app is listening on correct port
# Verify environment variables
```

#### 4. **Environment Variables Not Set**
```bash
# Go to Railway dashboard
# Navigate to Variables tab
# Add missing environment variables
```

### Debug Commands

```bash
# Check Railway logs
railway logs

# Check Railway status
railway status

# Redeploy manually
railway up
```

## 🔒 Security Considerations

### Environment Variables
- Never commit sensitive data to Git
- Use Railway's environment variable system
- Rotate secrets regularly

### SSL/TLS
- Railway provides automatic HTTPS
- No additional SSL configuration needed

### Rate Limiting
- Built-in rate limiting in the application
- Monitor usage in Railway dashboard

## 📈 Scaling

### Railway Free Tier
- 500 hours/month
- 512MB RAM
- Shared CPU
- Perfect for development and small production

### Railway Pro ($5/month)
- Unlimited hours
- 1GB RAM
- Dedicated CPU
- Custom domains
- Better for production use

### Auto-scaling
- Railway automatically handles traffic spikes
- No manual scaling configuration needed

## 🔄 Updates and Maintenance

### Updating Your App
```bash
# Make changes to your code
git add .
git commit -m "Update feature"
git push origin main

# Railway automatically redeploys
```

### Monitoring Updates
1. Check Railway dashboard for deployment status
2. Monitor health checks
3. Review logs for any errors
4. Test the application

### Rollback (if needed)
1. Go to Railway dashboard
2. Navigate to Deployments
3. Click on previous deployment
4. Select "Redeploy"

## 🎯 Best Practices

### Code Organization
- Keep your code in a public GitHub repository
- Use meaningful commit messages
- Document your API endpoints
- Include comprehensive README

### Security
- Use strong SECRET_KEY
- Never expose API keys in code
- Implement proper input validation
- Monitor for suspicious activity

### Performance
- Optimize your Docker image
- Use efficient Python packages
- Implement caching where appropriate
- Monitor resource usage

### Monitoring
- Set up health checks
- Monitor application logs
- Track error rates
- Set up alerts for critical issues

## 🚀 Production Checklist

- [ ] Repository created and pushed to GitHub
- [ ] Railway project created
- [ ] Environment variables configured
- [ ] Health checks passing
- [ ] SSL certificate active (automatic)
- [ ] Custom domain configured (optional)
- [ ] Monitoring set up
- [ ] Documentation updated
- [ ] Security measures implemented
- [ ] Backup strategy in place

## 🆘 Support

### Railway Support
- [Railway Documentation](https://docs.railway.app/)
- [Railway Discord](https://discord.gg/railway)
- [Railway Status](https://status.railway.app/)

### Application Support
- Check the [Security Guide](SECURITY_GUIDE.md)
- Review application logs in Railway dashboard
- Create issues on GitHub for bugs

Your Stock Evaluator Pro is now ready for production deployment on Railway! 🎉

## Quick Fix for 502 API Errors

If you're getting 502 errors with messages like "API Error: 502" or "Cannot connect to backend API at http://localhost:8000", this means your frontend is trying to connect to localhost instead of your deployed backend.

### Solution

1. **Set the `API_BASE_URL` environment variable** on your deployment platform to point to your actual backend URL.

   **For Railway:**
   - Go to your Railway dashboard
   - Select your frontend service
   - Go to Variables tab
   - Add: `API_BASE_URL=https://your-backend-app-name.railway.app`
   
   **For Heroku:**
   ```bash
   heroku config:set API_BASE_URL=https://your-backend-app-name.herokuapp.com
   ```
   
   **For other platforms:**
   - Set the environment variable `API_BASE_URL` to your backend's public URL

2. **Redeploy your frontend** after setting the environment variable.

3. **Verify both services are running:**
   - Backend should be accessible at your backend URL
   - Frontend should be accessible at your frontend URL

### Example Configuration

If your backend is deployed at `https://stock-evaluator-api.railway.app` and your frontend at `https://stock-evaluator-web.railway.app`, set:

```
API_BASE_URL=https://stock-evaluator-api.railway.app
```

## Full Deployment Instructions

### Prerequisites
- Python 3.8+
- Docker (optional)
- API keys for:
  - Financial Modeling Prep (FMP)
  - SerpAPI
  - Google Gemini

### Environment Variables

Set these environment variables on your deployment platform:

#### Required
- `FMP_API_KEY` - Your Financial Modeling Prep API key
- `SERP_API_KEY` - Your SerpAPI key  
- `GOOGLE_GEMINI_API_KEY` - Your Google Gemini API key
- `API_BASE_URL` - URL of your deployed backend (e.g., `https://your-backend.railway.app`)

#### Optional
- `SECRET_KEY` - Secret key for Flask sessions (auto-generated if not set)
- `ENVIRONMENT` - Set to `production` for production deployments
- `DEBUG` - Set to `False` for production
- `LOG_LEVEL` - Logging level (INFO, DEBUG, WARNING, ERROR)

### Deployment Options

#### Option 1: Railway (Recommended)

1. **Deploy Backend:**
   ```bash
   # Connect your backend repository
   railway login
   railway link
   railway up
   ```

2. **Deploy Frontend:**
   ```bash
   # Connect your frontend repository  
   railway login
   railway link
   railway up
   ```

3. **Set Environment Variables:**
   - Backend: Set `FMP_API_KEY`, `SERP_API_KEY`, `GOOGLE_GEMINI_API_KEY`
   - Frontend: Set `API_BASE_URL` to your backend URL

#### Option 2: Heroku

1. **Deploy Backend:**
   ```bash
   heroku create your-backend-app
   git push heroku main
   heroku config:set FMP_API_KEY=your_key
   heroku config:set SERP_API_KEY=your_key
   heroku config:set GOOGLE_GEMINI_API_KEY=your_key
   ```

2. **Deploy Frontend:**
   ```bash
   heroku create your-frontend-app
   git push heroku main
   heroku config:set API_BASE_URL=https://your-backend-app.herokuapp.com
   ```

#### Option 3: Docker Compose

1. **Create `.env` file:**
   ```env
   FMP_API_KEY=your_key
   SERP_API_KEY=your_key
   GOOGLE_GEMINI_API_KEY=your_key
   SECRET_KEY=your_secret_key
   API_BASE_URL=http://localhost:8000
   ```

2. **Deploy:**
   ```bash
   docker-compose -f docker-compose.web.yml up -d
   ```

### Health Checks

After deployment, verify both services are running:

- **Backend Health:** `https://your-backend-url/health`
- **Frontend Health:** `https://your-frontend-url/health`

### Troubleshooting

#### Common Issues

1. **502 Bad Gateway:**
   - Check if backend is running
   - Verify `API_BASE_URL` is correct
   - Check backend logs for errors

2. **API Key Errors:**
   - Verify all API keys are set correctly
   - Check API key quotas and limits

3. **Connection Timeouts:**
   - Increase timeout settings
   - Check network connectivity
   - Verify service URLs are accessible

#### Logs

Check logs for detailed error information:

- **Backend logs:** Available in your deployment platform's log viewer
- **Frontend logs:** Check browser console and server logs

### Security Considerations

1. **Environment Variables:** Never commit API keys to version control
2. **Rate Limiting:** Configure appropriate rate limits for your use case
3. **CORS:** Configure CORS settings if needed
4. **HTTPS:** Always use HTTPS in production

### Monitoring

The application includes built-in monitoring:

- **Health endpoints:** `/health` for both frontend and backend
- **Security dashboard:** `/admin/security` (basic version)
- **Logging:** Comprehensive logging for debugging and monitoring

### Support

For additional help:
1. Check the logs for specific error messages
2. Verify all environment variables are set correctly
3. Test the backend API directly using curl or Postman
4. Check the health endpoints for service status 