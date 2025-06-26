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
from contextlib import asynccontextmanager

# Import after environment setup
load_dotenv("keys.env")

from modules.evaluator import StockEvaluator
from modules.models import EvaluationResponse, EvaluationRequest
from config.settings import settings

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
async def evaluate_stock(ticker: str) -> EvaluationResponse:
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
        
        result = await app.state.evaluator.evaluate_company(ticker)
        
        try:
            response = EvaluationResponse(**result)
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
async def evaluate_stock_post(request: EvaluationRequest) -> EvaluationResponse:
    """
    POST endpoint for stock evaluation with additional parameters
    """
    try:
        logger.info(f"Evaluating stock via POST: {request.ticker}")
        
        result = await app.state.evaluator.evaluate_company(
            request.ticker,
            include_detailed_analysis=request.include_detailed_analysis,
            custom_weights=request.custom_weights
        )
        
        response = EvaluationResponse(**result)
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
