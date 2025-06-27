import httpx
import asyncio
from typing import Dict, Any, List, Optional
import os
from datetime import datetime, timedelta
import json
from ratelimit import limits, sleep_and_retry
import time
import logging

logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self):
        self.fmp_api_key = os.getenv("FMP_API_KEY")
        self.serp_api_key = os.getenv("SERP_API_KEY")
        self.fmp_base_url = "https://financialmodelingprep.com/api/v3"
        self.serp_base_url = "https://serpapi.com/search"
        self.rate_limit_per_minute = int(os.getenv("FMP_RATE_LIMIT_PER_MINUTE", 5))
        self.rate_limit_per_day = int(os.getenv("FMP_RATE_LIMIT_PER_DAY", 250))
        self.retry_delay = int(os.getenv("FMP_RETRY_DELAY", 60))
        self.last_fmp_call = 0
        self.daily_request_count = 0
        self.last_reset_date = datetime.now().date()
        
    def _reset_daily_counter_if_needed(self):
        """Reset daily counter if it's a new day"""
        current_date = datetime.now().date()
        if current_date != self.last_reset_date:
            self.daily_request_count = 0
            self.last_reset_date = current_date
    
    async def _rate_limited_request(self, url: str, params: Dict = None, max_retries: int = 3) -> Dict:
        """Make rate-limited HTTP request with retry logic"""
        self._reset_daily_counter_if_needed()
        
        # Check daily limit
        if self.daily_request_count >= self.rate_limit_per_day:
            raise Exception(f"Daily rate limit exceeded ({self.rate_limit_per_day} requests/day)")
        
        # Simple rate limiting - wait if needed
        current_time = time.time()
        time_since_last = current_time - self.last_fmp_call
        min_interval = 60 / self.rate_limit_per_minute  # seconds between calls
        
        if time_since_last < min_interval:
            wait_time = min_interval - time_since_last
            logger.info(f"Rate limiting: waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url, params=params)
                    
                    if response.status_code == 429:
                        # Rate limit hit
                        logger.warning(f"Rate limit hit (429) on attempt {attempt + 1}/{max_retries}")
                        if attempt < max_retries - 1:
                            wait_time = self.retry_delay * (attempt + 1)  # Exponential backoff
                            logger.info(f"Waiting {wait_time} seconds before retry")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise Exception("Rate limit exceeded after all retries")
                    
                    response.raise_for_status()
                    self.last_fmp_call = time.time()
                    self.daily_request_count += 1
                    return response.json()
                    
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt < max_retries - 1:
                    wait_time = self.retry_delay * (attempt + 1)
                    logger.warning(f"HTTP 429 error, waiting {wait_time} seconds before retry")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)  # Short delay for other errors
                    logger.warning(f"Request error: {e}, waiting {wait_time} seconds before retry")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status"""
        self._reset_daily_counter_if_needed()
        return {
            "daily_requests_used": self.daily_request_count,
            "daily_requests_remaining": self.rate_limit_per_day - self.daily_request_count,
            "daily_limit": self.rate_limit_per_day,
            "minute_limit": self.rate_limit_per_minute,
            "last_request_time": self.last_fmp_call,
            "time_since_last_request": time.time() - self.last_fmp_call if self.last_fmp_call > 0 else None
        }

    async def get_company_profile(self, ticker: str) -> Dict[str, Any]:
        """Get basic company information"""
        url = f"{self.fmp_base_url}/profile/{ticker}"
        params = {"apikey": self.fmp_api_key}
        
        data = await self._rate_limited_request(url, params)
        if data and isinstance(data, list) and len(data) > 0:
            profile = data[0]
            # If market cap or companyName is missing, mark as fallback
            if not profile.get('mktCap') or not profile.get('companyName'):
                profile['profile_freshness'] = 'fallback'
            else:
                profile['profile_freshness'] = 'fresh'
            return profile
        else:
            # Return a fallback profile
            return {'profile_freshness': 'fallback'}

    async def get_financial_statements(self, ticker: str, years: int = 5) -> Dict[str, List]:
        """Get income statement, balance sheet, and cash flow data"""
        statements = {}
        
        # Income Statement
        url = f"{self.fmp_base_url}/income-statement/{ticker}"
        params = {"limit": years, "apikey": self.fmp_api_key}
        statements["income"] = await self._rate_limited_request(url, params)
        
        # Balance Sheet
        url = f"{self.fmp_base_url}/balance-sheet-statement/{ticker}"
        statements["balance"] = await self._rate_limited_request(url, params)
        
        # Cash Flow Statement
        url = f"{self.fmp_base_url}/cash-flow-statement/{ticker}"
        statements["cashflow"] = await self._rate_limited_request(url, params)
        
        return statements

    async def get_key_metrics(self, ticker: str, years: int = 5) -> List[Dict]:
        """Get key financial metrics"""
        url = f"{self.fmp_base_url}/key-metrics/{ticker}"
        params = {"limit": years, "apikey": self.fmp_api_key}
        
        data = await self._rate_limited_request(url, params)
        if data and isinstance(data, list) and len(data) > 0:
            metrics = data
            # If marketCap or revenuePerShare is missing, mark as fallback
            if not metrics[0].get('marketCap') or not metrics[0].get('revenuePerShare'):
                metrics[0]['metrics_freshness'] = 'fallback'
            else:
                metrics[0]['metrics_freshness'] = 'fresh'
            return metrics
        else:
            # Return a fallback metrics dict
            return [{ 'metrics_freshness': 'fallback' }]

    async def get_financial_ratios(self, ticker: str, years: int = 5) -> List[Dict]:
        """Get financial ratios"""
        url = f"{self.fmp_base_url}/ratios/{ticker}"
        params = {"limit": years, "apikey": self.fmp_api_key}
        
        return await self._rate_limited_request(url, params)

    async def get_insider_trading(self, ticker: str) -> List[Dict]:
        """Get insider trading data"""
        url = f"{self.fmp_base_url}/insider-trading"
        params = {"symbol": ticker, "limit": 50, "apikey": self.fmp_api_key}
        
        return await self._rate_limited_request(url, params)

    async def get_industry_pe(self, industry: str) -> float:
        """Get industry average P/E ratio"""
        # This would typically require industry classification and averaging
        # For now, return a default industry PE
        return 20.0  # Default industry PE

    async def search_company_news(self, company_name: str, ticker: str) -> List[Dict]:
        """Search for recent company news using SERP API"""
        if not self.serp_api_key:
            return []
        
        query = f"{company_name} {ticker} stock news"
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.serp_api_key,
            "num": 10,
            "tbm": "nws"  # News search
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.serp_base_url, params=params)
                response.raise_for_status()
                data = response.json()
                return data.get("news_results", [])
        except Exception as e:
            print(f"Error fetching news: {e}")
            return []

    async def search_company_info(self, company_name: str, query_type: str) -> List[Dict]:
        """Search for specific company information"""
        if not self.serp_api_key:
            return []
        
        query_map = {
            "management": f"{company_name} CEO management team leadership",
            "competitors": f"{company_name} competitors industry analysis",
            "litigation": f"{company_name} lawsuit legal issues",
            "esg": f"{company_name} ESG sustainability environmental"
        }
        
        query = query_map.get(query_type, f"{company_name} {query_type}")
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.serp_api_key,
            "num": 5
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.serp_base_url, params=params)
                response.raise_for_status()
                data = response.json()
                return data.get("organic_results", [])
        except Exception as e:
            print(f"Error fetching {query_type} info: {e}")
            return []
