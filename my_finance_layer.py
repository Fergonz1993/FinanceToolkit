"""Simple wrapper layer over FinanceToolkit for easier usage.

This module provides high-level functions that simplify common workflows
like company analysis, portfolio analysis, and macro economic data retrieval.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import pandas as pd

from config import (
    get_api_key,
    get_default_benchmark,
    get_default_risk_free_rate,
    get_default_start_date,
)
from financetoolkit import Economics, Portfolio, Toolkit


# Cache Toolkit instances to avoid recreating them in the same session
_toolkit_cache: dict[str, Toolkit] = {}


def get_toolkit(
    tickers: list[str] | str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    quarterly: bool = False,
    **kwargs: Any,
) -> Toolkit:
    """
    Get or create a Toolkit instance with sensible defaults.
    
    This function caches Toolkit instances based on their parameters,
    so repeated calls with the same parameters in a notebook session
    will reuse the same instance.
    
    Args:
        tickers: List of ticker symbols or a single ticker string.
        start_date: Start date in YYYY-MM-DD format. Defaults to config or 5 years ago.
        end_date: End date in YYYY-MM-DD format. Defaults to today.
        quarterly: Whether to use quarterly data. Defaults to False.
        **kwargs: Additional arguments to pass to Toolkit initialization.
        
    Returns:
        Toolkit: Configured Toolkit instance.
    """
    # Use defaults from config if not provided
    if start_date is None:
        start_date = get_default_start_date()
    
    api_key = get_api_key()
    benchmark = get_default_benchmark()
    risk_free_rate = get_default_risk_free_rate()
    
    # Create cache key
    tickers_str = ",".join(sorted(tickers)) if isinstance(tickers, list) else str(tickers)
    cache_key = f"{tickers_str}_{start_date or 'None'}_{end_date or 'None'}_{quarterly}"
    
    # Return cached instance if available
    if cache_key in _toolkit_cache:
        return _toolkit_cache[cache_key]
    
    # Create new Toolkit instance
    toolkit = Toolkit(
        tickers=tickers,
        api_key=api_key,
        start_date=start_date,
        end_date=end_date,
        quarterly=quarterly,
        benchmark_ticker=benchmark,
        risk_free_rate=risk_free_rate,
        reverse_dates=True,
        progress_bar=True,
        **kwargs,
    )
    
    # Cache it
    _toolkit_cache[cache_key] = toolkit
    
    return toolkit


def analyze_company(
    tickers: list[str] | str,
    start_date: str | None = None,
    end_date: str | None = None,
    quarterly: bool = False,
    include_models: bool = True,
    include_ratios: bool = True,
    include_historical: bool = True,
) -> dict[str, Any]:
    """
    Perform comprehensive company analysis.
    
    This function fetches financial statements, ratios, models, and historical data
    for the specified tickers and returns them in a structured dictionary.
    
    Args:
        tickers: List of ticker symbols or a single ticker string.
        start_date: Start date in YYYY-MM-DD format. Defaults to config or 5 years ago.
        end_date: End date in YYYY-MM-DD format. Defaults to today.
        quarterly: Whether to use quarterly data. Defaults to False.
        include_models: Whether to include financial models (DuPont, WACC, etc.). Defaults to True.
        include_ratios: Whether to include financial ratios. Defaults to True.
        include_historical: Whether to include historical price data. Defaults to True.
        
    Returns:
        dict: Dictionary containing:
            - "statements": dict with "income", "balance", "cashflow" DataFrames
            - "ratios": dict with ratio categories (profitability, liquidity, etc.)
            - "models": dict with model results (dupont, wacc, etc.)
            - "historical": DataFrame with historical price data
            - "toolkit": The Toolkit instance used (for advanced usage)
    """
    # Ensure tickers is a list
    if isinstance(tickers, str):
        tickers = [tickers]
    
    # Get Toolkit instance
    toolkit = get_toolkit(
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        quarterly=quarterly,
    )
    
    result: dict[str, Any] = {
        "toolkit": toolkit,
    }
    
    # Fetch financial statements
    result["statements"] = {
        "income": toolkit.get_income_statement(),
        "balance": toolkit.get_balance_sheet_statement(),
        "cashflow": toolkit.get_cash_flow_statement(),
    }
    
    # Fetch ratios if requested
    if include_ratios:
        result["ratios"] = {
            "profitability": toolkit.ratios.collect_profitability_ratios(),
            "liquidity": toolkit.ratios.collect_liquidity_ratios(),
            "solvency": toolkit.ratios.collect_solvency_ratios(),
            "efficiency": toolkit.ratios.collect_efficiency_ratios(),
            "valuation": toolkit.ratios.collect_valuation_ratios(),
        }
    
    # Fetch models if requested
    if include_models:
        result["models"] = {
            "dupont": toolkit.models.get_dupont_analysis(),
            "extended_dupont": toolkit.models.get_extended_dupont_analysis(),
            "wacc": toolkit.models.get_weighted_average_cost_of_capital(),
            "enterprise_value": toolkit.models.get_enterprise_value_breakdown(),
        }
    
    # Fetch historical data if requested
    if include_historical:
        result["historical"] = toolkit.get_historical_data()
    
    return result


def analyze_portfolio(
    positions_path: str,
    benchmark: str | None = None,
    start_date: str | None = None,
    quarterly: bool = False,
) -> dict[str, Any]:
    """
    Analyze a portfolio from a CSV or Excel file.
    
    This function loads portfolio positions and calculates key metrics
    including performance vs benchmark and risk metrics.
    
    Args:
        positions_path: Path to portfolio CSV or Excel file.
        benchmark: Benchmark ticker for comparison. Defaults to config or "SPY".
        start_date: Start date for analysis. Defaults to config or earliest available.
        quarterly: Whether to use quarterly data. Defaults to False.
        
    Returns:
        dict: Dictionary containing:
            - "overview": DataFrame with portfolio overview
            - "performance": DataFrame with performance metrics
            - "risk": DataFrame with risk metrics
            - "portfolio": The Portfolio instance (for advanced usage)
    """
    api_key = get_api_key()
    
    if benchmark is None:
        benchmark = get_default_benchmark()
    
    # Initialize Portfolio
    portfolio = Portfolio(
        portfolio_dataset=positions_path,
        benchmark_ticker=benchmark,
        api_key=api_key,
        quarterly=quarterly,
    )
    
    result: dict[str, Any] = {
        "portfolio": portfolio,
    }
    
    # Get overview
    try:
        result["overview"] = portfolio.get_portfolio_overview()
    except Exception:
        result["overview"] = pd.DataFrame()
    
    # Get performance metrics
    try:
        result["performance"] = {
            "returns": portfolio.get_portfolio_performance(),
            "correlations": portfolio.get_correlation_matrix(),
        }
    except Exception:
        result["performance"] = {"returns": pd.DataFrame(), "correlations": pd.DataFrame()}
    
    # Get risk metrics
    try:
        result["risk"] = {
            "var": portfolio.get_value_at_risk(),
            "cvar": portfolio.get_conditional_value_at_risk(),
        }
    except Exception:
        result["risk"] = {"var": pd.DataFrame(), "cvar": pd.DataFrame()}
    
    return result


def get_macro_snapshot(
    countries: list[str] | str,
    metrics: tuple[str, ...] | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
) -> dict[str, pd.DataFrame]:
    """
    Get macroeconomic indicators for specified countries.
    
    This function retrieves key economic indicators like GDP, unemployment,
    CPI, and inflation rates for the specified countries.
    
    Args:
        countries: List of country names or a single country string.
        metrics: Tuple of metrics to retrieve. Options: "gdp", "unemployment", "cpi", "inflation".
                 Defaults to ("gdp", "unemployment", "cpi").
        start_year: Start year for data retrieval. Defaults to 10 years ago.
        end_year: End year for data retrieval. Defaults to current year.
        
    Returns:
        dict: Dictionary with metric names as keys and DataFrames as values.
              Each DataFrame has countries as columns and dates as index.
    """
    if metrics is None:
        metrics = ("gdp", "unemployment", "cpi")
    
    # Ensure countries is a list
    if isinstance(countries, str):
        countries = [countries]
    
    # Convert years to dates if provided
    start_date = None
    end_date = None
    if start_year:
        start_date = f"{start_year}-01-01"
    if end_year:
        end_date = f"{end_year}-12-31"
    
    # Initialize Economics
    economics = Economics(start_date=start_date, end_date=end_date)
    
    result: dict[str, pd.DataFrame] = {}
    
    # Fetch requested metrics
    if "gdp" in metrics:
        try:
            result["gdp"] = economics.get_gross_domestic_product()
        except Exception:
            result["gdp"] = pd.DataFrame()
    
    if "unemployment" in metrics:
        try:
            result["unemployment"] = economics.get_unemployment_rate()
        except Exception:
            result["unemployment"] = pd.DataFrame()
    
    if "cpi" in metrics:
        try:
            result["cpi"] = economics.get_consumer_price_index()
        except Exception:
            result["cpi"] = pd.DataFrame()
    
    if "inflation" in metrics:
        try:
            result["inflation"] = economics.get_inflation_rate()
        except Exception:
            result["inflation"] = pd.DataFrame()
    
    # Filter to requested countries if data is available
    for metric_name, df in result.items():
        if not df.empty:
            # Try to filter to requested countries
            available_countries = df.columns.tolist()
            requested_countries = [
                c for c in countries if c in available_countries
            ]
            if requested_countries:
                result[metric_name] = df[requested_countries]
    
    return result

