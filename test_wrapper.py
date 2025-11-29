"""Simple tests for the wrapper layer.

These tests ensure the wrapper API remains stable as FinanceToolkit evolves.
Run with: pytest test_wrapper.py
"""

import os
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Mock the API key requirement for testing
os.environ["FMP_API_KEY"] = "test_key"


def test_get_toolkit_creates_instance():
    """Test that get_toolkit creates a Toolkit instance."""
    from my_finance_layer import get_toolkit
    
    with patch("my_finance_layer.Toolkit") as mock_toolkit:
        mock_instance = MagicMock()
        mock_toolkit.return_value = mock_instance
        
        result = get_toolkit(tickers=["AAPL"], start_date="2020-01-01")
        
        assert result == mock_instance
        mock_toolkit.assert_called_once()


def test_analyze_company_structure():
    """Test that analyze_company returns the expected structure."""
    from my_finance_layer import analyze_company
    
    with patch("my_finance_layer.get_toolkit") as mock_get_toolkit:
        # Create a mock toolkit
        mock_toolkit = MagicMock()
        mock_toolkit.get_income_statement.return_value = pd.DataFrame({"Revenue": [100]})
        mock_toolkit.get_balance_sheet_statement.return_value = pd.DataFrame({"Assets": [200]})
        mock_toolkit.get_cash_flow_statement.return_value = pd.DataFrame({"Cash": [50]})
        mock_toolkit.get_historical_data.return_value = pd.DataFrame({"Close": [150]})
        
        # Mock ratio collections
        mock_toolkit.ratios.collect_profitability_ratios.return_value = pd.DataFrame({"ROE": [0.15]})
        mock_toolkit.ratios.collect_liquidity_ratios.return_value = pd.DataFrame({"Current Ratio": [2.0]})
        mock_toolkit.ratios.collect_solvency_ratios.return_value = pd.DataFrame({"Debt/Equity": [0.5]})
        mock_toolkit.ratios.collect_efficiency_ratios.return_value = pd.DataFrame({"Asset Turnover": [1.2]})
        mock_toolkit.ratios.collect_valuation_ratios.return_value = pd.DataFrame({"PE": [20]})
        
        # Mock model results
        mock_toolkit.models.get_dupont_analysis.return_value = pd.DataFrame({"ROE": [0.15]})
        mock_toolkit.models.get_extended_dupont_analysis.return_value = pd.DataFrame({"ROE": [0.15]})
        mock_toolkit.models.get_weighted_average_cost_of_capital.return_value = pd.DataFrame({"WACC": [0.08]})
        mock_toolkit.models.get_enterprise_value_breakdown.return_value = pd.DataFrame({"EV": [1000]})
        
        mock_get_toolkit.return_value = mock_toolkit
        
        result = analyze_company(["AAPL"], start_date="2020-01-01")
        
        # Check structure
        assert "statements" in result
        assert "ratios" in result
        assert "models" in result
        assert "historical" in result
        assert "toolkit" in result
        
        # Check statements structure
        assert "income" in result["statements"]
        assert "balance" in result["statements"]
        assert "cashflow" in result["statements"]
        
        # Check ratios structure
        assert "profitability" in result["ratios"]
        assert "liquidity" in result["ratios"]
        assert "solvency" in result["ratios"]
        assert "efficiency" in result["ratios"]
        assert "valuation" in result["ratios"]
        
        # Check models structure
        assert "dupont" in result["models"]
        assert "extended_dupont" in result["models"]
        assert "wacc" in result["models"]
        assert "enterprise_value" in result["models"]


def test_get_macro_snapshot_structure():
    """Test that get_macro_snapshot returns the expected structure."""
    from my_finance_layer import get_macro_snapshot
    
    with patch("my_finance_layer.Economics") as mock_economics_class:
        mock_economics = MagicMock()
        mock_economics.get_gross_domestic_product.return_value = pd.DataFrame({"United States": [100]})
        mock_economics.get_unemployment_rate.return_value = pd.DataFrame({"United States": [3.5]})
        mock_economics.get_consumer_price_index.return_value = pd.DataFrame({"United States": [110]})
        mock_economics_class.return_value = mock_economics
        
        result = get_macro_snapshot(
            countries=["United States"],
            metrics=("gdp", "unemployment", "cpi")
        )
        
        # Check structure
        assert "gdp" in result
        assert "unemployment" in result
        assert "cpi" in result
        
        # Check that DataFrames are returned
        assert isinstance(result["gdp"], pd.DataFrame)
        assert isinstance(result["unemployment"], pd.DataFrame)
        assert isinstance(result["cpi"], pd.DataFrame)


def test_analyze_portfolio_structure():
    """Test that analyze_portfolio returns the expected structure."""
    from my_finance_layer import analyze_portfolio
    
    with patch("my_finance_layer.Portfolio") as mock_portfolio_class:
        mock_portfolio = MagicMock()
        mock_portfolio.get_portfolio_overview.return_value = pd.DataFrame({"Weight": [0.5]})
        mock_portfolio.get_portfolio_performance.return_value = pd.DataFrame({"Return": [0.1]})
        mock_portfolio.get_correlation_matrix.return_value = pd.DataFrame({"AAPL": [1.0]})
        mock_portfolio.get_value_at_risk.return_value = pd.DataFrame({"VaR": [0.02]})
        mock_portfolio.get_conditional_value_at_risk.return_value = pd.DataFrame({"CVaR": [0.03]})
        mock_portfolio_class.return_value = mock_portfolio
        
        result = analyze_portfolio("test_portfolio.xlsx")
        
        # Check structure
        assert "overview" in result
        assert "performance" in result
        assert "risk" in result
        assert "portfolio" in result
        
        # Check performance structure
        assert "returns" in result["performance"]
        assert "correlations" in result["performance"]
        
        # Check risk structure
        assert "var" in result["risk"]
        assert "cvar" in result["risk"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

