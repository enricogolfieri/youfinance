import unit_test as u

from modules.agents.dcf_agent import DCFAgent


@u.unit_test("Test DCF Formulas with Known Values")
def test_dcf_formulas():
    """Validate DCF formulas with simple round numbers"""

    dcf_agent = DCFAgent(fmp_client=None, ai_engine=None)

    # Simple numbers for easy manual calculation
    mock_financials = {
        "profile": {
            "price": 100.0,
            "marketCap": 1_000_000_000_000,  # $1T / $100 = 10B shares
            "beta": 1.0,
        },
        "cash_flows": [
            {
                "date": "2023",
                "operatingCashFlow": 110_000_000_000,
                "capitalExpenditure": -10_000_000_000,
            },  # FCF = 100B
            {
                "date": "2022",
                "operatingCashFlow": 100_000_000_000,
                "capitalExpenditure": -10_000_000_000,
            },
            {
                "date": "2021",
                "operatingCashFlow": 90_000_000_000,
                "capitalExpenditure": -10_000_000_000,
            },
            {
                "date": "2020",
                "operatingCashFlow": 80_000_000_000,
                "capitalExpenditure": -10_000_000_000,
            },
            {
                "date": "2019",
                "operatingCashFlow": 70_000_000_000,
                "capitalExpenditure": -10_000_000_000,
            },
        ],
        "balance_sheets": [
            {
                "date": "2023",
                "totalDebt": 100_000_000_000,  # $100B debt
                "cashAndCashEquivalents": 50_000_000_000,  # $50B cash, net debt = $50B
            }
        ],
        "income_statements": [
            {"date": "2023", "revenue": 400_000_000_000},
            {"date": "2022", "revenue": 380_000_000_000},
        ],
    }

    mock_ai_assumptions = {
        "fcf_growth_rate": 0.10,
        "terminal_growth_rate": 0.03,
        "risk_free_rate": 0.04,
        "market_risk_premium": 0.06,
        "company_risk_premium": 0.01,
        "projection_years": 5,
        "reasoning": "Test",
    }

    print("=" * 60)
    print("DCF Formula Validation Test")
    print("=" * 60)

    # Expected calculations
    print("\nExpected Calculations:")
    print("-" * 60)

    # 1. FCF
    expected_fcf = 110_000_000_000 - 10_000_000_000
    print(f"1. FCF = Operating CF - CapEx")
    print(f"   = $110B - $10B = ${expected_fcf/1e9:.0f}B")

    # 2. Shares
    expected_shares = 1_000_000_000_000 / 100.0
    print(f"\n2. Shares = Market Cap / Price")
    print(f"   = $1T / $100 = {expected_shares/1e9:.0f}B shares")

    # 3. Cost of Equity (before debt adjustment)
    expected_coe = 0.04 + (1.0 * 0.06) + 0.01
    print(f"\n3. Cost of Equity = Risk-Free + Beta×Premium + Company Risk")
    print(f"   = 4% + (1.0 × 6%) + 1% = {expected_coe:.1%}")

    # 4. Net Debt
    expected_net_debt = 100_000_000_000 - 50_000_000_000
    print(f"\n4. Net Debt = Debt - Cash")
    print(f"   = $100B - $50B = ${expected_net_debt/1e9:.0f}B")

    # Run DCF
    print("\n" + "=" * 60)
    print("Running DCF Calculation...")
    print("=" * 60)

    success, result = dcf_agent.calculate_dcf(
        "TEST", mock_financials, mock_ai_assumptions
    )

    if not success:
        print(f"\n❌ FAILED: {result}")
        return False

    print("\n✓ DCF calculation completed")

    # Validate results
    print("\n" + "=" * 60)
    print("Validating Results:")
    print("=" * 60)

    # Check FCF
    actual_fcf = result["fcf_history"][0]
    if abs(actual_fcf - expected_fcf) > 1000:
        print(f"\n❌ FCF mismatch:")
        print(f"   Expected: ${expected_fcf/1e9:.1f}B")
        print(f"   Actual: ${actual_fcf/1e9:.1f}B")
        return False
    print(f"\n✓ FCF correct: ${actual_fcf/1e9:.0f}B")

    # Check WACC is reasonable (will be adjusted for debt/equity mix)
    wacc = result["assumptions"]["wacc"]
    if not (0.05 < wacc < 0.15):
        print(f"\n❌ WACC {wacc:.2%} outside expected range 5-15%")
        return False
    print(f"✓ WACC in range: {wacc:.2%}")

    # Check intrinsic value is positive
    intrinsic = result["intrinsic_value"]
    if intrinsic <= 0:
        print(f"\n❌ Intrinsic value must be positive, got ${intrinsic:.2f}")
        return False
    print(f"✓ Intrinsic value positive: ${intrinsic:.2f}")

    # Check enterprise value
    ev = result["enterprise_value"]
    if ev <= 0:
        print(f"\n❌ Enterprise value must be positive")
        return False
    print(f"✓ Enterprise value: ${ev/1e9:.0f}B")

    # Check projected FCF growth
    projected = result["projected_fcf"]
    if len(projected) != 5:
        print(f"\n❌ Expected 5 projections, got {len(projected)}")
        return False
    if projected[0] <= actual_fcf:
        print(f"\n❌ First projection should be higher than base FCF")
        return False
    print(f"✓ FCF projections: ${actual_fcf/1e9:.0f}B → ${projected[-1]/1e9:.0f}B")

    # Display full results
    print("\n" + "=" * 60)
    print("Full Results:")
    print("=" * 60)
    print(f"Intrinsic Value: ${result['intrinsic_value']:.2f}")
    print(f"Current Price: ${result['current_price']:.2f}")
    print(f"Upside: {result['upside_downside']:.1f}%")
    print(f"Recommendation: {result['recommendation']}")
    print(f"WACC: {result['assumptions']['wacc']:.2%}")
    print(f"Enterprise Value: ${result['enterprise_value']/1e9:.1f}B")
    print(f"Terminal Value: ${result['terminal_value']/1e9:.1f}B")

    print("\n" + "=" * 60)
    print("✅ All formula validations passed!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    test_dcf_formulas()
