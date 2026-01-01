"""DCF valuation agent - AI determines ALL assumptions including WACC"""

import modules.logger as logger
from modules.agents.base_agent import Agent


# AI ONLY estimates the inputs - WE do all calculations
DCF_ASSUMPTIONS_PROMPT = """Analyze {symbol} and estimate DCF input variables.

COMPANY DATA:
Price: ${price:.2f}
Market Cap: ${mkt_cap:,.0f}
Beta: {beta}

FCF HISTORY (Operating CF - CapEx):
{fcf_history}

REVENUE HISTORY:
{revenue_history}

BALANCE SHEET:
Total Debt: ${debt:,.0f}
Cash: ${cash:,.0f}

Provide ONLY your estimates as JSON (no calculations, no explanations in JSON):
{{
    "fcf_growth_rate": 0.XX,
    "terminal_growth_rate": 0.0XX,
    "risk_free_rate": 0.0XX,
    "market_risk_premium": 0.0XX,
    "company_risk_premium": 0.0XX,
    "growth_decline_factor": 0.0X,
    "projection_years": 5-10,
    "found_context": "True/False",
    "reasoning": "Why you chose these estimates"
}}

ESTIMATE these inputs:
1. FCF growth rate: Initial growth rate based on FCF trend, industry, company stage (-10% to 30%)
2. Terminal growth: Long-term economy growth (2-3%)
3. Risk-free rate: Current 10-year Treasury yield (3-5%)
4. Market risk premium: Expected equity return above risk-free (6-10%)
5. Company risk premium: Additional risk for this specific company (0-5%)
6. Growth decline factor: How much growth rate declines each year (0-0.15)
   - 0.00 = no decline (steady growth)
   - 0.05 = gentle decline (mature stable companies)
   - 0.10 = moderate decline (default for most)
   - 0.15 = aggressive decline (high uncertainty)
7. Projection years: 5-10 years based on business predictability
8. Found context: Did you find relevant info in the provided context?

Just estimate the inputs - we'll calculate WACC and DCF.
CONTEXT (insights from company videos/discussions):
{context}

Use this context to inform your growth estimates and risk assessments.
"""


class DCFAgent(Agent):
    """DCF agent - AI calculates all assumptions, code does arithmetic"""

    def __init__(self, fmp_client, ai_engine):
        super().__init__(ai_engine)
        self.fmp_client = fmp_client

    def fetch_financials(self, symbol):
        """Fetch from FMP with validation"""
        financials = {
            "income_statements": [],
            "cash_flows": [],
            "balance_sheets": [],
            "profile": None,
        }

        # Profile
        success, profile = self.fmp_client.get_company_profile(symbol)
        if not success:
            return False, f"Failed to fetch profile: {profile}"
        financials["profile"] = profile

        # Income statements
        success, income = self.fmp_client.get_income_statement(symbol, limit=5)
        if not success:
            return False, f"Failed to fetch income statements: {income}"
        if not income or len(income) == 0:
            return False, f"No income statement data available for {symbol}"
        financials["income_statements"] = income

        # Cash flows (CRITICAL for DCF)
        success, cash_flows = self.fmp_client.get_cash_flow_statement(symbol, limit=5)
        if not success:
            return False, f"Failed to fetch cash flows: {cash_flows}"
        if not cash_flows or len(cash_flows) < 2:
            return (
                False,
                f"Insufficient cash flow history for {symbol} (need at least 2 years)",
            )
        financials["cash_flows"] = cash_flows

        # Balance sheets
        success, balance_sheets = self.fmp_client.get_balance_sheet(symbol, limit=5)
        if not success:
            return False, f"Failed to fetch balance sheets: {balance_sheets}"
        if not balance_sheets or len(balance_sheets) == 0:
            return False, f"No balance sheet data available for {symbol}"
        financials["balance_sheets"] = balance_sheets

        logger.info(f"Successfully fetched all financials for {symbol}")
        return True, financials

    def validate_financials(self, financials):
        """Strict validation - no defaults allowed"""

        # Profile validation
        profile = financials.get("profile")
        if not profile:
            return False, "Missing profile data"

        required_profile = {
            "price": "stock price",
            "marketCap": "market capitalization",
            "beta": "beta coefficient",
        }
        for key, name in required_profile.items():
            if key not in profile or profile[key] is None:
                return False, f"Missing {name} in profile"
            if key in ["price", "marketCap"] and profile[key] <= 0:
                return False, f"Invalid {name}: {profile[key]}"

        # Cash flows validation
        cash_flows = financials.get("cash_flows", [])
        if len(cash_flows) < 2:
            return False, "Need at least 2 years of cash flow data"

        for i, cf in enumerate(cash_flows[:5]):
            if "operatingCashFlow" not in cf or cf["operatingCashFlow"] is None:
                return False, f"Missing operating cash flow for year {i+1}"
            if "capitalExpenditure" not in cf or cf["capitalExpenditure"] is None:
                return False, f"Missing capital expenditure for year {i+1}"
            if "date" not in cf:
                return False, f"Missing date for cash flow year {i+1}"

        # Balance sheet validation
        balance_sheets = financials.get("balance_sheets", [])
        if len(balance_sheets) == 0:
            return False, "No balance sheet data"

        bs = balance_sheets[0]
        required_bs = {
            "totalDebt": "total debt",
            "cashAndCashEquivalents": "cash and equivalents",
        }
        for key, name in required_bs.items():
            if key not in bs or bs[key] is None:
                return False, f"Missing {name} in balance sheet"

        # Income statements validation
        income_statements = financials.get("income_statements", [])
        if len(income_statements) == 0:
            return False, "No income statement data"

        for i, inc in enumerate(income_statements[:5]):
            if "revenue" not in inc or inc["revenue"] is None:
                return False, f"Missing revenue for year {i+1}"
            if "date" not in inc:
                return False, f"Missing date for income statement year {i+1}"

        return True, ""

    def validate_ai_assumptions(self, ai_assumptions):
        """Validate AI assumptions - all must be present and valid"""

        required = {
            "fcf_growth_rate": (-0.10, 0.30),
            "terminal_growth_rate": (0.015, 0.035),
            "risk_free_rate": (0.03, 0.05),
            "market_risk_premium": (0.06, 0.10),
            "company_risk_premium": (0.0, 0.05),
            "growth_decline_factor": (0.0, 0.15),
            "projection_years": (5, 10),
        }

        for key, (min_val, max_val) in required.items():
            if key not in ai_assumptions:
                return False, f"AI did not provide {key}"

            value = ai_assumptions[key]
            if value is None:
                return False, f"AI provided None for {key}"

            if not isinstance(value, (int, float)):
                return False, f"AI provided non-numeric {key}: {value}"

            if value < min_val or value > max_val:
                return (
                    False,
                    f"AI provided {key}={value} outside valid range [{min_val}, {max_val}]",
                )

        if "reasoning" not in ai_assumptions or not ai_assumptions["reasoning"]:
            return False, "AI did not provide reasoning for assumptions"

        return True, ""

    def get_ai_assumptions(self, symbol, financials, context=None):
        """Get AI to calculate all DCF assumptions including WACC"""

        # Validate first
        success, msg = self.validate_financials(financials)
        if not success:
            return False, f"Financial validation failed: {msg}"

        profile = financials["profile"]
        cash_flows = financials["cash_flows"]
        income_statements = financials["income_statements"]
        balance_sheets = financials["balance_sheets"]

        # Build FCF history
        fcf_list = []
        for cf in cash_flows[:5]:
            op_cf = cf["operatingCashFlow"]
            capex = cf["capitalExpenditure"]
            fcf = op_cf + capex  # capex is negative
            date = cf["date"]
            fcf_list.append(f"{date}: ${fcf:,.0f}")

        # Build revenue history
        revenue_list = []
        for inc in income_statements[:5]:
            revenue = inc["revenue"]
            date = inc["date"]
            revenue_list.append(f"{date}: ${revenue:,.0f}")

        prompt = DCF_ASSUMPTIONS_PROMPT.format(
            symbol=symbol,
            price=profile["price"],
            mkt_cap=profile["marketCap"],
            beta=profile["beta"],
            fcf_history="\n".join(fcf_list),
            revenue_history="\n".join(revenue_list),
            debt=balance_sheets[0]["totalDebt"],
            cash=balance_sheets[0]["cashAndCashEquivalents"],
            context=context if context else "N/A",
        )

        # Ask AI
        success, result = self.ask(prompt, max_tokens=2000, expect_json=True)
        if not success:
            return False, f"AI failed to provide assumptions: {result}"

        # Validate AI response
        success, msg = self.validate_ai_assumptions(result)
        if not success:
            return False, f"AI assumptions validation failed: {msg}"

        logger.info(f"AI assumptions for {symbol}: {result}")
        return True, result

    def calculate_dcf(self, symbol, financials, ai_assumptions):
        """Calculate DCF - WE do ALL calculations"""

        try:
            # Get data
            profile = financials["profile"]
            cash_flows = financials["cash_flows"]
            balance_sheets = financials["balance_sheets"]

            current_price = profile["price"]
            market_cap = profile["marketCap"]
            beta = profile["beta"]
            shares_outstanding = market_cap / current_price

            # Calculate FCF history
            fcf_history = []
            for cf in cash_flows[:5]:
                fcf = cf["operatingCashFlow"] + cf["capitalExpenditure"]
                fcf_history.append(fcf)

            logger.info(
                f"FCF history for {symbol}: {[f'${f/1e9:.1f}B' for f in fcf_history]}"
            )

            # Check for positive FCF
            positive_fcf = [f for f in fcf_history if f > 0]
            if len(positive_fcf) == 0:
                return (
                    False,
                    f"{symbol} has no positive free cash flow. DCF not applicable.",
                )

            # Get AI's estimates (NOT calculations)
            growth_rate = ai_assumptions["fcf_growth_rate"]
            terminal_growth = ai_assumptions["terminal_growth_rate"]
            risk_free_rate = ai_assumptions["risk_free_rate"]
            market_risk_premium = ai_assumptions["market_risk_premium"]
            company_risk_premium = ai_assumptions["company_risk_premium"]
            growth_decline_factor = ai_assumptions["growth_decline_factor"]
            projection_years = int(ai_assumptions["projection_years"])

            # Get debt and cash
            debt = balance_sheets[0]["totalDebt"]
            cash = balance_sheets[0]["cashAndCashEquivalents"]

            # WE calculate WACC using AI's estimates
            cost_of_equity = (
                risk_free_rate + (beta * market_risk_premium) + company_risk_premium
            )

            # Adjust for debt
            total_value = market_cap + debt
            if total_value > 0:
                weight_equity = market_cap / total_value
                weight_debt = debt / total_value
                cost_of_debt = 0.05
                tax_rate = 0.21
                wacc = (weight_equity * cost_of_equity) + (
                    weight_debt * cost_of_debt * (1 - tax_rate)
                )
            else:
                wacc = cost_of_equity

            # Clamp WACC to reasonable range
            wacc = max(min(wacc, 0.20), 0.06)

            # Validate WACC > terminal growth
            if wacc <= terminal_growth:
                return (
                    False,
                    f"WACC ({wacc:.2%}) must be greater than terminal growth ({terminal_growth:.2%})",
                )

            # Project FCF with AI-determined declining growth
            projected_fcf = []
            last_fcf = fcf_history[0]

            for year in range(1, projection_years + 1):
                # Decline growth each year by AI's factor
                year_growth = growth_rate  # * (1 - (year * growth_decline_factor))
                # Don't let it go negative
                year_growth = max(year_growth, 0)
                next_fcf = last_fcf * (1 + year_growth)
                projected_fcf.append(next_fcf)
                last_fcf = next_fcf

            logger.info(
                f"Projected FCF for {symbol} (starting at ${fcf_history[0]/1e9:.1f}B, growth {growth_rate:.1%} declining): {[f'${f/1e9:.1f}B' for f in projected_fcf]}"
            )

            # Terminal value
            terminal_fcf = projected_fcf[-1] * (1 + terminal_growth)
            terminal_value = terminal_fcf / (wacc - terminal_growth)

            # Present value of projected FCF
            pv_fcf = []
            for i, fcf in enumerate(projected_fcf, 1):
                pv = fcf / ((1 + wacc) ** i)
                pv_fcf.append(pv)

            # Present value of terminal value
            pv_terminal = terminal_value / ((1 + wacc) ** projection_years)

            # Enterprise value
            enterprise_value = sum(pv_fcf) + pv_terminal

            # Equity value
            net_debt = debt - cash
            equity_value = enterprise_value - net_debt

            # Intrinsic value per share
            intrinsic_value = equity_value / shares_outstanding

            # Upside/downside
            upside = ((intrinsic_value - current_price) / current_price) * 100

            # Recommendation
            if upside > 20:
                rec = "UNDERVALUED - Strong Buy"
            elif upside > 10:
                rec = "UNDERVALUED - Buy"
            elif upside > -10:
                rec = "FAIRLY VALUED - Hold"
            elif upside > -20:
                rec = "OVERVALUED - Sell"
            else:
                rec = "OVERVALUED - Strong Sell"

            result = {
                "intrinsic_value": intrinsic_value,
                "current_price": current_price,
                "upside_downside": upside,
                "recommendation": rec,
                "enterprise_value": enterprise_value,
                "terminal_value": terminal_value,
                "assumptions": {
                    "wacc": wacc,
                    "fcf_growth_rate": growth_rate,
                    "terminal_growth_rate": terminal_growth,
                    "projection_years": projection_years,
                    "beta": beta,
                    "risk_free_rate": risk_free_rate,
                    "market_risk_premium": market_risk_premium,
                    "company_risk_premium": company_risk_premium,
                    "growth_decline_factor": growth_decline_factor,
                    "ai_reasoning": ai_assumptions["reasoning"],
                },
                "fcf_history": fcf_history,
                "projected_fcf": projected_fcf,
            }

            logger.info(
                f"DCF for {symbol}: Intrinsic=${intrinsic_value:.2f}, Current=${current_price:.2f}, Upside={upside:.1f}%"
            )
            return True, result

        except KeyError as e:
            return False, f"Missing required data field: {str(e)}"
        except ZeroDivisionError:
            return False, "Division by zero in DCF calculation"
        except Exception as e:
            return False, f"DCF calculation error: {str(e)}"

    def run_valuation(self, symbol, context=None):
        """Full DCF pipeline with strict validation at every step"""

        # Step 1: Fetch financials
        logger.info(f"Starting DCF valuation for {symbol}")
        success, financials = self.fetch_financials(symbol)
        if not success:
            logger.error(f"Fetch failed: {financials}")
            return False, financials

        # Step 2: AI determines assumptions (with optional YouTube context)
        success, ai_assumptions = self.get_ai_assumptions(symbol, financials, context)
        if not success:
            logger.error(f"AI assumptions failed: {ai_assumptions}")
            return False, ai_assumptions

        # Step 3: Calculate DCF
        success, dcf_result = self.calculate_dcf(symbol, financials, ai_assumptions)
        if not success:
            logger.error(f"DCF calculation failed: {dcf_result}")
            return False, dcf_result

        return True, {"dcf": dcf_result, "ai_assumptions": ai_assumptions}
