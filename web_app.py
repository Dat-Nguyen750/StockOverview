from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_session import Session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
import json
import os
from datetime import datetime
import secrets
import logging
from functools import wraps
import hashlib
import time

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/web_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Configuration
API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8000')

# Abuse prevention settings
MAX_REQUESTS_PER_IP_PER_HOUR = 20
MAX_REQUESTS_PER_IP_PER_DAY = 100
SUSPICIOUS_PATTERNS = [
    'admin', 'test', 'debug', 'eval', 'exec', 'script',
    'union', 'select', 'insert', 'delete', 'drop', 'create'
]

# Store for tracking suspicious activity
suspicious_ips = {}
failed_attempts = {}

def log_security_event(event_type, details, ip_address=None):
    """Log security events for monitoring"""
    if not ip_address:
        ip_address = get_remote_address()
    
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'ip_address': ip_address,
        'user_agent': request.headers.get('User-Agent', 'Unknown'),
        'details': details
    }
    
    logger.warning(f"SECURITY_EVENT: {json.dumps(log_entry)}")
    
    # Store suspicious IPs
    if event_type in ['rate_limit_exceeded', 'suspicious_input', 'api_key_abuse']:
        if ip_address not in suspicious_ips:
            suspicious_ips[ip_address] = {'count': 0, 'first_seen': time.time()}
        suspicious_ips[ip_address]['count'] += 1

def validate_input_safety(text):
    """Validate input for suspicious patterns"""
    if not text:
        return True
    
    text_lower = text.lower()
    for pattern in SUSPICIOUS_PATTERNS:
        if pattern in text_lower:
            return False
    return True

def check_api_key_abuse(api_keys):
    """Check for potential API key abuse patterns"""
    # Check for obvious fake keys
    fake_patterns = ['test', 'demo', 'fake', '123', 'abc', 'key']
    for key_type, key_value in api_keys.items():
        if key_value and len(key_value) < 10:
            return True
        if key_value and any(pattern in key_value.lower() for pattern in fake_patterns):
            return True
    return False

def monitor_api_usage(func):
    """Decorator to monitor API usage and detect abuse"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        ip_address = get_remote_address()
        
        # Log request
        logger.info(f"API_REQUEST: {ip_address} - {request.method} {request.path}")
        
        try:
            result = func(*args, **kwargs)
            
            # Log successful request
            duration = time.time() - start_time
            logger.info(f"API_SUCCESS: {ip_address} - {duration:.2f}s")
            
            return result
            
        except Exception as e:
            # Log failed request
            duration = time.time() - start_time
            logger.error(f"API_ERROR: {ip_address} - {duration:.2f}s - {str(e)}")
            
            # Track failed attempts
            if ip_address not in failed_attempts:
                failed_attempts[ip_address] = {'count': 0, 'last_attempt': time.time()}
            failed_attempts[ip_address]['count'] += 1
            failed_attempts[ip_address]['last_attempt'] = time.time()
            
            raise
    
    return wrapper

@app.route('/')
def index():
    """Main landing page"""
    logger.info(f"PAGE_VIEW: {get_remote_address()} - Home page")
    return render_template('index.html')

@app.route('/evaluate', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
@monitor_api_usage
def evaluate():
    """Stock evaluation page with rate limiting"""
    if request.method == 'POST':
        # Get form data
        ticker = request.form.get('ticker', '').upper().strip()
        fmp_key = request.form.get('fmp_key', '').strip()
        serp_key = request.form.get('serp_key', '').strip()
        gemini_key = request.form.get('gemini_key', '').strip()
        
        ip_address = get_remote_address()
        
        # Input validation and security checks
        if not validate_input_safety(ticker):
            log_security_event('suspicious_input', f'Invalid ticker: {ticker}', ip_address)
            flash('Invalid ticker symbol provided', 'error')
            return render_template('evaluate.html')
        
        # Check API keys for abuse patterns
        api_keys = {'fmp': fmp_key, 'serp': serp_key, 'gemini': gemini_key}
        if check_api_key_abuse(api_keys):
            log_security_event('api_key_abuse', 'Suspicious API keys detected', ip_address)
            flash('Please provide valid API keys', 'error')
            return render_template('evaluate.html')
        
        # Validate inputs
        if not ticker:
            flash('Please enter a stock ticker symbol', 'error')
            return render_template('evaluate.html')
        
        if not all([fmp_key, serp_key, gemini_key]):
            flash('Please provide all required API keys', 'error')
            return render_template('evaluate.html')
        
        # Store API keys in session for this evaluation
        session['api_keys'] = {
            'fmp_key': fmp_key,
            'serp_key': serp_key,
            'gemini_key': gemini_key
        }
        
        try:
            # Call the API with user's keys
            response = requests.post(
                f"{API_BASE_URL}/evaluate",
                json={
                    "ticker": ticker,
                    "include_detailed_analysis": True
                },
                headers={
                    'X-FMP-API-Key': fmp_key,
                    'X-SERP-API-Key': serp_key,
                    'X-GEMINI-API-Key': gemini_key
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Log successful evaluation
                logger.info(f"EVALUATION_SUCCESS: {ip_address} - {ticker} - Score: {result.get('composite_score', 'N/A')}")
                
                return render_template('result.html', result=result, ticker=ticker)
            else:
                error_msg = f"API Error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', error_msg)
                except:
                    pass
                
                # Log API errors
                logger.error(f"API_ERROR: {ip_address} - {ticker} - {error_msg}")
                
                flash(error_msg, 'error')
                return render_template('evaluate.html')
                
        except requests.exceptions.RequestException as e:
            logger.error(f"CONNECTION_ERROR: {ip_address} - {ticker} - {str(e)}")
            flash(f'Connection error: {str(e)}', 'error')
            return render_template('evaluate.html')
    
    return render_template('evaluate.html')

@app.route('/api/evaluate', methods=['POST'])
@limiter.limit("5 per minute")
@monitor_api_usage
def api_evaluate():
    """API endpoint for programmatic access with stricter rate limiting"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        ticker = data.get('ticker', '').upper().strip()
        fmp_key = data.get('fmp_api_key', '').strip()
        serp_key = data.get('serp_api_key', '').strip()
        gemini_key = data.get('gemini_api_key', '').strip()
        
        ip_address = get_remote_address()
        
        # Security checks
        if not validate_input_safety(ticker):
            log_security_event('suspicious_input', f'API Invalid ticker: {ticker}', ip_address)
            return jsonify({'error': 'Invalid ticker symbol'}), 400
        
        api_keys = {'fmp': fmp_key, 'serp': serp_key, 'gemini': gemini_key}
        if check_api_key_abuse(api_keys):
            log_security_event('api_key_abuse', 'API Suspicious keys detected', ip_address)
            return jsonify({'error': 'Invalid API keys'}), 400
        
        if not ticker:
            return jsonify({'error': 'Ticker symbol is required'}), 400
        
        if not all([fmp_key, serp_key, gemini_key]):
            return jsonify({'error': 'All API keys are required'}), 400
        
        # Call the API
        response = requests.post(
            f"{API_BASE_URL}/evaluate",
            json={
                "ticker": ticker,
                "include_detailed_analysis": data.get('include_detailed_analysis', False)
            },
            headers={
                'X-FMP-API-Key': fmp_key,
                'X-SERP-API-Key': serp_key,
                'X-GEMINI-API-Key': gemini_key
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"API_EVALUATION_SUCCESS: {ip_address} - {ticker}")
            return jsonify(result)
        else:
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else {'detail': 'API Error'}
            logger.error(f"API_EVALUATION_ERROR: {ip_address} - {ticker} - {response.status_code}")
            return jsonify(error_data), response.status_code
            
    except Exception as e:
        logger.error(f"API_EXCEPTION: {get_remote_address()} - {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/docs')
def docs():
    """API documentation page"""
    logger.info(f"PAGE_VIEW: {get_remote_address()} - Documentation")
    return render_template('docs.html')

@app.route('/about')
def about():
    """About page"""
    logger.info(f"PAGE_VIEW: {get_remote_address()} - About")
    return render_template('about.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            return jsonify({'status': 'healthy', 'api': 'connected'})
        else:
            return jsonify({'status': 'degraded', 'api': 'error'}), 503
    except:
        return jsonify({'status': 'unhealthy', 'api': 'disconnected'}), 503

@app.route('/admin/security')
def security_dashboard():
    """Security monitoring dashboard (basic version)"""
    # In production, this should be protected with authentication
    return jsonify({
        'suspicious_ips': suspicious_ips,
        'failed_attempts': failed_attempts,
        'total_suspicious_events': len(suspicious_ips),
        'total_failed_attempts': sum(data['count'] for data in failed_attempts.values())
    })

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded"""
    ip_address = get_remote_address()
    log_security_event('rate_limit_exceeded', f'Rate limit exceeded for {ip_address}', ip_address)
    return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    logger.warning(f"404_ERROR: {get_remote_address()} - {request.path}")
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    logger.error(f"500_ERROR: {get_remote_address()} - {str(e)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Railway compatibility - use PORT environment variable
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    # Create logs directory if it doesn't exist
    import pathlib
    pathlib.Path('logs').mkdir(exist_ok=True)
    pathlib.Path('flask_session').mkdir(exist_ok=True)
    
    logger.info(f"Starting Stock Evaluator Pro on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug) 