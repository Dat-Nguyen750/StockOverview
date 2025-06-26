# Stock Evaluator Pro - AI-Powered Investment Analysis

A comprehensive AI-powered web application for evaluating publicly traded companies for long-term investment potential. This application is designed for production deployment with enterprise-grade features and can be easily deployed to Railway.

## 🚀 Features

- **Multi-source Data Integration**: Financial Modeling Prep, SERP API, Google Gemini
- **Comprehensive Scoring Framework**: 5 key categories with weighted scoring
- **AI-Powered Analysis**: Google Gemini for business fundamentals and sentiment analysis
- **Production-Ready Architecture**: Docker, Redis, Celery, Nginx
- **Enterprise Security**: SSL/TLS, rate limiting, security headers
- **Monitoring & Observability**: Prometheus metrics, Sentry integration, structured logging
- **High Availability**: Load balancing, health checks, auto-restart
- **RESTful API**: FastAPI-based with automatic documentation
- **Beautiful Web Interface**: Modern, responsive design with Bootstrap 5

## 📋 Prerequisites

- GitHub account
- Railway account (free tier available)
- API Keys for:
  - Financial Modeling Prep (FMP)
  - SERP API
  - Google Gemini
- 4GB+ RAM, 2+ CPU cores (for local development)

## 🚀 Quick Deploy to Railway

### 1. **Fork/Clone the Repository**
```bash
# Clone this repository
git clone https://github.com/yourusername/stock-evaluator-pro.git
cd stock-evaluator-pro

# Or fork on GitHub and clone your fork
```

### 2. **Deploy to Railway**
1. Go to [Railway.app](https://railway.app)
2. Sign up/Login with your GitHub account
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway will automatically detect the Python app and deploy it

### 3. **Configure Environment Variables**
In your Railway project dashboard, add these environment variables:

```bash
# Required for Railway
PORT=8000

# Security
SECRET_KEY=your-super-secret-key-here

# API Configuration (optional - users provide their own)
API_BASE_URL=https://your-railway-app.railway.app

# Environment
FLASK_ENV=production
```

### 4. **Access Your Application**
Railway will provide you with a URL like: `https://your-app-name.railway.app`

## 🛠️ Local Development

### 1. **Clone and Setup**
```bash
git clone https://github.com/yourusername/stock-evaluator-pro.git
cd stock-evaluator-pro
```

### 2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 3. **Run Development Server**
```bash
# Start the API backend
python main.py

# In another terminal, start the web app
python web_app.py
```

Visit `http://localhost:5000` to use the web interface!

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Interface │    │   API Backend   │    │   External APIs │
│   (Flask)       │    │   (FastAPI)     │    │   (FMP, SERP)   │
│   Port 5000     │    │   Port 8000     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Rate Limiting │    │   AI Analysis   │    │   Data Sources  │
│   Security      │    │   Scoring       │    │   Monitoring    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📊 API Endpoints

### Core Endpoints
- `GET /` - Main landing page
- `GET /evaluate` - Stock evaluation form
- `POST /evaluate` - Submit evaluation
- `GET /api/evaluate` - API endpoint for programmatic access
- `GET /health` - Health check
- `GET /docs` - API documentation
- `GET /about` - About page

### Documentation
- `GET /docs` - Interactive API docs
- `GET /admin/security` - Security monitoring dashboard

## 🔒 Security Features

- **SSL/TLS Encryption**: All traffic encrypted (Railway provides this)
- **Rate Limiting**: 10 req/s per IP, burst up to 20
- **Security Headers**: HSTS, XSS protection, frame options
- **Input Validation**: Comprehensive input sanitization
- **API Key Protection**: No persistent storage of user keys
- **Abuse Prevention**: Suspicious activity detection and blocking

## 📈 Monitoring & Observability

### Health Checks
```bash
# Check application health
curl https://your-app.railway.app/health

# Check security dashboard
curl https://your-app.railway.app/admin/security
```

### Logs
Railway provides built-in log viewing in the dashboard:
- Application logs
- Build logs
- Deployment logs

### Local Monitoring
```bash
# Run monitoring script
python monitor.py

# Continuous monitoring
python monitor.py --continuous
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PORT` | Yes | 5000 | Port for the application |
| `SECRET_KEY` | Yes | - | Application secret key |
| `API_BASE_URL` | No | localhost:8000 | Backend API URL |
| `FLASK_ENV` | No | development | Environment mode |

### Railway-Specific Settings
- **Build Command**: Automatically detected from requirements.txt
- **Start Command**: `python web_app.py`
- **Health Check**: `/health` endpoint
- **Auto-deploy**: Enabled on GitHub push

## 🚨 Security & Monitoring

### What Gets Monitored
- **Security Events**: Rate limit violations, suspicious input, API key abuse
- **Application Health**: Service availability, response times
- **Usage Analytics**: Request patterns, popular tickers
- **Error Tracking**: API failures, connection issues

### Rate Limiting
- **Web Interface**: 10 requests per minute per IP
- **API Endpoint**: 5 requests per minute per IP
- **Global Limits**: 200 requests per day per IP

### Abuse Prevention
- Input validation and sanitization
- Suspicious pattern detection
- Automatic IP tracking
- Real-time security event logging

## 📚 Development

### Code Quality
```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

### Testing
```bash
# Run tests
pytest

# Test API endpoints
python test_aapl.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the [Security Guide](SECURITY_GUIDE.md)
- Review the logs in Railway dashboard

## 🔄 Updates

To update your Railway deployment:
1. Push changes to your GitHub repository
2. Railway will automatically redeploy
3. Monitor the deployment in Railway dashboard

## 🎯 Railway Benefits

- **Automatic HTTPS**: SSL certificates provided
- **Global CDN**: Fast loading worldwide
- **Auto-scaling**: Handles traffic spikes
- **Zero-downtime deployments**: Seamless updates
- **Built-in monitoring**: Logs and metrics
- **Custom domains**: Use your own domain
- **Environment variables**: Secure configuration

## 🚀 Production Checklist

- [x] Repository created and pushed to GitHub
- [x] Railway project created and deployed
- [x] Environment variables configured
- [x] Health checks passing
- [x] SSL certificate active
- [x] Monitoring set up
- [x] Security features enabled
- [x] Documentation updated

Your Stock Evaluator Pro is now ready for production use on Railway! Users can visit your Railway URL, get their own API keys, and start analyzing stocks immediately. 