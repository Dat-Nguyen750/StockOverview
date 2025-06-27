import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from modules.data_fetcher import DataFetcher
from modules.scoring import FinancialScorer
from modules.llm_orchestrator import LLMOrchestrator
from modules.models import InvestmentVerdict
import json

class StockEvaluator:
    def __init__(self):
        self.data_fetcher = DataFetcher()
        self.scorer = FinancialScorer()
        self.llm_orchestrator = LLMOrchestrator()
    
    def _determine_verdict(self, composite_score: float) -> InvestmentVerdict:
        """Determine investment verdict based on composite score"""
        if composite_score >= 80:
            return InvestmentVerdict.STRONG_BUY
        elif composite_score >= 65:
            return InvestmentVerdict.BUY
        elif composite_score >= 50:
            return InvestmentVerdict.HOLD
        else:
            return InvestmentVerdict.AVOID
    
    def _generate_explanation(self, scores: Dict[str, float], verdict: InvestmentVerdict) -> str:
        """Generate explanation based on scores and verdict"""
        explanations = []
        
        # Analyze strengths
        strong_areas = [k for k, v in scores.items() if isinstance(v, (int, float)) and v >= 75]
        weak_areas = [k for k, v in scores.items() if isinstance(v, (int, float)) and v < 50]
        
        if strong_areas:
            explanations.append(f"Strong performance in {', '.join(str(strong) for strong in strong_areas).replace('_', ' ')}")
        
        if weak_areas:
            explanations.append(f"Concerns in {', '.join(str(strong) for strong in weak_areas).replace('_', ' ')}")
        
        # Add verdict-specific commentary
        if verdict == InvestmentVerdict.STRONG_BUY:
            explanations.append("Excellent overall fundamentals with strong growth prospects")
        elif verdict == InvestmentVerdict.BUY:
            explanations.append("Solid fundamentals with good long-term potential")
        elif verdict == InvestmentVerdict.HOLD:
            explanations.append("Mixed signals - monitor for improvement or deterioration")
        else:
            explanations.append("Significant concerns identified - avoid until improvements are made")
        
        # Ensure all explanation parts are strings
        return ". ".join(str(e) for e in explanations) + "."
    
    async def evaluate_company(
        self, 
        ticker: str, 
        include_detailed_analysis: bool = False,
        custom_weights: Optional[Dict[str, float]] = None,
        fmp_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        serp_api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Main evaluation function that orchestrates the entire analysis"""
        
        # Update weights if custom weights provided
        if custom_weights:
            self.scorer.weights.update(custom_weights)
        
        try:
            # Step 1: Gather all data concurrently
            
            # Basic company data
            company_profile = await self.data_fetcher.get_company_profile(ticker, api_key=fmp_api_key)
            if not company_profile:
                raise ValueError(f"Company profile not found for ticker {ticker}")
            
            # Financial data
            financial_data_tasks = [
                self.data_fetcher.get_financial_statements(ticker, api_key=fmp_api_key),
                self.data_fetcher.get_key_metrics(ticker, api_key=fmp_api_key),
                self.data_fetcher.get_financial_ratios(ticker, api_key=fmp_api_key),
                self.data_fetcher.get_insider_trading(ticker, api_key=fmp_api_key)
            ]
            
            statements, metrics, ratios, insider_trading = await asyncio.gather(*financial_data_tasks)
            
            # News and additional data
            company_name = company_profile.get('companyName', ticker)
            news_data = await self.data_fetcher.search_company_news(company_name, ticker, serp_api_key=serp_api_key)
            
            # Step 2: Calculate rule-based scores
            
            # Financial Health (35%)
            financial_health_score, financial_details = self.scorer.calculate_financial_health_score(
                statements, ratios, metrics
            )
            
            # Valuation (20%)
            industry_pe = await self.data_fetcher.get_industry_pe(company_profile.get('industry', ''))
            valuation_score, valuation_details = self.scorer.calculate_valuation_score(
                company_profile, metrics, industry_pe
            )
            
            # Growth Potential (15%) - partial
            growth_score, growth_details = self.scorer.calculate_growth_score(statements)
            
            # Step 3: LLM Analysis
            
            llm_tasks = [
                self.llm_orchestrator.analyze_business_fundamentals(company_profile, news_data, api_key=gemini_api_key),
                self.llm_orchestrator.analyze_tam_and_growth(company_profile, news_data, api_key=gemini_api_key),
                self.llm_orchestrator.analyze_sentiment_and_risks(company_profile, news_data, insider_trading, api_key=gemini_api_key)
            ]
            
            business_analysis, tam_analysis, sentiment_analysis = await asyncio.gather(*llm_tasks)

            print("\n[DEBUG] Raw LLM business_analysis:", business_analysis)
            print("[DEBUG] Raw LLM tam_analysis:", tam_analysis)
            print("[DEBUG] Raw LLM sentiment_analysis:", sentiment_analysis)

            # Ensure all LLM results are dicts
            def ensure_dict(obj, fallback, label=None):
                if not isinstance(obj, dict):
                    if label:
                        print(f"[DEBUG] {label} fallback used!")
                    return fallback
                return obj

            business_analysis = ensure_dict(
                business_analysis,
                {
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
                },
                label="business_analysis"
            )
            tam_analysis = ensure_dict(
                tam_analysis,
                {
                    "tam_score": 25,
                    "growth_initiatives_score": 25,
                    "total_score": 50,
                    "analysis": {
                        "tam_assessment": "Analysis unavailable",
                        "growth_initiatives": "Analysis unavailable"
                    }
                },
                label="tam_analysis"
            )
            sentiment_analysis = ensure_dict(
                sentiment_analysis,
                {
                    "news_sentiment_score": 25,
                    "red_flags_score": 40,
                    "total_score": 65,
                    "analysis": {
                        "sentiment_summary": "Analysis unavailable",
                        "identified_red_flags": ["Analysis unavailable"],
                        "positive_indicators": ["Analysis unavailable"]
                    }
                },
                label="sentiment_analysis"
            )

            # Ensure all *_score and total_score fields are numbers
            def safe_score(d, key, default=60):
                v = d.get(key, default)
                try:
                    return float(v)
                except (TypeError, ValueError):
                    return float(default)

            final_scores = {
                "financial_health": financial_health_score,
                "business_fundamentals": safe_score(business_analysis, "total_score", 60),
                "valuation": valuation_score,
                "growth_potential": (growth_score * 0.6) + (safe_score(tam_analysis, "total_score", 50) * 0.4),  # Combine rule-based and LLM
                "sentiment": safe_score(sentiment_analysis, "total_score", 65)
            }
            
            # Calculate composite score
            composite_score = sum(
                score * self.scorer.weights[category] 
                for category, score in final_scores.items()
            )
            
            # Determine verdict and explanation
            verdict = self._determine_verdict(composite_score)
            explanation = self._generate_explanation(final_scores, verdict)
            
            # Step 5: Build response
            # Generate a general summary using the same LLM orchestrator and model as the rest of the agent
            general_summary = ""
            try:
                print("[DEBUG] Sending summary prompt to LLM...")
                summary_prompt = f"""
                Based on the following analyses, provide a concise, human-readable summary (3-5 sentences) of the overall investment case for {company_name} ({ticker.upper()}).
                
                Business Analysis: {json.dumps(business_analysis)}
                TAM & Growth Analysis: {json.dumps(tam_analysis)}
                Sentiment & Risks Analysis: {json.dumps(sentiment_analysis)}
                Financial Health Score: {financial_health_score}
                Valuation Score: {valuation_score}
                Growth Score: {growth_score}
                Composite Score: {round(composite_score, 1)}
                Verdict: {verdict}
                Explanation: {explanation}
                
                Focus on the most important strengths, weaknesses, and the overall investment outlook.
                """
                summary_response = self.llm_orchestrator.model.generate_content(summary_prompt)
                print("[DEBUG] Raw LLM summary response:", summary_response)
                # Try to extract the summary text robustly
                if hasattr(summary_response, 'text'):
                    general_summary = summary_response.text.strip()
                elif hasattr(summary_response, 'result') and hasattr(summary_response.result, 'text'):
                    general_summary = summary_response.result.text.strip()
                else:
                    general_summary = str(summary_response).strip()
                if not general_summary:
                    general_summary = "Summary unavailable."
            except Exception as e:
                print("Error generating summary:", e)
                general_summary = "Summary unavailable."

            # --- Data freshness logic ---
            profile_freshness = company_profile.get('profile_freshness', 'fallback')
            metrics_freshness = (metrics[0].get('metrics_freshness', 'fallback') if metrics and isinstance(metrics, list) and isinstance(metrics[0], dict) else 'fallback')
            data_freshness = 'fresh' if profile_freshness == 'fresh' and metrics_freshness == 'fresh' else 'fallback'

            result = {
                "ticker": ticker.upper(),
                "company_name": company_name,
                "score_breakdown": final_scores,
                "composite_score": round(composite_score, 1),
                "verdict": verdict,
                "explanation": explanation,
                "general_summary": general_summary,
                "evaluation_timestamp": datetime.now().isoformat(),
                "data_sources": ["Financial Modeling Prep", "Google Gemini", "SERP API"],
                "data_freshness": data_freshness
            }
            
            # Add detailed analysis if requested
            if include_detailed_analysis:
                result["detailed_analysis"] = {
                    "financial_details": financial_details,
                    "valuation_details": valuation_details,
                    "growth_details": growth_details,
                    "business_analysis": business_analysis,
                    "tam_analysis": tam_analysis,
                    "sentiment_analysis": sentiment_analysis,
                    "company_profile": company_profile,
                    "key_metrics": metrics[:1] if metrics else [],
                    "insider_trading_summary": {
                        "recent_transactions": len(insider_trading),
                        "net_insider_buying": sum(1 for t in insider_trading if t.get('transactionType') == 'P-Purchase'),
                        "net_insider_selling": sum(1 for t in insider_trading if t.get('transactionType') == 'S-Sale')
                    },
                    "profile_freshness": profile_freshness,
                    "metrics_freshness": metrics_freshness
                }
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            if "rate limit" in error_msg.lower() or "429" in error_msg:
                rate_limit_status = self.data_fetcher.get_rate_limit_status(api_key=fmp_api_key)
                raise Exception(f"API rate limit exceeded for your API key. Daily requests used: {rate_limit_status['daily_requests_used']}/{rate_limit_status['daily_limit']}. Please try again later or upgrade your API plan.")
            elif "daily rate limit exceeded" in error_msg.lower():
                raise Exception(f"Daily API limit reached for your API key. Please try again tomorrow or upgrade your API plan.")
            else:
                raise Exception(f"Error fetching data for {ticker}: {error_msg}")
