import httpx
import asyncio
from typing import Dict, Any, List, Optional
import os
from datetime import datetime, timedelta
import json
from ratelimit import limits, sleep_and_retry
import time

class DataFetcher:
    def __init__(self):
        self.fmp_api_key = os.getenv("FMP_API_KEY")
        self.serp_api_key = os.getenv("SERP_API_KEY")
        self.fmp_base_url = "https://financialmodelingprep.com/api/v3"
        self.serp_base_url = "https://serpapi.com/search"
        self.rate_limit = int(os.getenv("FMP_RATE_LIMIT_PER_MINUTE", 15))
        self.last_fmp_call = 0
        
    async def _rate_limited_request(self, url: str, params: Dict = None) -> Dict:
        """Make rate-limited HTTP request"""
        # Simple rate limiting - wait if needed
        current_time = time.time()
        time_since_last = current_time - self.last_fmp_call
        min_interval = 60 / self.rate_limit  # seconds between calls
        
        if time_since_last < min_interval:
            await asyncio.sleep(min_interval - time_since_last)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            self.last_fmp_call = time.time()
            return response.json()

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
