import unit_test as u

from modules import key as keys
from modules.fetchers.fmp_fetcher import FinancialModelingPrep
from modules.agents.ceo_agent import CeoAgent
from modules.agents.dcf_agent import DCFAgent
from modules.agents.youtube_agent import YouTubeAgent


@u.unit_test("Test FMP CEO Fetch")
def test_fmp_ceo_fetch():
    """Test fetching CEO info from Financial Modeling Prep"""

    # Get FMP key
    fmp_key = keys.FinancialModelingPrepKey()
    fmp_client = FinancialModelingPrep(key=fmp_key)
    ceo_agent = CeoAgent(fmp_client, None)

    # Create FMP client

    # Test with well-known stocks
    symbol = "AAPL"  # Apple Inc.
    success, ceo_data = ceo_agent.fetch_ceo_info(symbol)

    if success:
        # Find CEO
        print(f"CEO Name: {ceo_data.get('name')}")
        print(f"Position: {ceo_data.get('title')}")
        print(f"Compensation: {ceo_data.get('pay')}")
    else:
        print(f"No CEO found in {len(ceo_data)} executives")

    return success


@u.unit_test("Test DCF Fetch Financials")
def test_dcf_fetch():
    """Test DCF agent's fetch_financials method"""

    # Initialize FMP client
    fmp_key = keys.FinancialModelingPrepKey()

    if not fmp_key.exists():
        print("❌ FMP API key not configured")
        print("Set FMP_API_KEY in your .env file")
        return

    # Create FMP client and DCF agent
    fmp_client = FinancialModelingPrep(key=fmp_key)
    dcf_agent = DCFAgent(fmp_client=fmp_client, ai_engine=None)

    test_symbol = "AAPL"

    print(f"Testing fetch_financials for {test_symbol}...")
    print("-" * 60)

    # Call the agent's fetch method
    success, result = dcf_agent.fetch_financials(test_symbol)

    if not success:
        print(f"\n❌ Failed: {result}")
        return False

    print(f"\n Success! Fetched financial data\n")

    # Display what we got
    financials = result

    # Profile
    print("1. Company Profile")
    print("-" * 40)
    if financials.get("profile"):
        profile = financials["profile"]
        print(f"  Company: {profile.get('companyName')}")
        print(f"  Price: ${profile.get('price')}")
        print(f"  Market Cap: ${profile.get('marketCap'):,.0f}")
        print(f"  Beta: {profile.get('beta')}")
    else:
        print("  ❌ No profile data")

    # Cash Flows
    print("\n2. Cash Flow Statements")
    print("-" * 40)
    cash_flows = financials.get("cash_flows", [])
    if cash_flows:
        print(f"  Found {len(cash_flows)} statements")
        for i, cf in enumerate(cash_flows[:3], 1):
            operating_cf = cf.get("operatingCashFlow")
            capex = cf.get("capitalExpenditure")
            fcf = operating_cf + capex
            print(f"\n  Year {i} ({cf.get('date', 'N/A')}):")
            print(f"    Operating CF: ${operating_cf:,.0f}")
            print(f"    CapEx: ${capex:,.0f}")
            print(f"    Free Cash Flow: ${fcf:,.0f}")
    else:
        print("  ❌ No cash flow data")

    # Balance Sheets
    print("\n3. Balance Sheets")
    print("-" * 40)
    balance_sheets = financials.get("balance_sheets", [])
    if balance_sheets:
        print(f"  Found {len(balance_sheets)} statements")
        bs = balance_sheets[0]
        print(f"\n  Latest ({bs.get('date')}):")
        print(f"    Total Debt: ${bs.get('totalDebt', 0):,.0f}")
        print(f"    Cash: ${bs.get('cashAndCashEquivalents', 0):,.0f}")
    else:
        print("  ❌ No balance sheet data")

    # Income Statements
    print("\n4. Income Statements")
    print("-" * 40)
    income_statements = financials.get("income_statements", [])
    if income_statements:
        print(f"  Found {len(income_statements)} statements")
        inc = income_statements[0]
        print(f"\n  Latest ({inc.get('date')}):")
        print(f"    Revenue: ${inc.get('revenue', 0):,.0f}")
    else:
        print("  ⚠️  No income statement data (optional)")

    return True


if __name__ == "__main__":
    test_fmp_ceo_fetch()
    test_dcf_fetch()
