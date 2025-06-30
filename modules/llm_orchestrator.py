import google.generativeai as genai
import os
import json
from typing import Dict, Any, List

class LLMOrchestrator:
    def __init__(self):
        # Initialize with environment variable as fallback
        self.default_api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
        self.default_model = None
        if self.default_api_key:
            genai.configure(api_key=self.default_api_key)
            self.default_model = genai.GenerativeModel('gemini-1.5-flash')
    
    def _get_model(self, api_key: str = None):
        """Get a model instance for the specified API key"""
        if api_key:
            # Basic validation - Gemini keys typically start with "AI"
            if not self._is_valid_gemini_key_format(api_key):
                print(f"Warning: API key format doesn't look like a valid Gemini key")
                # Still try to use it, but warn the user
            
            # Create a new configuration for this specific API key
            genai.configure(api_key=api_key)
            return genai.GenerativeModel('gemini-1.5-flash')
        else:
            # Use default model
            return self.default_model
    
    def _is_valid_gemini_key_format(self, api_key: str) -> bool:
        """Basic validation to check if API key format looks like Gemini"""
        if not api_key:
            return False
        
        # Gemini API keys typically:
        # - Start with "AI" 
        # - Are around 40-50 characters long
        # - Contain alphanumeric characters
        if len(api_key) < 30 or len(api_key) > 60:
            return False
        
        if not api_key.startswith("AI"):
            return False
        
        # Check if it contains only valid characters
        import re
        if not re.match(r'^[A-Za-z0-9_-]+$', api_key):
            return False
        
        return True
    
    async def analyze_business_fundamentals(self, company_profile: Dict, news_data: List[Dict], api_key: str = None) -> Dict[str, Any]:
        """Analyze business fundamentals using Gemini"""
        
        model = self._get_model(api_key)
        if not model:
            return {
                "revenue_model_score": 15,
                "competitive_moat_score": 15,
                "industry_position_score": 15,
                "management_quality_score": 15,
                "total_score": 60,
                "analysis": {
                    "revenue_model": "Analysis unavailable - No API key provided",
                    "competitive_moat": "Analysis unavailable - No API key provided",
                    "industry_position": "Analysis unavailable - No API key provided",
                    "management_quality": "Analysis unavailable - No API key provided"
                },
                "key_strengths": ["Analysis unavailable - No API key provided"],
                "key_concerns": ["Analysis unavailable - No API key provided"]
            }
        
        prompt = """
        Analyze the business fundamentals of {company_name} based on the following information:
        
        Company Profile:
        - Industry: {industry}
        - Sector: {sector}
        - Market Cap: ${market_cap:,.0f}
        - Description: {description}
        - CEO: {ceo}
        - Website: {website}
        - Exchange: {exchange}
        
        Please evaluate and score (0-100) each of the following criteria:
        
        1. Revenue Model Clarity (25 points): How clear and sustainable is the business model?
        2. Competitive Moat (25 points): Does the company have sustainable competitive advantages (IP, scale, brand, network effects)?
        3. Industry Position (25 points): Is the company a leader in its industry (top 3 position)?
        4. Management Quality (25 points): Based on available information, assess management quality.
        
        Return your analysis in the following JSON format:
        {{
            "revenue_model_score": <0-25>,
            "competitive_moat_score": <0-25>,
            "industry_position_score": <0-25>,
            "management_quality_score": <0-25>,
            "total_score": <0-100>,
            "analysis": {{
                "revenue_model": "<brief analysis>",
                "competitive_moat": "<brief analysis>",
                "industry_position": "<brief analysis>",
                "management_quality": "<brief analysis>"
            }},
            "key_strengths": ["<strength1>", "<strength2>"],
            "key_concerns": ["<concern1>", "<concern2>"]
        }}
        """.format(
            company_name=company_profile.get('companyName', 'this company'),
            industry=company_profile.get('industry', 'N/A'),
            sector=company_profile.get('sector', 'N/A'),
            market_cap=company_profile.get('mktCap', 0),
            description=company_profile.get('description', 'N/A')[:500],
            ceo=company_profile.get('ceo', 'N/A'),
            website=company_profile.get('website', 'N/A'),
            exchange=company_profile.get('exchangeShortName', 'N/A')
        )
        
        try:
            response = model.generate_content(prompt)
            # Parse JSON from response
            json_str = response.text.strip()
            if json_str.startswith('```json'):
                json_str = json_str[7:-3]
            elif json_str.startswith('```'):
                json_str = json_str[3:-3]
            
            # Parse the JSON response
            try:
                result = json.loads(json_str)
            except Exception:
                result = None
            
            # Ensure result is a dict
            if not isinstance(result, dict):
                return {
                    "revenue_model_score": 15,
                    "competitive_moat_score": 15,
                    "industry_position_score": 15,
                    "management_quality_score": 15,
                    "total_score": 60,
                    "analysis": {
                        "revenue_model": "Analysis unavailable - Invalid response format",
                        "competitive_moat": "Analysis unavailable - Invalid response format",
                        "industry_position": "Analysis unavailable - Invalid response format",
                        "management_quality": "Analysis unavailable - Invalid response format"
                    },
                    "key_strengths": ["Analysis unavailable - Invalid response format"],
                    "key_concerns": ["Analysis unavailable - Invalid response format"]
                }
            
            # Ensure all string values are safe for formatting
            if isinstance(result, dict):
                for key, value in result.items():
                    if isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            if isinstance(subvalue, str):
                                # Replace any curly braces that might be interpreted as format specifiers
                                result[key][subkey] = subvalue.replace('{', '{{').replace('}', '}}')
                    elif isinstance(value, list):
                        result[key] = [str(item).replace('{', '{{').replace('}', '}}') if isinstance(item, str) else item for item in value]
                    elif isinstance(value, str):
                        result[key] = value.replace('{', '{{').replace('}', '}}')
            
            return result
        except Exception as e:
            # Check for specific error types
            error_str = str(e).lower()
            
            # Authentication/API key errors
            if any(keyword in error_str for keyword in ["401", "unauthorized", "invalid api key", "authentication", "permission"]):
                print(f"Gemini API authentication error: {e}")
                return {
                    "revenue_model_score": 15,
                    "competitive_moat_score": 15,
                    "industry_position_score": 15,
                    "management_quality_score": 15,
                    "total_score": 60,
                    "analysis": {
                        "revenue_model": "Analysis unavailable - Invalid API key",
                        "competitive_moat": "Analysis unavailable - Invalid API key",
                        "industry_position": "Analysis unavailable - Invalid API key",
                        "management_quality": "Analysis unavailable - Invalid API key"
                    },
                    "key_strengths": ["Analysis unavailable - Invalid API key"],
                    "key_concerns": ["Analysis unavailable - Invalid API key"]
                }
            
            # Rate limit/quota errors
            elif "429" in error_str or "quota" in error_str or "exceeded" in error_str:
                print(f"Gemini API quota exceeded: {e}")
                return {
                    "revenue_model_score": 15,
                    "competitive_moat_score": 15,
                    "industry_position_score": 15,
                    "management_quality_score": 15,
                    "total_score": 60,
                    "analysis": {
                        "revenue_model": "Analysis unavailable - API quota exceeded",
                        "competitive_moat": "Analysis unavailable - API quota exceeded",
                        "industry_position": "Analysis unavailable - API quota exceeded",
                        "management_quality": "Analysis unavailable - API quota exceeded"
                    },
                    "key_strengths": ["Analysis unavailable - API quota exceeded"],
                    "key_concerns": ["Analysis unavailable - API quota exceeded"]
                }
            
            # General fallback for other errors
            else:
                print(f"Gemini API error: {e}")
                fallback = {
                    "revenue_model_score": 15,
                    "competitive_moat_score": 15,
                    "industry_position_score": 15,
                    "management_quality_score": 15,
                    "total_score": 60,
                    "analysis": {
                        "revenue_model": "Analysis unavailable - API error",
                        "competitive_moat": "Analysis unavailable - API error",
                        "industry_position": "Analysis unavailable - API error",
                        "management_quality": "Analysis unavailable - API error"
                    },
                    "key_strengths": ["Analysis unavailable - API error"],
                    "key_concerns": ["Analysis unavailable - API error"]
                }
                return fallback
    
    async def analyze_tam_and_growth(self, company_profile: Dict, news_data: List[Dict], api_key: str = None) -> Dict[str, Any]:
        """Analyze Total Addressable Market and growth initiatives"""
        
        model = self._get_model(api_key)
        if not model:
            return {
                "tam_score": 25,
                "growth_initiatives_score": 25,
                "total_score": 50,
                "analysis": {
                    "tam_assessment": "Analysis unavailable - No API key provided",
                    "growth_initiatives": "Analysis unavailable - No API key provided"
                }
            }
        
        prompt = """
        Analyze the Total Addressable Market (TAM) and growth potential for {company_name}:
        
        Company: {company_name}
        Industry: {industry}
        Sector: {sector}
        Description: {description}
        
        Recent News Headlines:
        {news_headlines}
        
        Please assess:
        1. TAM Size (0-50 points): How large is the total addressable market?
        2. Growth Initiatives (0-50 points): What growth initiatives or expansion plans are evident?
        
        Return JSON format:
        {{
            "tam_score": <0-50>,
            "growth_initiatives_score": <0-50>,
            "total_score": <0-100>,
            "analysis": {{
                "tam_assessment": "<TAM analysis>",
                "growth_initiatives": "<growth analysis>"
            }}
        }}
        """.format(
            company_name=company_profile.get('companyName', 'this company'),
            industry=company_profile.get('industry', 'N/A'),
            sector=company_profile.get('sector', 'N/A'),
            description=company_profile.get('description', 'N/A')[:500],
            news_headlines=[item.get('title', '') for item in news_data[:5]]
        )
        
        try:
            response = model.generate_content(prompt)
            json_str = response.text.strip()
            if json_str.startswith('```json'):
                json_str = json_str[7:-3]
            elif json_str.startswith('```'):
                json_str = json_str[3:-3]
            
            # Parse the JSON response
            try:
                result = json.loads(json_str)
            except Exception:
                result = None
            
            # Ensure result is a dict
            if not isinstance(result, dict):
                return {
                    "tam_score": 25,
                    "growth_initiatives_score": 25,
                    "total_score": 50,
                    "analysis": {
                        "tam_assessment": "Analysis unavailable",
                        "growth_initiatives": "Analysis unavailable"
                    }
                }
            
            # Ensure all string values are safe for formatting
            if isinstance(result, dict):
                for key, value in result.items():
                    if isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            if isinstance(subvalue, str):
                                # Replace any curly braces that might be interpreted as format specifiers
                                result[key][subkey] = subvalue.replace('{', '{{').replace('}', '}}')
                    elif isinstance(value, list):
                        result[key] = [str(item).replace('{', '{{').replace('}', '}}') if isinstance(item, str) else item for item in value]
                    elif isinstance(value, str):
                        result[key] = value.replace('{', '{{').replace('}', '}}')
            
            return result
        except Exception as e:
            # Check for quota exceeded error
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower() or "exceeded" in error_str.lower():
                print(f"Gemini API quota exceeded: {e}")
                return {
                    "tam_score": 25,
                    "growth_initiatives_score": 25,
                    "total_score": 50,
                    "analysis": {
                        "tam_assessment": "Analysis unavailable - API quota exceeded",
                        "growth_initiatives": "Analysis unavailable - API quota exceeded"
                    }
                }
            
            # General fallback for other errors
            fallback = {
                "tam_score": 25,
                "growth_initiatives_score": 25,
                "total_score": 50,
                "analysis": {
                    "tam_assessment": "Analysis unavailable",
                    "growth_initiatives": "Analysis unavailable"
                }
            }
            return fallback
    
    async def analyze_sentiment_and_risks(self, company_profile: Dict, news_data: List[Dict], insider_trading: List[Dict], api_key: str = None) -> Dict[str, Any]:
        """Analyze sentiment and identify red flags"""
        
        model = self._get_model(api_key)
        if not model:
            return {
                "news_sentiment_score": 25,
                "red_flags_score": 40,
                "total_score": 65,
                "analysis": {
                    "sentiment_summary": "Analysis unavailable - No API key provided",
                    "identified_red_flags": ["Analysis unavailable - No API key provided"],
                    "positive_indicators": ["Analysis unavailable - No API key provided"]
                }
            }
        
        news_titles = [item.get('title', '') for item in news_data[:10]]
        insider_summary = "Recent insider transactions: {} transactions".format(len(insider_trading))
        
        prompt = """
        Analyze sentiment and red flags for {company_name}:
        
        Company: {company_name}
        
        Recent News Headlines:
        {news_titles}
        
        Insider Trading: {insider_summary}
        
        Please assess and score (0-100):
        1. News Sentiment (0-40 points): Overall sentiment from recent news
        2. Red Flags Assessment (0-60 points): Any red flags like lawsuits, fraud, management issues, regulatory problems
        
        Look for:
        - Positive: innovation, partnerships, growth, awards, strong earnings
        - Negative: lawsuits, investigations, regulatory issues, management departures, scandals
        
        Return JSON format:
        {{
            "news_sentiment_score": <0-40>,
            "red_flags_score": <0-60>,
            "total_score": <0-100>,
            "analysis": {{
                "sentiment_summary": "<brief sentiment analysis>",
                "identified_red_flags": ["<flag1>", "<flag2>"],
                "positive_indicators": ["<positive1>", "<positive2>"]
            }}
        }}
        """.format(
            company_name=company_profile.get('companyName', 'this company'),
            news_titles=news_titles,
            insider_summary=insider_summary
        )
        
        try:
            response = model.generate_content(prompt)
            json_str = response.text.strip()
            if json_str.startswith('```json'):
                json_str = json_str[7:-3]
            elif json_str.startswith('```'):
                json_str = json_str[3:-3]
            
            # Parse the JSON response
            try:
                result = json.loads(json_str)
            except Exception:
                result = None
            
            # Ensure result is a dict
            if not isinstance(result, dict):
                return {
                    "news_sentiment_score": 25,
                    "red_flags_score": 40,
                    "total_score": 65,
                    "analysis": {
                        "sentiment_summary": "Analysis unavailable",
                        "identified_red_flags": ["Analysis unavailable"],
                        "positive_indicators": ["Analysis unavailable"]
                    }
                }
            
            # Ensure all string values are safe for formatting
            if isinstance(result, dict):
                for key, value in result.items():
                    if isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            if isinstance(subvalue, str):
                                # Replace any curly braces that might be interpreted as format specifiers
                                result[key][subkey] = subvalue.replace('{', '{{').replace('}', '}}')
                    elif isinstance(value, list):
                        result[key] = [str(item).replace('{', '{{').replace('}', '}}') if isinstance(item, str) else item for item in value]
                    elif isinstance(value, str):
                        result[key] = value.replace('{', '{{').replace('}', '}}')
            
            return result
        except Exception as e:
            # Check for quota exceeded error
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower() or "exceeded" in error_str.lower():
                print(f"Gemini API quota exceeded: {e}")
                return {
                    "news_sentiment_score": 25,
                    "red_flags_score": 40,
                    "total_score": 65,
                    "analysis": {
                        "sentiment_summary": "Analysis unavailable - API quota exceeded",
                        "identified_red_flags": ["Analysis unavailable - API quota exceeded"],
                        "positive_indicators": ["Analysis unavailable - API quota exceeded"]
                    }
                }
            
            # General fallback for other errors
            fallback = {
                "news_sentiment_score": 25,
                "red_flags_score": 40,
                "total_score": 65,
                "analysis": {
                    "sentiment_summary": "Analysis unavailable",
                    "identified_red_flags": ["Analysis unavailable"],
                    "positive_indicators": ["Analysis unavailable"]
                }
            }
            return fallback
    
    async def generate_dcf_valuation(self, statements: Dict, company_profile: Dict, api_key: str = None) -> Dict[str, Any]:
        """Generate DCF valuation analysis"""
        
        model = self._get_model(api_key)
        if not model:
            return {
                "estimated_fair_value": company_profile.get('mktCap', 0),
                "current_market_cap": company_profile.get('mktCap', 0),
                "upside_percentage": 0,
                "confidence_level": "low",
                "key_assumptions": ["Analysis unavailable - No API key provided"],
                "analysis": "Analysis unavailable - No API key provided",
                "data_notes": self._get_data_freshness_notes(company_profile)
            }
        
        latest_income = statements.get("income", [{}])[0] if statements.get("income") else {}
        latest_cashflow = statements.get("cashflow", [{}])[0] if statements.get("cashflow") else {}
        
        # Get data freshness notes
        data_notes = self._get_data_freshness_notes(company_profile)
        
        prompt = f"""
        Perform a simplified DCF (Discounted Cash Flow) valuation for {company_profile.get('companyName', 'this company')}:
        
        Financial Data:
        - Revenue: ${latest_income.get('revenue', 0):,.0f}
        - Free Cash Flow: ${latest_cashflow.get('freeCashFlow', 0):,.0f}
        - Market Cap: ${company_profile.get('mktCap', 0):,.0f}
        - Industry: {company_profile.get('industry', 'N/A')}
        
        Data Notes: {data_notes}
        
        Please provide:
        1. Estimated fair value range
        2. Key assumptions used
        3. Upside/downside vs current market cap
        
        Return JSON format:
        {{
            "estimated_fair_value": <estimated_value>,
            "current_market_cap": <current_market_cap>,
            "upside_percentage": <upside_percent>,
            "confidence_level": "<high/medium/low>",
            "key_assumptions": ["<assumption1>", "<assumption2>"],
            "analysis": "<brief DCF analysis>",
            "data_notes": "<data freshness and validation notes>"
        }}
        """
        
        try:
            response = model.generate_content(prompt)
            json_str = response.text.strip()
            if json_str.startswith('```json'):
                json_str = json_str[7:-3]
            elif json_str.startswith('```'):
                json_str = json_str[3:-3]
            
            result = json.loads(json_str)
            result['data_notes'] = data_notes
            return result
        except Exception as e:
            return {
                "estimated_fair_value": company_profile.get('mktCap', 0),
                "current_market_cap": company_profile.get('mktCap', 0),
                "upside_percentage": 0,
                "confidence_level": "low",
                "key_assumptions": ["Analysis unavailable"],
                "analysis": "DCF analysis unavailable",
                "data_notes": data_notes
            }

    def _get_data_freshness_notes(self, company_profile: Dict) -> str:
        """Generate data freshness and validation notes"""
        notes = []
        
        # Check for calculated/fallback data
        if company_profile.get('shares_calculated'):
            notes.append("Shares outstanding was calculated from market cap and price")
        
        if company_profile.get('mkt_cap_calculated'):
            notes.append("Market cap was recalculated due to data discrepancy")
        
        if company_profile.get('mkt_cap_from_metrics'):
            notes.append("Market cap sourced from key metrics endpoint")
        
        if company_profile.get('price_from_quote'):
            notes.append("Price sourced from real-time quote")
        
        # Check profile freshness
        if company_profile.get('profile_freshness') == 'fallback':
            notes.append("Using fallback profile data")
        
        # Check for missing critical data
        if not company_profile.get('sharesOutstanding'):
            notes.append("Shares outstanding data unavailable")
        
        if not company_profile.get('mktCap'):
            notes.append("Market cap data unavailable")
        
        if not company_profile.get('price'):
            notes.append("Price data unavailable")
        
        # Add timestamp if available
        if company_profile.get('lastUpdated'):
            notes.append(f"Last updated: {company_profile['lastUpdated']}")
        
        return "; ".join(notes) if notes else "All data appears fresh and validated"
