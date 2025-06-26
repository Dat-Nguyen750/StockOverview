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