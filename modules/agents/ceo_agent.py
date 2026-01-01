"""CEO analysis agent - fetch and analyze CEO information"""

import modules.logger as logger
from modules.agents.base_agent import Agent


# Prompt defined at top of file
CEO_ANALYSIS_PROMPT = """As an executive recruiter and corporate governance expert, analyze this CEO for {symbol} 
and assess whether they are well-positioned to lead the company to future growth.

CEO INFORMATION:
Name: {name}
Position: {position}
Age: {age}
Year Born: {year_born}
Tenure Start: {since}
Compensation: {compensation} {currency}

Provide your assessment as JSON ONLY (no markdown, no extra text):
{{
    "fit_score": 1-10,
    "fit_level": "EXCELLENT/GOOD/MODERATE/POOR",
    "strengths": ["strength1", "strength2"],
    "concerns": ["concern1", "concern2"],
    "summary": "Brief overall assessment"
}}
"""


class CeoAgent(Agent):
    """Agent for CEO analysis"""

    def __init__(self, fmp_client, ai_engine):
        super().__init__(ai_engine)
        self.fmp_client = fmp_client

    def fetch_ceo_info(self, symbol):
        """
        Fetch CEO information from Financial Modeling Prep

        Returns:
            tuple: (success: bool, data: dict or error_message: str)
        """
        # Get executives from FMP
        success, executives = self.fmp_client.get_key_executives(symbol)

        if not success:
            return False, executives  # executives contains error message

        # Find CEO - actual FMP format
        for exec in executives:
            title = exec.get("title", "").upper()
            if "CEO" in title or "CHIEF EXECUTIVE OFFICER" in title:
                # Calculate age from yearBorn
                year_born = exec.get("yearBorn")
                age = 2024 - year_born if year_born else None

                ceo_data = {
                    "name": exec.get("name"),
                    "position": exec.get("title"),
                    "age": age,
                    "year_born": year_born,
                    "since": exec.get("titleSince"),
                    "compensation": exec.get("pay"),
                    "currency": exec.get("currencyPay", "USD"),
                    "gender": exec.get("gender"),
                    "source": "Financial Modeling Prep",
                }
                logger.info(f"CEO found: {ceo_data['name']}")
                return True, ceo_data

        return False, f"No CEO found in executive data for {symbol}"

    def analyze_ceo_fit(self, symbol, ceo_data):
        """
        Analyze if CEO is a good fit for future growth using AI

        Returns:
            tuple: (success: bool, analysis: dict or error_message: str)
        """
        if not ceo_data:
            return False, "No CEO data provided for analysis"

        # Build prompt from template with actual data
        prompt = CEO_ANALYSIS_PROMPT.format(
            symbol=symbol,
            name=ceo_data.get("name", "N/A"),
            position=ceo_data.get("position", "N/A"),
            age=ceo_data.get("age", "N/A"),
            year_born=ceo_data.get("year_born", "N/A"),
            since=ceo_data.get("since", "N/A"),
            compensation=ceo_data.get("compensation", "N/A"),
            currency=ceo_data.get("currency", ""),
        )

        # Use base Agent.ask() method
        success, result = self.ask(prompt, max_tokens=4000, expect_json=True)

        if success:
            logger.info(f"CEO analysis completed: fit_score={result.get('fit_score')}")

        return success, result

    def run_analysis(self, symbol):
        """
        Coordinator function - fetch CEO info and analyze

        Returns:
            tuple: (success: bool, result: dict or error_message: str)
        """
        # Step 1: Fetch CEO info
        success, ceo_data = self.fetch_ceo_info(symbol)
        if not success:
            return False, ceo_data  # ceo_data contains error message

        # Step 2: Analyze CEO fit
        success, analysis = self.analyze_ceo_fit(symbol, ceo_data)
        if not success:
            return False, analysis  # analysis contains error message

        # Combine data and analysis
        result = {"ceo_info": ceo_data, "analysis": analysis}

        return True, result
