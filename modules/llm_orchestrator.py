import google.generativeai as genai
import os
import json
from typing import Dict, Any, List

class LLMOrchestrator:
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    async def analyze_business_fundamentals(self, company_profile: Dict, news_data: List[Dict]) -> Dict[str, Any]:
        """Analyze business fundamentals using Gemini"""
        
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
            response = self.model.generate_content(prompt)
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
                        "revenue_model": "Analysis unavailable",
                        "competitive_moat": "Analysis unavailable",
                        "industry_position": "Analysis unavailable",
                        "management_quality": "Analysis unavailable"
                    },
                    "key_strengths": ["Analysis unavailable"],
                    "key_concerns": ["Analysis unavailable"]
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
            fallback = {
                "revenue_model_score": 15,
                "competitive_moat_score": 15,
                "industry_position_score": 15,
                "management_quality_score": 15,
                "total_score": 60,
                "analysis": {
                    "revenue_model": "Analysis unavailable",
                    "competitive_moat": "Analysis unavailable",
                    "industry_position": "Analysis unavailable",
                    "management_quality": "Analysis unavailable"
                },
                "key_strengths": ["Analysis unavailable"],
                "key_concerns": ["Analysis unavailable"]
            }
            return fallback
    
    async def analyze_tam_and_growth(self, company_profile: Dict, news_data: List[Dict]) -> Dict[str, Any]:
        """Analyze Total Addressable Market and growth initiatives"""
        
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
            response = self.model.generate_content(prompt)
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
    
    async def analyze_sentiment_and_risks(self, company_profile: Dict, news_data: List[Dict], insider_trading: List[Dict]) -> Dict[str, Any]:
        """Analyze sentiment and identify red flags"""
        
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
            response = self.model.generate_content(prompt)
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
    
    async def generate_dcf_valuation(self, statements: Dict, company_profile: Dict) -> Dict[str, Any]:
        """Generate DCF valuation analysis"""
        
        latest_income = statements.get("income", [{}])[0] if statements.get("income") else {}
        latest_cashflow = statements.get("cashflow", [{}])[0] if statements.get("cashflow") else {}
        
        prompt = f"""
        Perform a simplified DCF (Discounted Cash Flow) valuation for {company_profile.get('companyName', 'this company')}:
        
        Financial Data:
        - Revenue: ${latest_income.get('revenue', 0):,.0f}
        - Free Cash Flow: ${latest_cashflow.get('freeCashFlow', 0):,.0f}
        - Market Cap: ${company_profile.get('mktCap', 0):,.0f}
        - Industry: {company_profile.get('industry', 'N/A')}
        
        Please provide:
        1. Estimated fair value range
        2. Key assumptions used
        3. Upside/downside vs current market cap
        
        Return JSON format:
        {
            "estimated_fair_value": <estimated_value>,
            "current_market_cap": <current_market_cap>,
            "upside_percentage": <upside_percent>,
            "confidence_level": "<high/medium/low>",
            "key_assumptions": ["<assumption1>", "<assumption2>"],
            "analysis": "<brief DCF analysis>"
        }
        """
        
        try:
            response = self.model.generate_content(prompt)
            json_str = response.text.strip()
            if json_str.startswith('```json'):
                json_str = json_str[7:-3]
            elif json_str.startswith('```'):
                json_str = json_str[3:-3]
            
            return json.loads(json_str)
        except Exception as e:
            return {
                "estimated_fair_value": company_profile.get('mktCap', 0),
                "current_market_cap": company_profile.get('mktCap', 0),
                "upside_percentage": 0,
                "confidence_level": "low",
                "key_assumptions": ["Analysis unavailable"],
                "analysis": "DCF analysis unavailable"
            }
