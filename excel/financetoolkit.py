"""xlwings Excel add-in for FinanceToolkit.

This module provides Excel User Defined Functions (UDFs) that can be called
directly from Excel cells to perform financial analysis.

Setup:
1. Install xlwings: pip install xlwings
2. Run: xlwings addin install
3. Open Excel and enable the xlwings add-in
4. Open financetoolkit.xlsm and enable macros
"""

import sys
from pathlib import Path

import xlwings as xw

# Add parent directory to path to import my_finance_layer
sys.path.insert(0, str(Path(__file__).parent.parent))

from my_finance_layer import analyze_company, get_macro_snapshot, get_toolkit


@xw.func
@xw.arg("ticker", doc="Stock ticker symbol (e.g., 'AAPL')")
@xw.arg("start_date", doc="Start date in YYYY-MM-DD format (optional)")
def FT_INCOME(ticker: str, start_date: str | None = None):
    """
    Get income statement for a ticker.
    
    Returns a 2D array with financial statement data.
    """
    try:
        result = analyze_company(
            tickers=ticker,
            start_date=start_date,
            include_models=False,
            include_ratios=False,
            include_historical=False,
        )
        
        income = result["statements"]["income"]
        if income.empty:
            return [["No data available"]]
        
        # Convert DataFrame to list of lists for Excel
        # Include index as first column
        data = [[income.index.name or "Metric"] + list(income.columns)]
        for idx, row in income.iterrows():
            data.append([str(idx)] + row.tolist())
        
        return data
    except Exception as e:
        return [[f"Error: {str(e)}"]]


@xw.func
@xw.arg("ticker", doc="Stock ticker symbol (e.g., 'AAPL')")
@xw.arg("start_date", doc="Start date in YYYY-MM-DD format (optional)")
def FT_BALANCE(ticker: str, start_date: str | None = None):
    """
    Get balance sheet for a ticker.
    
    Returns a 2D array with balance sheet data.
    """
    try:
        result = analyze_company(
            tickers=ticker,
            start_date=start_date,
            include_models=False,
            include_ratios=False,
            include_historical=False,
        )
        
        balance = result["statements"]["balance"]
        if balance.empty:
            return [["No data available"]]
        
        # Convert DataFrame to list of lists for Excel
        data = [[balance.index.name or "Metric"] + list(balance.columns)]
        for idx, row in balance.iterrows():
            data.append([str(idx)] + row.tolist())
        
        return data
    except Exception as e:
        return [[f"Error: {str(e)}"]]


@xw.func
@xw.arg("ticker", doc="Stock ticker symbol (e.g., 'AAPL')")
@xw.arg("ratio_type", doc="Type of ratio: 'profitability', 'liquidity', 'solvency', 'efficiency', 'valuation'")
@xw.arg("start_date", doc="Start date in YYYY-MM-DD format (optional)")
def FT_RATIOS(ticker: str, ratio_type: str, start_date: str | None = None):
    """
    Get financial ratios for a ticker.
    
    ratio_type options: profitability, liquidity, solvency, efficiency, valuation
    Returns a 2D array with ratio data.
    """
    try:
        result = analyze_company(
            tickers=ticker,
            start_date=start_date,
            include_models=False,
            include_ratios=True,
            include_historical=False,
        )
        
        ratio_type = ratio_type.lower()
        if ratio_type not in result.get("ratios", {}):
            return [[f"Invalid ratio type. Use: profitability, liquidity, solvency, efficiency, valuation"]]
        
        ratios = result["ratios"][ratio_type]
        if ratios.empty:
            return [["No data available"]]
        
        # Convert DataFrame to list of lists for Excel
        data = [[ratios.index.name or "Ratio"] + list(ratios.columns)]
        for idx, row in ratios.iterrows():
            data.append([str(idx)] + row.tolist())
        
        return data
    except Exception as e:
        return [[f"Error: {str(e)}"]]


@xw.func
@xw.arg("ticker", doc="Stock ticker symbol (e.g., 'AAPL')")
@xw.arg("start_date", doc="Start date in YYYY-MM-DD format (optional)")
def FT_WACC(ticker: str, start_date: str | None = None):
    """
    Calculate Weighted Average Cost of Capital (WACC) for a ticker.
    
    Returns a 2D array with WACC breakdown.
    """
    try:
        result = analyze_company(
            tickers=ticker,
            start_date=start_date,
            include_models=True,
            include_ratios=False,
            include_historical=False,
        )
        
        wacc = result["models"]["wacc"]
        if wacc.empty:
            return [["No data available"]]
        
        # Convert DataFrame to list of lists for Excel
        data = [[wacc.index.name or "Metric"] + list(wacc.columns)]
        for idx, row in wacc.iterrows():
            data.append([str(idx)] + row.tolist())
        
        return data
    except Exception as e:
        return [[f"Error: {str(e)}"]]


@xw.func
@xw.arg("country", doc="Country name (e.g., 'United States')")
@xw.arg("metric", doc="Metric: 'gdp', 'unemployment', 'cpi', 'inflation'")
@xw.arg("start_year", doc="Start year (optional)")
def FT_MACRO(country: str, metric: str, start_year: int | None = None):
    """
    Get macroeconomic indicator for a country.
    
    metric options: gdp, unemployment, cpi, inflation
    Returns a 2D array with time series data.
    """
    try:
        result = get_macro_snapshot(
            countries=country,
            metrics=(metric.lower(),),
            start_year=start_year,
        )
        
        if metric.lower() not in result:
            return [[f"Invalid metric. Use: gdp, unemployment, cpi, inflation"]]
        
        df = result[metric.lower()]
        if df.empty:
            return [["No data available"]]
        
        # Convert DataFrame to list of lists for Excel
        data = [[df.index.name or "Date"] + list(df.columns)]
        for idx, row in df.iterrows():
            data.append([str(idx)] + row.tolist())
        
        return data
    except Exception as e:
        return [[f"Error: {str(e)}"]]


@xw.func
@xw.arg("ticker", doc="Stock ticker symbol (e.g., 'AAPL')")
@xw.arg("metric", doc="Specific metric name (e.g., 'Return on Equity')")
@xw.arg("start_date", doc="Start date in YYYY-MM-DD format (optional)")
def FT_RATIO(ticker: str, metric: str, start_date: str | None = None):
    """
    Get a specific financial ratio value for a ticker.
    
    Returns a single value or array if multiple periods.
    """
    try:
        result = analyze_company(
            tickers=ticker,
            start_date=start_date,
            include_models=False,
            include_ratios=True,
            include_historical=False,
        )
        
        # Search across all ratio types
        for ratio_type, ratios_df in result.get("ratios", {}).items():
            if not ratios_df.empty and metric in ratios_df.index:
                values = ratios_df.loc[metric].values
                if len(values) == 1:
                    return float(values[0])
                return values.tolist()
        
        return f"Metric '{metric}' not found"
    except Exception as e:
        return f"Error: {str(e)}"


@xw.func
@xw.arg("ticker", doc="Stock ticker symbol (e.g., 'AAPL')")
@xw.arg("start_date", doc="Start date in YYYY-MM-DD format (optional)")
def FT_DUPONT(ticker: str, start_date: str | None = None):
    """
    Get DuPont analysis for a ticker.
    
    Returns a 2D array with DuPont breakdown.
    """
    try:
        result = analyze_company(
            tickers=ticker,
            start_date=start_date,
            include_models=True,
            include_ratios=False,
            include_historical=False,
        )
        
        dupont = result["models"]["extended_dupont"]
        if dupont.empty:
            return [["No data available"]]
        
        # Convert DataFrame to list of lists for Excel
        data = [[dupont.index.name or "Component"] + list(dupont.columns)]
        for idx, row in dupont.iterrows():
            data.append([str(idx)] + row.tolist())
        
        return data
    except Exception as e:
        return [[f"Error: {str(e)}"]]

