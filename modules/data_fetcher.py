import httpx
import asyncio
from typing import Dict, Any, List, Optional
import os
from datetime import datetime, timedelta
import json
from ratelimit import limits, sleep_and_retry
import time
import logging
import hashlib

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
        
        # Per-API-key rate limiting storage
        self.api_key_timers = {}  # {api_key_hash: last_call_time}
        self.api_key_daily_counts = {}  # {api_key_hash: daily_count}
        self.api_key_reset_dates = {}  # {api_key_hash: reset_date}
        
    def _get_api_key_hash(self, api_key: str) -> str:
        """Create a hash of the API key for storage"""
        return hashlib.md5(api_key.encode()).hexdigest()
    
    def _reset_daily_counter_if_needed(self, api_key: str):
        """Reset daily counter if it's a new day for specific API key"""
        api_key_hash = self._get_api_key_hash(api_key)
        current_date = datetime.now().date()
        
        if api_key_hash not in self.api_key_reset_dates or current_date != self.api_key_reset_dates[api_key_hash]:
            self.api_key_daily_counts[api_key_hash] = 0
            self.api_key_reset_dates[api_key_hash] = current_date
    
    async def _rate_limited_request(self, url: str, params: Dict = None, max_retries: int = 3, api_key: str = None) -> Dict:
        """Make rate-limited HTTP request with per-API-key rate limiting"""
        # Use provided API key or fallback to environment variable
        if api_key is None:
            api_key = self.fmp_api_key
            
        api_key_hash = self._get_api_key_hash(api_key)
        self._reset_daily_counter_if_needed(api_key)
        
        # Check daily limit for this specific API key
        daily_count = self.api_key_daily_counts.get(api_key_hash, 0)
        if daily_count >= self.rate_limit_per_day:
            raise Exception(f"Daily rate limit exceeded for API key ({self.rate_limit_per_day} requests/day)")
        
        # Per-API-key rate limiting - wait if needed
        current_time = time.time()
        last_call_time = self.api_key_timers.get(api_key_hash, 0)
        time_since_last = current_time - last_call_time
        min_interval = 60 / self.rate_limit_per_minute  # seconds between calls
        
        if time_since_last < min_interval:
            wait_time = min_interval - time_since_last
            logger.info(f"Rate limiting for API key {api_key_hash[:8]}...: waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url, params=params)
                    
                    # Log the response status for debugging
                    logger.info(f"API Response: {response.status_code} for {url.split('/')[-1]}")
                    
                    if response.status_code == 429:
                        # Rate limit hit
                        logger.warning(f"Rate limit hit (429) for API key {api_key_hash[:8]}... on attempt {attempt + 1}/{max_retries}")
                        if attempt < max_retries - 1:
                            wait_time = self.retry_delay * (attempt + 1)  # Exponential backoff
                            logger.info(f"Waiting {wait_time} seconds before retry")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise Exception("Rate limit exceeded after all retries")
                    
                    # Handle specific error codes
                    if response.status_code == 502:
                        logger.error(f"Bad Gateway (502) error from Financial Modeling Prep API on attempt {attempt + 1}/{max_retries}")
                        if attempt < max_retries - 1:
                            wait_time = 10 * (attempt + 1)  # Longer delay for 502 errors
                            logger.info(f"Waiting {wait_time} seconds before retry for 502 error")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise Exception("Financial Modeling Prep API is experiencing issues (502 Bad Gateway). Please try again later.")
                    
                    if response.status_code == 503:
                        logger.error(f"Service Unavailable (503) error from Financial Modeling Prep API on attempt {attempt + 1}/{max_retries}")
                        if attempt < max_retries - 1:
                            wait_time = 15 * (attempt + 1)  # Even longer delay for 503 errors
                            logger.info(f"Waiting {wait_time} seconds before retry for 503 error")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise Exception("Financial Modeling Prep API is temporarily unavailable (503 Service Unavailable). Please try again later.")
                    
                    response.raise_for_status()
                    self.api_key_timers[api_key_hash] = time.time()
                    self.api_key_daily_counts[api_key_hash] = daily_count + 1
                    return response.json()
                    
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP {e.response.status_code} error for {url}: {e}")
                if e.response.status_code == 429 and attempt < max_retries - 1:
                    wait_time = self.retry_delay * (attempt + 1)
                    logger.warning(f"HTTP 429 error for API key {api_key_hash[:8]}..., waiting {wait_time} seconds before retry")
                    await asyncio.sleep(wait_time)
                    continue
                elif e.response.status_code in [502, 503] and attempt < max_retries - 1:
                    wait_time = 10 * (attempt + 1)
                    logger.warning(f"HTTP {e.response.status_code} error, waiting {wait_time} seconds before retry")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Re-raise with more descriptive error message
                    if e.response.status_code == 401:
                        raise Exception("Invalid API key for Financial Modeling Prep. Please check your API key.")
                    elif e.response.status_code == 403:
                        raise Exception("API key does not have permission to access this endpoint.")
                    elif e.response.status_code == 404:
                        raise Exception("Data not found for this ticker symbol.")
                    elif e.response.status_code == 500:
                        raise Exception("Financial Modeling Prep API internal error. Please try again later.")
                    else:
                        raise Exception(f"Financial Modeling Prep API error ({e.response.status_code}): {e}")
            except httpx.ConnectError as e:
                logger.error(f"Connection error for {url}: {e}")
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)
                    logger.warning(f"Connection error, waiting {wait_time} seconds before retry")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"Unable to connect to Financial Modeling Prep API: {e}")
            except httpx.TimeoutException as e:
                logger.error(f"Timeout error for {url}: {e}")
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)
                    logger.warning(f"Timeout error, waiting {wait_time} seconds before retry")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"Request to Financial Modeling Prep API timed out: {e}")
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)  # Short delay for other errors
                    logger.warning(f"Request error for API key {api_key_hash[:8]}...: {e}, waiting {wait_time} seconds before retry")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise

    def get_rate_limit_status(self, api_key: str = None) -> Dict[str, Any]:
        """Get current rate limit status for specific API key"""
        if api_key is None:
            api_key = self.fmp_api_key
            
        api_key_hash = self._get_api_key_hash(api_key)
        self._reset_daily_counter_if_needed(api_key)
        
        daily_count = self.api_key_daily_counts.get(api_key_hash, 0)
        last_call_time = self.api_key_timers.get(api_key_hash, 0)
        
        return {
            "api_key_hash": api_key_hash[:8] + "...",  # Only show first 8 chars for privacy
            "daily_requests_used": daily_count,
            "daily_requests_remaining": self.rate_limit_per_day - daily_count,
            "daily_limit": self.rate_limit_per_day,
            "minute_limit": self.rate_limit_per_minute,
            "last_request_time": last_call_time,
            "time_since_last_request": time.time() - last_call_time if last_call_time > 0 else None
        }

    async def get_company_profile(self, ticker: str, api_key: str = None) -> Dict[str, Any]:
        """Get basic company information"""
        url = f"{self.fmp_base_url}/profile/{ticker}"
        params = {"apikey": api_key or self.fmp_api_key}
        
        data = await self._rate_limited_request(url, params, api_key=api_key)
        if data and isinstance(data, list) and len(data) > 0:
            profile = data[0]
            
            # Validate and fix market cap data
            profile = await self._validate_and_fix_market_cap(profile, ticker, api_key)
            
            # If market cap or companyName is missing, mark as fallback
            if not profile.get('mktCap') or not profile.get('companyName'):
                profile['profile_freshness'] = 'fallback'
            else:
                profile['profile_freshness'] = 'fresh'
            return profile
        else:
            # Return a fallback profile
            return {'profile_freshness': 'fallback'}

    async def _validate_and_fix_market_cap(self, profile: Dict[str, Any], ticker: str, api_key: str = None) -> Dict[str, Any]:
        """Validate and fix market cap data when shares outstanding is missing or zero"""
        try:
            # Check if shares outstanding is missing or zero
            shares_outstanding = profile.get('sharesOutstanding', 0)
            reported_mkt_cap = profile.get('mktCap', 0)
            price = profile.get('price', 0)
            
            # If shares outstanding is zero but we have price and market cap, calculate shares
            if shares_outstanding == 0 and price > 0 and reported_mkt_cap > 0:
                calculated_shares = reported_mkt_cap / price
                profile['sharesOutstanding'] = calculated_shares
                profile['shares_calculated'] = True
                logger.info(f"Calculated shares outstanding for {ticker}: {calculated_shares:,.0f}")
            
            # If we have price and shares but market cap seems wrong, recalculate
            elif shares_outstanding > 0 and price > 0:
                calculated_mkt_cap = price * shares_outstanding
                discrepancy = abs(reported_mkt_cap - calculated_mkt_cap)
                discrepancy_percent = (discrepancy / reported_mkt_cap) * 100 if reported_mkt_cap > 0 else 0
                
                # If discrepancy is more than 5%, use calculated value
                if discrepancy_percent > 5:
                    profile['mktCap'] = calculated_mkt_cap
                    profile['mkt_cap_calculated'] = True
                    logger.info(f"Recalculated market cap for {ticker}: ${calculated_mkt_cap:,.0f} (was ${reported_mkt_cap:,.0f})")
            
            # Try to get real-time quote data as fallback
            if shares_outstanding == 0 or price == 0:
                quote_data = await self._get_real_time_quote(ticker, api_key)
                if quote_data:
                    if shares_outstanding == 0 and quote_data.get('marketCap', 0) > 0 and quote_data.get('price', 0) > 0:
                        calculated_shares = quote_data['marketCap'] / quote_data['price']
                        profile['sharesOutstanding'] = calculated_shares
                        profile['shares_calculated'] = True
                        logger.info(f"Used quote data to calculate shares for {ticker}: {calculated_shares:,.0f}")
                    
                    if price == 0 and quote_data.get('price', 0) > 0:
                        profile['price'] = quote_data['price']
                        profile['price_from_quote'] = True
                        logger.info(f"Used quote data for price for {ticker}: ${quote_data['price']:.2f}")
            
            # Final validation - if we still don't have proper data, try key metrics
            if shares_outstanding == 0 or reported_mkt_cap == 0:
                metrics_data = await self._get_key_metrics_fallback(ticker, api_key)
                if metrics_data:
                    if reported_mkt_cap == 0 and metrics_data.get('marketCap', 0) > 0:
                        profile['mktCap'] = metrics_data['marketCap']
                        profile['mkt_cap_from_metrics'] = True
                        logger.info(f"Used key metrics for market cap for {ticker}: ${metrics_data['marketCap']:,.0f}")
            
        except Exception as e:
            logger.error(f"Error validating market cap for {ticker}: {e}")
        
        return profile

    async def _get_real_time_quote(self, ticker: str, api_key: str = None) -> Dict[str, Any]:
        """Get real-time quote data as fallback"""
        try:
            url = f"{self.fmp_base_url}/quote/{ticker}"
            params = {"apikey": api_key or self.fmp_api_key}
            
            data = await self._rate_limited_request(url, params, api_key=api_key)
            if data and isinstance(data, list) and len(data) > 0:
                return data[0]
        except Exception as e:
            logger.error(f"Error getting real-time quote for {ticker}: {e}")
        
        return {}

    async def _get_key_metrics_fallback(self, ticker: str, api_key: str = None) -> Dict[str, Any]:
        """Get key metrics as fallback for market cap"""
        try:
            url = f"{self.fmp_base_url}/key-metrics/{ticker}"
            params = {"limit": 1, "apikey": api_key or self.fmp_api_key}
            
            data = await self._rate_limited_request(url, params, api_key=api_key)
            if data and isinstance(data, list) and len(data) > 0:
                return data[0]
        except Exception as e:
            logger.error(f"Error getting key metrics for {ticker}: {e}")
        
        return {}

    async def get_financial_statements(self, ticker: str, years: int = 5, api_key: str = None) -> Dict[str, List]:
        """Get income statement, balance sheet, and cash flow data"""
        statements = {}
        api_key = api_key or self.fmp_api_key
        
        # Income Statement
        url = f"{self.fmp_base_url}/income-statement/{ticker}"
        params = {"limit": years, "apikey": api_key}
        statements["income"] = await self._rate_limited_request(url, params, api_key=api_key)
        
        # Balance Sheet
        url = f"{self.fmp_base_url}/balance-sheet-statement/{ticker}"
        statements["balance"] = await self._rate_limited_request(url, params, api_key=api_key)
        
        # Cash Flow Statement
        url = f"{self.fmp_base_url}/cash-flow-statement/{ticker}"
        statements["cashflow"] = await self._rate_limited_request(url, params, api_key=api_key)
        
        return statements

    async def get_key_metrics(self, ticker: str, years: int = 5, api_key: str = None) -> List[Dict]:
        """Get key financial metrics"""
        url = f"{self.fmp_base_url}/key-metrics/{ticker}"
        params = {"limit": years, "apikey": api_key or self.fmp_api_key}
        
        data = await self._rate_limited_request(url, params, api_key=api_key)
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

    async def get_financial_ratios(self, ticker: str, years: int = 5, api_key: str = None) -> List[Dict]:
        """Get financial ratios"""
        url = f"{self.fmp_base_url}/ratios/{ticker}"
        params = {"limit": years, "apikey": api_key or self.fmp_api_key}
        
        return await self._rate_limited_request(url, params, api_key=api_key)

    async def get_insider_trading(self, ticker: str, api_key: str = None) -> List[Dict]:
        """Get insider trading data"""
        url = f"{self.fmp_base_url}/insider-trading"
        params = {"symbol": ticker, "limit": 50, "apikey": api_key or self.fmp_api_key}
        
        return await self._rate_limited_request(url, params, api_key=api_key)

    async def get_industry_pe(self, industry: str) -> float:
        """Get industry average P/E ratio"""
        # This would typically require industry classification and averaging
        # For now, return a default industry PE
        return 20.0  # Default industry PE

    async def search_company_news(self, company_name: str, ticker: str, serp_api_key: str = None) -> List[Dict]:
        """Search for recent company news using SERP API"""
        api_key = serp_api_key or self.serp_api_key
        if not api_key:
            logger.warning("No SERP API key provided for news search")
            return []
        
        query = f"{company_name} {ticker} stock news"
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "num": 10,
            "tbm": "nws"  # News search
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(self.serp_base_url, params=params)
                    
                    # Handle specific error codes
                    if response.status_code == 429:
                        logger.warning(f"SERP API rate limit exceeded (429) on attempt {attempt + 1}/{max_retries}")
                        if attempt < max_retries - 1:
                            wait_time = 60 * (attempt + 1)  # Wait 60s, 120s, 180s
                            logger.info(f"Waiting {wait_time} seconds before retry for SERP API")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error("SERP API rate limit exceeded after all retries")
                            return []
                    
                    if response.status_code == 401:
                        logger.error("Invalid SERP API key")
                        return []
                    
                    if response.status_code == 403:
                        logger.error("SERP API key does not have permission")
                        return []
                    
                    response.raise_for_status()
                    data = response.json()
                    news_results = data.get("news_results", [])
                    
                    if news_results:
                        logger.info(f"Successfully fetched {len(news_results)} news articles for {ticker}")
                        return news_results
                    else:
                        logger.warning(f"No news results found for {ticker}")
                        return []
                        
            except httpx.HTTPStatusError as e:
                logger.error(f"SERP API HTTP error {e.response.status_code}: {e}")
                if attempt < max_retries - 1:
                    wait_time = 10 * (attempt + 1)
                    logger.info(f"Waiting {wait_time} seconds before retry for SERP API")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    return []
                    
            except httpx.TimeoutException as e:
                logger.error(f"SERP API timeout error: {e}")
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)
                    logger.info(f"Waiting {wait_time} seconds before retry for SERP API timeout")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    return []
                    
            except Exception as e:
                logger.error(f"SERP API error: {e}")
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)
                    logger.info(f"Waiting {wait_time} seconds before retry for SERP API error")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    return []
        
        return []

    async def search_company_info(self, company_name: str, query_type: str, serp_api_key: str = None) -> List[Dict]:
        """Search for specific company information"""
        api_key = serp_api_key or self.serp_api_key
        if not api_key:
            logger.warning("No SERP API key provided for company info search")
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
            "api_key": api_key,
            "num": 5
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(self.serp_base_url, params=params)
                    
                    # Handle specific error codes
                    if response.status_code == 429:
                        logger.warning(f"SERP API rate limit exceeded (429) for {query_type} on attempt {attempt + 1}/{max_retries}")
                        if attempt < max_retries - 1:
                            wait_time = 60 * (attempt + 1)  # Wait 60s, 120s, 180s
                            logger.info(f"Waiting {wait_time} seconds before retry for SERP API {query_type}")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(f"SERP API rate limit exceeded for {query_type} after all retries")
                            return []
                    
                    if response.status_code == 401:
                        logger.error("Invalid SERP API key")
                        return []
                    
                    if response.status_code == 403:
                        logger.error("SERP API key does not have permission")
                        return []
                    
                    response.raise_for_status()
                    data = response.json()
                    organic_results = data.get("organic_results", [])
                    
                    if organic_results:
                        logger.info(f"Successfully fetched {len(organic_results)} results for {query_type}")
                        return organic_results
                    else:
                        logger.warning(f"No results found for {query_type}")
                        return []
                        
            except httpx.HTTPStatusError as e:
                logger.error(f"SERP API HTTP error {e.response.status_code} for {query_type}: {e}")
                if attempt < max_retries - 1:
                    wait_time = 10 * (attempt + 1)
                    logger.info(f"Waiting {wait_time} seconds before retry for SERP API {query_type}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    return []
                    
            except httpx.TimeoutException as e:
                logger.error(f"SERP API timeout error for {query_type}: {e}")
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)
                    logger.info(f"Waiting {wait_time} seconds before retry for SERP API {query_type} timeout")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    return []
                    
            except Exception as e:
                logger.error(f"SERP API error for {query_type}: {e}")
                if attempt < max_retries - 1:
                    wait_time = 5 * (attempt + 1)
                    logger.info(f"Waiting {wait_time} seconds before retry for SERP API {query_type} error")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    return []
        
        return []
