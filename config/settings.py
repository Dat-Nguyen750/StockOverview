import os
import secrets
from typing import Dict, List
from pathlib import Path

class Settings:
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # API Keys
    FMP_API_KEY: str = os.getenv("FMP_API_KEY", "")
    SERP_API_KEY: str = os.getenv("SERP_API_KEY", "")
    GOOGLE_GEMINI_API_KEY: str = os.getenv("GOOGLE_GEMINI_API_KEY", "")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ALLOWED_HOSTS: List[str] = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    WORKERS: int = int(os.getenv("WORKERS", 4))
    
    # Rate Limiting
    FMP_RATE_LIMIT_PER_MINUTE: int = int(os.getenv("FMP_RATE_LIMIT_PER_MINUTE", 5))  # Conservative for free tier
    FMP_RATE_LIMIT_PER_DAY: int = int(os.getenv("FMP_RATE_LIMIT_PER_DAY", 250))  # Daily limit for free tier
    FMP_RETRY_DELAY: int = int(os.getenv("FMP_RETRY_DELAY", 60))  # Seconds to wait after rate limit hit
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/app.log")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # Monitoring
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
    PROMETHEUS_ENABLED: bool = os.getenv("PROMETHEUS_ENABLED", "False").lower() == "true"
    
    # Scoring Weights (can be customized)
    DEFAULT_WEIGHTS: Dict[str, float] = {
        "financial_health": 0.35,
        "business_fundamentals": 0.20,
        "valuation": 0.20,
        "growth_potential": 0.15,
        "sentiment": 0.10
    }
    
    # Scoring Thresholds
    VERDICT_THRESHOLDS: Dict[str, float] = {
        "strong_buy": 80.0,
        "buy": 65.0,
        "hold": 50.0,
        "avoid": 0.0
    }
    
    # Cache Settings
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", 3600))  # 1 hour default
    
    # API Timeouts
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", 30))
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"
    
    def validate_required_keys(self) -> List[str]:
        """Validate that all required API keys are present"""
        missing_keys = []
        required_keys = {
            "FMP_API_KEY": self.FMP_API_KEY,
            "SERP_API_KEY": self.SERP_API_KEY,
            "GOOGLE_GEMINI_API_KEY": self.GOOGLE_GEMINI_API_KEY
        }
        
        for key_name, key_value in required_keys.items():
            if not key_value:
                missing_keys.append(key_name)
        
        return missing_keys

settings = Settings()
