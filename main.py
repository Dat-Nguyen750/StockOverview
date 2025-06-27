# main.py
import logging
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import asyncio
from dotenv import load_dotenv
import os
import time
import json
import math
from contextlib import asynccontextmanager

# Import after environment setup
load_dotenv("keys.env")

from modules.evaluator import StockEvaluator
from modules.models import EvaluationResponse, EvaluationRequest
from config.settings import settings

def sanitize_for_json(obj):
    """
    Recursively sanitize an object to ensure it's JSON serializable.
    Replaces infinite values and NaN with safe alternatives.
    """
    if isinstance(obj, dict):
        return {key: sanitize_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None  # Replace NaN and inf with None
        return obj
    elif isinstance(obj, (int, str, bool, type(None))):
        return obj
    else:
        return str(obj)  # Convert any other types to string

# Setup logging
def setup_logging():
    """Configure logging for the application"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(settings.LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific loggers
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Stock Evaluation API...")
    
    # Validate required API keys
    missing_keys = settings.validate_required_keys()
    if missing_keys:
        logger.error(f"Missing required API keys: {missing_keys}")
        raise ValueError(f"Missing required API keys: {missing_keys}")
    
    # Initialize the stock evaluator
    try:
        app.state.evaluator = StockEvaluator()
        logger.info("Stock evaluator initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize stock evaluator: {e}")
        raise
    
    logger.info("Stock Evaluation API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Stock Evaluation API...")

# Create FastAPI app with lifespan
app = FastAPI(
    title="Stock Evaluation API",
    description="AI-powered stock evaluation for long-term investment decisions",
    version="1.0.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan
)

# Security middleware
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - {process_time:.3f}s")
    
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.get("/")
async def root():
    return {
        "message": "Stock Evaluation API is running",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint"""
    try:
        # Basic health check
        health_status = {
            "status": "healthy",
            "api_version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "timestamp": time.time()
        }
        
        # Check if evaluator is available
        if hasattr(app.state, 'evaluator'):
            health_status["evaluator"] = "available"
            
            # Add rate limit status if available
            try:
                rate_limit_status = app.state.evaluator.data_fetcher.get_rate_limit_status()
                health_status["rate_limits"] = {
                    "daily_requests_used": rate_limit_status["daily_requests_used"],
                    "daily_requests_remaining": rate_limit_status["daily_requests_remaining"],
                    "daily_limit": rate_limit_status["daily_limit"],
                    "minute_limit": rate_limit_status["minute_limit"]
                }
                
                # Check if we're approaching limits
                daily_usage_percent = (rate_limit_status["daily_requests_used"] / rate_limit_status["daily_limit"]) * 100
                if daily_usage_percent > 80:
                    health_status["status"] = "degraded"
                    health_status["warnings"] = ["Approaching daily API limit"]
                elif daily_usage_percent > 95:
                    health_status["status"] = "unhealthy"
                    health_status["warnings"] = ["Daily API limit nearly reached"]
                    
            except Exception as e:
                logger.warning(f"Could not get rate limit status: {e}")
                health_status["rate_limits"] = "unavailable"
        else:
            health_status["evaluator"] = "unavailable"
            health_status["status"] = "degraded"
        
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.get("/evaluate")
async def evaluate_stock(ticker: str, request_headers: Request) -> EvaluationResponse:
    """
    Evaluate a stock for long-term investment potential
    
    Args:
        ticker: Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)
    
    Returns:
        Comprehensive evaluation with scores and verdict
    """
    try:
        ticker = ticker.upper().strip()
        if not ticker:
            raise HTTPException(status_code=400, detail="Ticker symbol is required")
        
        logger.info(f"Evaluating stock: {ticker}")
        
        # Extract FMP API key from headers if provided
        fmp_api_key = request_headers.headers.get('X-FMP-API-Key')
        
        result = await app.state.evaluator.evaluate_company(ticker, fmp_api_key=fmp_api_key)
        
        # Sanitize the result to ensure JSON serialization
        sanitized_result = sanitize_for_json(result)
        
        try:
            response = EvaluationResponse(**sanitized_result)
            logger.info(f"Successfully evaluated {ticker}: {response.composite_score}/100")
            return response
        except Exception as validation_error:
            logger.error(f"Response validation error for {ticker}: {validation_error}")
            raise HTTPException(status_code=400, detail=f"Response validation error: {str(validation_error)}")
    
    except ValueError as e:
        logger.warning(f"Invalid request for ticker {ticker}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error evaluating {ticker}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/evaluate")
async def evaluate_stock_post(request: EvaluationRequest, request_headers: Request) -> EvaluationResponse:
    """
    POST endpoint for stock evaluation with additional parameters
    """
    try:
        logger.info(f"Evaluating stock via POST: {request.ticker}")
        
        # Extract FMP API key from headers if provided
        fmp_api_key = request_headers.headers.get('X-FMP-API-Key')
        
        result = await app.state.evaluator.evaluate_company(
            request.ticker,
            include_detailed_analysis=request.include_detailed_analysis,
            custom_weights=request.custom_weights,
            fmp_api_key=fmp_api_key
        )
        
        # Sanitize the result to ensure JSON serialization
        sanitized_result = sanitize_for_json(result)
        
        response = EvaluationResponse(**sanitized_result)
        logger.info(f"Successfully evaluated {request.ticker} via POST: {response.composite_score}/100")
        return response
    
    except ValueError as e:
        logger.warning(f"Invalid POST request for ticker {request.ticker}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error evaluating {request.ticker} via POST: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Metrics endpoint for monitoring
@app.get("/metrics")
async def metrics():
    """Basic metrics endpoint for monitoring"""
    return {
        "uptime": time.time(),
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }

@app.get("/rate-limits")
async def rate_limits(request_headers: Request):
    """Get current rate limit status"""
    try:
        if not hasattr(app.state, 'evaluator'):
            raise HTTPException(status_code=503, detail="Evaluator not available")
        
        # Extract FMP API key from headers if provided
        fmp_api_key = request_headers.headers.get('X-FMP-API-Key')
        
        rate_limit_status = app.state.evaluator.data_fetcher.get_rate_limit_status(api_key=fmp_api_key)
        return {
            "rate_limits": rate_limit_status,
            "timestamp": time.time(),
            "environment": settings.ENVIRONMENT
        }
    except Exception as e:
        logger.error(f"Error getting rate limit status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting rate limit status: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    # Validate environment before starting
    missing_keys = settings.validate_required_keys()
    if missing_keys:
        print(f"❌ Missing required API keys: {missing_keys}")
        print("Please set the required environment variables before starting the server.")
        sys.exit(1)
    
    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        app, 
        host=settings.HOST, 
        port=settings.PORT,
        workers=settings.WORKERS if settings.is_production else 1,
        log_level=settings.LOG_LEVEL.lower()
    )
