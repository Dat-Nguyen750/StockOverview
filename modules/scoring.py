import numpy as np
from typing import Dict, Any, List, Tuple
from datetime import datetime

class FinancialScorer:
    def __init__(self):
        self.weights = {
            "financial_health": 0.35,
            "business_fundamentals": 0.20,
            "valuation": 0.20,
            "growth_potential": 0.15,
            "sentiment": 0.10
        }
    
    def calculate_revenue_cagr(self, income_statements: List[Dict]) -> float:
        """Calculate 5-year revenue CAGR"""
        if len(income_statements) < 2:
            return 0.0
        
        revenues = [stmt.get("revenue", 0) for stmt in income_statements if stmt.get("revenue")]
        if len(revenues) < 2:
            return 0.0
        
        # Sort by date (newest first from FMP)
        revenues.reverse()  # Oldest first for CAGR calculation
        
        if revenues[0] <= 0 or revenues[-1] <= 0:
            return 0.0
        
        years = len(revenues) - 1
        cagr = (revenues[-1] / revenues[0]) ** (1/years) - 1
        return cagr * 100  # Return as percentage
    
    def calculate_financial_health_score(self, statements: Dict, ratios: List[Dict], metrics: List[Dict]) -> Tuple[float, Dict]:
        """Calculate financial health score (35% weight)"""
        scores = {}
        details = {}
        
        # Revenue Growth (CAGR over 5 years) - 20 points
        cagr = self.calculate_revenue_cagr(statements.get("income", []))
        details["revenue_cagr"] = cagr
        if cagr >= 15:
            scores["revenue_growth"] = 20
        elif cagr >= 10:
            scores["revenue_growth"] = 15
        elif cagr >= 5:
            scores["revenue_growth"] = 10
        elif cagr >= 0:
            scores["revenue_growth"] = 5
        else:
            scores["revenue_growth"] = 0
        
        # Profitability (Net Margin > 10%) - 15 points
        latest_income = statements.get("income", [{}])[0] if statements.get("income") else {}
        revenue = latest_income.get("revenue", 1)
        net_income = latest_income.get("netIncome", 0)
        net_margin = (net_income / revenue * 100) if revenue > 0 else 0
        details["net_margin"] = net_margin
        
        if net_margin >= 20:
            scores["profitability"] = 15
        elif net_margin >= 15:
            scores["profitability"] = 12
        elif net_margin >= 10:
            scores["profitability"] = 10
        elif net_margin >= 5:
            scores["profitability"] = 6
        elif net_margin > 0:
            scores["profitability"] = 3
        else:
            scores["profitability"] = 0
        
        # Free Cash Flow (positive 3 years) - 15 points
        cashflows = statements.get("cashflow", [])[:3]
        positive_fcf_years = sum(1 for cf in cashflows if cf.get("freeCashFlow", 0) > 0)
        details["positive_fcf_years"] = positive_fcf_years
        scores["free_cash_flow"] = min(positive_fcf_years * 5, 15)
        
        # Debt Management - 20 points
        latest_balance = statements.get("balance", [{}])[0] if statements.get("balance") else {}
        total_debt = latest_balance.get("totalDebt", 0)
        total_equity = latest_balance.get("totalStockholdersEquity", 1)
        debt_to_equity = total_debt / total_equity if total_equity > 0 else float('inf')
        details["debt_to_equity"] = debt_to_equity
        
        # Interest coverage
        ebit = latest_income.get("operatingIncome", 0)
        interest_expense = latest_income.get("interestExpense", 1)
        interest_coverage = ebit / interest_expense if interest_expense > 0 else float('inf')
        details["interest_coverage"] = interest_coverage
        
        debt_score = 0
        if debt_to_equity < 0.5 and interest_coverage > 10:
            debt_score = 20
        elif debt_to_equity < 1.0 and interest_coverage > 5:
            debt_score = 15
        elif debt_to_equity < 1.5 and interest_coverage > 3:
            debt_score = 10
        elif debt_to_equity < 2.0 and interest_coverage > 2:
            debt_score = 5
        
        scores["debt_management"] = debt_score
        
        # Liquidity (Current Ratio > 1.5) - 15 points
        current_assets = latest_balance.get("totalCurrentAssets", 0)
        current_liabilities = latest_balance.get("totalCurrentLiabilities", 1)
        current_ratio = current_assets / current_liabilities if current_liabilities > 0 else 0
        details["current_ratio"] = current_ratio
        
        if current_ratio >= 2.5:
            scores["liquidity"] = 15
        elif current_ratio >= 2.0:
            scores["liquidity"] = 12
        elif current_ratio >= 1.5:
            scores["liquidity"] = 10
        elif current_ratio >= 1.0:
            scores["liquidity"] = 6
        else:
            scores["liquidity"] = 0
        
        # ROE > 15% - 15 points
        latest_metrics = metrics[0] if metrics else {}
        roe = latest_metrics.get("roe", 0) * 100 if latest_metrics.get("roe") else 0
        details["roe"] = roe
        
        if roe >= 25:
            scores["roe"] = 15
        elif roe >= 20:
            scores["roe"] = 12
        elif roe >= 15:
            scores["roe"] = 10
        elif roe >= 10:
            scores["roe"] = 6
        elif roe > 0:
            scores["roe"] = 3
        else:
            scores["roe"] = 0
        
        total_score = sum(scores.values())
        return total_score, {"scores": scores, "details": details}
    
    def calculate_valuation_score(self, profile: Dict, metrics: List[Dict], industry_pe: float = 20.0) -> Tuple[float, Dict]:
        """Calculate valuation score (20% weight)"""
        scores = {}
        details = {}
        
        latest_metrics = metrics[0] if metrics else {}
        
        # P/E vs Industry - 30 points
        pe_ratio = latest_metrics.get("peRatio", 0)
        details["pe_ratio"] = pe_ratio
        details["industry_pe"] = industry_pe
        
        if pe_ratio > 0:
            pe_premium = (pe_ratio - industry_pe) / industry_pe * 100
            details["pe_premium"] = pe_premium
            
            if pe_premium <= -20:  # 20% discount to industry
                scores["pe_valuation"] = 30
            elif pe_premium <= -10:
                scores["pe_valuation"] = 25
            elif pe_premium <= 0:
                scores["pe_valuation"] = 20
            elif pe_premium <= 10:
                scores["pe_valuation"] = 15
            elif pe_premium <= 25:
                scores["pe_valuation"] = 10
            else:
                scores["pe_valuation"] = 0
        else:
            scores["pe_valuation"] = 0
        
        # PEG Ratio - 30 points
        peg_ratio = latest_metrics.get("pegRatio", 0)
        details["peg_ratio"] = peg_ratio
        
        if peg_ratio > 0:
            if peg_ratio <= 0.5:
                scores["peg_ratio"] = 30
            elif peg_ratio <= 1.0:
                scores["peg_ratio"] = 25
            elif peg_ratio <= 1.5:
                scores["peg_ratio"] = 15
            elif peg_ratio <= 2.0:
                scores["peg_ratio"] = 10
            else:
                scores["peg_ratio"] = 0
        else:
            scores["peg_ratio"] = 15  # Neutral if not available
        
        # Price to Free Cash Flow - 25 points
        price_to_fcf = latest_metrics.get("pfcfRatio", 0)
        details["price_to_fcf"] = price_to_fcf
        
        if price_to_fcf > 0:
            if price_to_fcf <= 10:
                scores["price_to_fcf"] = 25
            elif price_to_fcf <= 15:
                scores["price_to_fcf"] = 20
            elif price_to_fcf <= 20:
                scores["price_to_fcf"] = 15
            elif price_to_fcf <= 30:
                scores["price_to_fcf"] = 10
            else:
                scores["price_to_fcf"] = 0
        else:
            scores["price_to_fcf"] = 10  # Neutral if not available
        
        # Price to Book - 15 points
        price_to_book = latest_metrics.get("pbRatio", 0)
        details["price_to_book"] = price_to_book
        
        if price_to_book > 0:
            if price_to_book <= 1.0:
                scores["price_to_book"] = 15
            elif price_to_book <= 2.0:
                scores["price_to_book"] = 12
            elif price_to_book <= 3.0:
                scores["price_to_book"] = 8
            elif price_to_book <= 5.0:
                scores["price_to_book"] = 5
            else:
                scores["price_to_book"] = 0
        else:
            scores["price_to_book"] = 8  # Neutral if not available
        
        total_score = sum(scores.values())
        return total_score, {"scores": scores, "details": details}
    
    def calculate_growth_score(self, statements: Dict) -> Tuple[float, Dict]:
        """Calculate growth potential score (15% weight) - without analyst estimates"""
        scores = {}
        details = {}
        
        # R&D Investment - 50 points (increased from 30)
        latest_income = statements.get("income", [{}])[0] if statements.get("income") else {}
        revenue = latest_income.get("revenue", 1)
        rd_expenses = latest_income.get("researchAndDevelopmentExpenses", 0)
        rd_ratio = (rd_expenses / revenue * 100) if revenue > 0 else 0
        details["rd_ratio"] = rd_ratio
        
        if rd_ratio >= 15:
            scores["rd_investment"] = 50
        elif rd_ratio >= 10:
            scores["rd_investment"] = 40
        elif rd_ratio >= 5:
            scores["rd_investment"] = 30
        elif rd_ratio >= 2:
            scores["rd_investment"] = 20
        elif rd_ratio > 0:
            scores["rd_investment"] = 15
        else:
            scores["rd_investment"] = 10  # Low for non-tech companies
        
        # CapEx Investment - 50 points (increased from 30)
        latest_cashflow = statements.get("cashflow", [{}])[0] if statements.get("cashflow") else {}
        capex = abs(latest_cashflow.get("capitalExpenditure", 0))
        capex_ratio = (capex / revenue * 100) if revenue > 0 else 0
        details["capex_ratio"] = capex_ratio
        
        if capex_ratio >= 8:
            scores["capex_investment"] = 50
        elif capex_ratio >= 5:
            scores["capex_investment"] = 40
        elif capex_ratio >= 3:
            scores["capex_investment"] = 30
        elif capex_ratio >= 1:
            scores["capex_investment"] = 20
        else:
            scores["capex_investment"] = 15
        
        total_score = sum(scores.values())
        return total_score, {"scores": scores, "details": details}
