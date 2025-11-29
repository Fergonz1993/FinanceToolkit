# Simple Wrapper Layer for FinanceToolkit

This wrapper layer provides a simplified, high-level API on top of FinanceToolkit, making it easier to perform common financial analysis tasks without needing to understand all the internals of the FinanceToolkit library.

## Setup

### 1. Install Dependencies

```bash
pip install python-dotenv
```

The FinanceToolkit itself should already be installed (it's part of this codebase).

### 2. Configure API Key

Create a `.env` file in the project root with your Financial Modeling Prep API key:

```env
FMP_API_KEY=your_api_key_here
```

Get your free API key at: https://www.jeroenbouma.com/fmp

### 3. Optional Configuration

You can also set default values in your `.env` file:

```env
DEFAULT_BENCHMARK=SPY
DEFAULT_START_DATE=2018-01-01
DEFAULT_RISK_FREE_RATE=10y
```

## Quick Start

### Company Analysis

```python
from my_finance_layer import analyze_company

# Analyze one or more companies
result = analyze_company(
    tickers=["AAPL", "MSFT"],
    start_date="2018-01-01"
)

# Access the results
income_statement = result["statements"]["income"]
profitability_ratios = result["ratios"]["profitability"]
dupont_analysis = result["models"]["extended_dupont"]
historical_data = result["historical"]
```

### Portfolio Analysis

```python
from my_finance_layer import analyze_portfolio

# Analyze your portfolio
result = analyze_portfolio(
    positions_path="portfolio.xlsx",
    benchmark="SPY"
)

# Access the results
overview = result["overview"]
performance = result["performance"]["returns"]
risk_metrics = result["risk"]["var"]
```

### Macro Economic Data

```python
from my_finance_layer import get_macro_snapshot

# Get macroeconomic indicators
result = get_macro_snapshot(
    countries=["United States", "Germany"],
    metrics=("gdp", "unemployment", "cpi"),
    start_year=2015,
    end_year=2024
)

# Access the data
gdp_data = result["gdp"]
unemployment = result["unemployment"]
cpi = result["cpi"]
```

## API Reference

### `analyze_company(tickers, start_date=None, end_date=None, quarterly=False, include_models=True, include_ratios=True, include_historical=True)`

Performs comprehensive company analysis.

**Parameters:**
- `tickers` (list[str] | str): List of ticker symbols or a single ticker string
- `start_date` (str | None): Start date in YYYY-MM-DD format. Defaults to config or 5 years ago
- `end_date` (str | None): End date in YYYY-MM-DD format. Defaults to today
- `quarterly` (bool): Whether to use quarterly data. Defaults to False
- `include_models` (bool): Whether to include financial models. Defaults to True
- `include_ratios` (bool): Whether to include financial ratios. Defaults to True
- `include_historical` (bool): Whether to include historical price data. Defaults to True

**Returns:**
- `dict`: Dictionary containing:
  - `"statements"`: dict with "income", "balance", "cashflow" DataFrames
  - `"ratios"`: dict with ratio categories (profitability, liquidity, solvency, efficiency, valuation)
  - `"models"`: dict with model results (dupont, extended_dupont, wacc, enterprise_value)
  - `"historical"`: DataFrame with historical price data
  - `"toolkit"`: The Toolkit instance (for advanced usage)

### `analyze_portfolio(positions_path, benchmark=None, start_date=None, quarterly=False)`

Analyzes a portfolio from a CSV or Excel file.

**Parameters:**
- `positions_path` (str): Path to portfolio CSV or Excel file
- `benchmark` (str | None): Benchmark ticker for comparison. Defaults to config or "SPY"
- `start_date` (str | None): Start date for analysis. Defaults to config or earliest available
- `quarterly` (bool): Whether to use quarterly data. Defaults to False

**Returns:**
- `dict`: Dictionary containing:
  - `"overview"`: DataFrame with portfolio overview
  - `"performance"`: dict with "returns" and "correlations" DataFrames
  - `"risk"`: dict with "var" and "cvar" DataFrames
  - `"portfolio"`: The Portfolio instance (for advanced usage)

### `get_macro_snapshot(countries, metrics=None, start_year=None, end_year=None)`

Retrieves macroeconomic indicators for specified countries.

**Parameters:**
- `countries` (list[str] | str): List of country names or a single country string
- `metrics` (tuple[str, ...] | None): Tuple of metrics to retrieve. Options: "gdp", "unemployment", "cpi", "inflation". Defaults to ("gdp", "unemployment", "cpi")
- `start_year` (int | None): Start year for data retrieval. Defaults to 10 years ago
- `end_year` (int | None): End year for data retrieval. Defaults to current year

**Returns:**
- `dict`: Dictionary with metric names as keys and DataFrames as values. Each DataFrame has countries as columns and dates as index.

### `get_toolkit(tickers=None, start_date=None, end_date=None, quarterly=False, **kwargs)`

Get or create a Toolkit instance with sensible defaults. This function caches Toolkit instances, so repeated calls with the same parameters in a notebook session will reuse the same instance.

**Parameters:**
- `tickers` (list[str] | str | None): List of ticker symbols or a single ticker string
- `start_date` (str | None): Start date in YYYY-MM-DD format. Defaults to config or 5 years ago
- `end_date` (str | None): End date in YYYY-MM-DD format. Defaults to today
- `quarterly` (bool): Whether to use quarterly data. Defaults to False
- `**kwargs`: Additional arguments to pass to Toolkit initialization

**Returns:**
- `Toolkit`: Configured Toolkit instance

## Examples

See the Jupyter notebooks in this directory:
- `01_company_analysis.ipynb` - Company analysis examples
- `02_portfolio_analysis.ipynb` - Portfolio analysis examples
- `03_macro_snapshot.ipynb` - Macro economic data examples

## Advanced Usage

If you need access to the full FinanceToolkit API, you can access the underlying objects:

```python
from my_finance_layer import analyze_company

result = analyze_company(["AAPL"])

# Access the Toolkit instance for advanced operations
toolkit = result["toolkit"]

# Now you can use any FinanceToolkit method
options_data = toolkit.options.collect_all_greeks()
risk_metrics = toolkit.risk.get_value_at_risk()
technical_indicators = toolkit.technicals.get_relative_strength_index()
```

## Notes

- The wrapper layer caches Toolkit instances based on their parameters, so repeated calls in the same session are efficient
- All functions handle errors gracefully and return empty DataFrames if data is unavailable
- The wrapper maintains the same data structures as FinanceToolkit, so you can use all the same pandas operations
- If FinanceToolkit internals change, only the wrapper needs to be updated - your code using the wrapper API remains stable

