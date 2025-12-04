# Using FinanceToolkit Without an API Key

This guide shows you how to use FinanceToolkit with sample data - no API key required.

## Why Use Sample Data?

- **Learn first, pay later** - Understand how the toolkit works before signing up for API access
- **Offline development** - Work without internet connection
- **Testing** - Validate your code with consistent, reproducible data

## Quick Start: Loading Sample Data

The toolkit includes test datasets in `tests/datasets/`. Here's how to use them:

```python
import pickle
import pandas as pd
from financetoolkit import Toolkit

# Step 1: Load the sample data files
with open('tests/datasets/historical_dataset.pickle', 'rb') as f:
    historical_data = pickle.load(f)

with open('tests/datasets/balance_dataset.pickle', 'rb') as f:
    balance_sheet = pickle.load(f)

with open('tests/datasets/income_dataset.pickle', 'rb') as f:
    income_statement = pickle.load(f)

with open('tests/datasets/cash_dataset.pickle', 'rb') as f:
    cash_flow = pickle.load(f)

# Step 2: Create Toolkit with your own data (no API key needed!)
toolkit = Toolkit(
    tickers=['AAPL', 'MSFT'],  # These should match tickers in your data
    historical=historical_data,
    balance=balance_sheet,
    income=income_statement,
    cash=cash_flow,
)

# Step 3: Use the toolkit normally
profitability = toolkit.ratios.collect_profitability_ratios()
print(profitability)
```

## Available Sample Data Files

| File | What It Contains | Use For |
|------|------------------|---------|
| `historical_dataset.pickle` | Stock prices (Open, High, Low, Close, Volume) | Returns, risk metrics, technical analysis |
| `balance_dataset.pickle` | Balance sheets (Assets, Liabilities, Equity) | Solvency ratios, liquidity ratios |
| `income_dataset.pickle` | Income statements (Revenue, Expenses, Profit) | Profitability ratios, margins |
| `cash_dataset.pickle` | Cash flow statements | Cash-based metrics, quality ratios |
| `risk_free_rate.pickle` | Treasury rates | Risk calculations, CAPM |
| `treasury_data.pickle` | Bond/treasury data | Fixed income analysis |
| `portfolio_historical_dataset.pickle` | Portfolio price data | Portfolio analysis |
| `portfolio_benchmark_dataset.pickle` | Benchmark comparison data | Performance vs benchmark |

## Understanding the Data Format

### Historical Data Structure
```python
# Historical data is a DataFrame with MultiIndex columns:
#
# Level 0: Ticker (e.g., 'AAPL', 'MSFT')
# Level 1: Price type (Open, High, Low, Close, Adj Close, Volume)
#
# Index: Dates

# Example structure:
#                  AAPL                              MSFT
#                  Open    High     Low   Close     Open    High ...
# 2020-01-02     74.06   75.15   73.80   75.09   158.78  159.95 ...
# 2020-01-03     74.29   75.14   74.12   74.36   158.32  159.95 ...
```

### Financial Statement Structure
```python
# Balance/Income/Cash statements are DataFrames with:
#
# Columns: Dates (years or quarters like '2020', '2021', '2022')
# Index: MultiIndex with (Ticker, Line Item)
#
# Example structure:
#                              2020         2021         2022
# (AAPL, Total Assets)     323,888M     351,002M     352,755M
# (AAPL, Total Liabilities) 258,549M     287,912M     302,083M
# (MSFT, Total Assets)     301,311M     333,779M     364,840M
```

## Creating Your Own Sample Data

If you want to use your own companies:

```python
import pandas as pd

# Create simple historical data
dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
historical = pd.DataFrame({
    ('MYCO', 'Open'): [100 + i*0.1 for i in range(len(dates))],
    ('MYCO', 'High'): [101 + i*0.1 for i in range(len(dates))],
    ('MYCO', 'Low'): [99 + i*0.1 for i in range(len(dates))],
    ('MYCO', 'Close'): [100.5 + i*0.1 for i in range(len(dates))],
    ('MYCO', 'Volume'): [1000000] * len(dates),
}, index=dates)
historical.columns = pd.MultiIndex.from_tuples(historical.columns)

# Create simple balance sheet
balance = pd.DataFrame({
    '2020': [1000000, 500000, 500000],
    '2021': [1200000, 600000, 600000],
    '2022': [1400000, 700000, 700000],
}, index=pd.MultiIndex.from_tuples([
    ('MYCO', 'Total Assets'),
    ('MYCO', 'Total Liabilities'),
    ('MYCO', 'Total Equity'),
]))

# Use with Toolkit
toolkit = Toolkit(
    tickers=['MYCO'],
    historical=historical,
    balance=balance,
)
```

## Using Excel Files (Portfolio Example)

The toolkit also supports Excel files for portfolio data:

```python
from financetoolkit import Portfolio

# Load from the example Excel file
portfolio = Portfolio(
    portfolio_dataset='tests/datasets/portfolio_test.xlsx'
)

# Or use the example datasets in the package
portfolio = Portfolio(
    portfolio_dataset='financetoolkit/portfolio/example_datasets/example_portfolio.xlsx'
)
```

## Inspecting Sample Data

Before using sample data, it helps to understand what's inside:

```python
import pickle

# Load and inspect
with open('tests/datasets/balance_dataset.pickle', 'rb') as f:
    data = pickle.load(f)

# See what tickers are available
print("Tickers:", data.index.get_level_values(0).unique().tolist())

# See what line items are available
print("Line items:", data.index.get_level_values(1).unique().tolist()[:10])

# See what years/periods are available
print("Periods:", data.columns.tolist())

# Preview the data
print(data.head(20))
```

## Next Steps

Once you're comfortable with sample data:

1. **Get an API key** - Sign up at [Financial Modeling Prep](https://www.jeroenbouma.com/fmp) (15% discount link)
2. **Try real data** - Replace sample data with live API data
3. **Learn the metrics** - See `beginners-guide.md` for explanations of what each metric means

## Troubleshooting

### "KeyError: ticker not found"
The tickers you specify in `Toolkit()` must match the tickers in your data files. Check what tickers exist in the pickle files first.

### "Cannot read pickle file"
Make sure you're running Python from the FinanceToolkit directory, or use absolute paths:
```python
import os
project_root = '/path/to/FinanceToolkit'
with open(os.path.join(project_root, 'tests/datasets/balance_dataset.pickle'), 'rb') as f:
    data = pickle.load(f)
```

### "Data has wrong format"
The Toolkit expects specific DataFrame structures. Use `print(data.head())` and `print(data.columns)` to verify your data matches the expected format.
