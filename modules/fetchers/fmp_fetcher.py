"""Financial Modeling Prep API wrapper"""

import requests
import modules.logger as logger


class FinancialModelingPrep:
    """
    A class to interact with the Financial Modeling Prep API for financial data.
    """

    def __init__(self, key):
        """
        Initialize the FMP client with the provided API key.
        """
        self.api_key = key.value
        self.base_url = "https://financialmodelingprep.com/stable"

    def _get(self, endpoint, params=None):
        """
        Internal method to make GET requests to the FMP API.

        :param endpoint: API endpoint (without base URL)
        :param params: Additional query parameters
        :return: Tuple of (success: bool, data or error_message)
        """
        if params is None:
            params = {}

        params["apikey"] = self.api_key
        url = f"{self.base_url}/{endpoint}"

        try:
            response = requests.get(url, params=params, timeout=10)

            if response.status_code != 200:
                return (
                    False,
                    f"HTTP {response.status_code}: {response.text} for url {url}",
                )

            data = response.json()
            return True, data

        except requests.exceptions.Timeout:
            return False, "Request timeout"
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def get_key_executives(self, symbol):
        """
        Fetch key executives for a given stock symbol.

        :param symbol: Stock symbol to fetch executives for
        :return: Tuple of (success: bool, executives list or error_message)
        """
        try:
            success, data = self._get(f"key-executives?symbol={symbol}")

            if not success:
                return False, f"Error fetching executives: {data} "

            if not data or len(data) == 0:
                return False, f"No executive data available for {symbol}"

            logger.info(f"Fetched {len(data)} executives for {symbol}")
            return True, data

        except Exception as e:
            return False, f"Error fetching key executives: {str(e)}"

    def get_company_profile(self, symbol):
        """
        Fetch company profile for a given stock symbol.

        :param symbol: Stock symbol to fetch profile for
        :return: Tuple of (success: bool, profile dict or error_message)
        """
        try:
            success, data = self._get(f"profile?symbol={symbol}")

            if not success:
                return False, f"Error fetching profile: {data}"

            if not data or len(data) == 0:
                return False, f"No profile data available for {symbol}"

            return True, data[0]  # Profile returns list with single item

        except Exception as e:
            return False, f"Error fetching company profile: {str(e)}"

    def get_income_statement(self, symbol, limit=5):
        """
        Fetch income statements for a given stock symbol.

        :param symbol: Stock symbol to fetch income statements for
        :param limit: Number of periods to fetch (default 5)
        :return: Tuple of (success: bool, income statements list or error_message)
        """
        try:
            success, data = self._get(
                f"income-statement?symbol={symbol}", {"limit": limit}
            )

            if not success:
                return False, f"Error fetching income statements: {data}"

            if not data or len(data) == 0:
                return False, f"No income statement data available for {symbol}"

            logger.info(f"Fetched {len(data)} income statements for {symbol}")
            return True, data

        except Exception as e:
            return False, f"Error fetching income statements: {str(e)}"

    def get_cash_flow_statement(self, symbol, limit=5):
        """
        Fetch cash flow statements for a given stock symbol.

        :param symbol: Stock symbol to fetch cash flow statements for
        :param limit: Number of periods to fetch (default 5)
        :return: Tuple of (success: bool, cash flow statements list or error_message)
        """
        try:
            success, data = self._get(
                f"cash-flow-statement?symbol={symbol}", {"limit": limit}
            )

            if not success:
                return False, f"Error fetching cash flow statements: {data}"

            if not data or len(data) == 0:
                return False, f"No cash flow data available for {symbol}"

            logger.info(f"Fetched {len(data)} cash flow statements for {symbol}")
            return True, data

        except Exception as e:
            return False, f"Error fetching cash flow statements: {str(e)}"

    def get_balance_sheet(self, symbol, limit=5):
        """
        Fetch balance sheets for a given stock symbol.

        :param symbol: Stock symbol to fetch balance sheets for
        :param limit: Number of periods to fetch (default 5)
        :return: Tuple of (success: bool, balance sheets list or error_message)
        """
        try:
            success, data = self._get(
                f"balance-sheet-statement?symbol={symbol}", {"limit": limit}
            )

            if not success:
                return False, f"Error fetching balance sheets: {data}"

            if not data or len(data) == 0:
                return False, f"No balance sheet data available for {symbol}"

            logger.info(f"Fetched {len(data)} balance sheets for {symbol}")
            return True, data

        except Exception as e:
            return False, f"Error fetching balance sheets: {str(e)}"
