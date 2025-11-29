# Excel Integration with xlwings

This directory contains the xlwings Excel add-in for FinanceToolkit, allowing you to use financial analysis functions directly in Excel.

## Features

- **Direct Excel Functions**: Use formulas like `=FT_INCOME("AAPL")` directly in Excel cells
- **Offline Capable**: Works without internet connection (uses cached data or Yahoo Finance fallback)
- **Mac & Windows**: Works on both platforms
- **Full DataFrame Support**: Returns multi-dimensional arrays that Excel can display

## Available Functions

### Company Analysis

- `=FT_INCOME(ticker, start_date)` - Get income statement
- `=FT_BALANCE(ticker, start_date)` - Get balance sheet
- `=FT_RATIOS(ticker, ratio_type, start_date)` - Get financial ratios
  - ratio_type: "profitability", "liquidity", "solvency", "efficiency", "valuation"
- `=FT_RATIO(ticker, metric, start_date)` - Get specific ratio value
- `=FT_WACC(ticker, start_date)` - Calculate WACC
- `=FT_DUPONT(ticker, start_date)` - DuPont analysis

### Macro Economic Data

- `=FT_MACRO(country, metric, start_year)` - Get macroeconomic indicators
  - metric: "gdp", "unemployment", "cpi", "inflation"

## Setup Instructions

### 1. Install xlwings

```bash
pip install xlwings
```

### 2. Install the xlwings Excel Add-in

```bash
xlwings addin install
```

This will:
- Install the xlwings add-in to Excel
- Configure Excel to connect to Python

### 3. Configure Python Path

The add-in needs to know where your `financetoolkit.py` file is located.

**Option A: Copy to xlwings UDF modules directory**

```bash
# Find xlwings UDF directory
python -c "import xlwings as xw; print(xw.udfs.__path__[0])"

# Copy financetoolkit.py there
cp excel/financetoolkit.py <path_from_above>
```

**Option B: Add to PYTHONPATH**

Add the FinanceToolkit project root to your PYTHONPATH environment variable.

### 4. Set Up Environment Variables

Make sure your `.env` file is in the project root with your FMP API key:

```env
FMP_API_KEY=your_api_key_here
```

### 5. Open Excel and Enable Macros

1. Open Excel
2. Go to File > Options > Trust Center > Trust Center Settings > Macro Settings
3. Enable "Enable all macros" or "Enable macros with notification"
4. The xlwings add-in should appear in the ribbon

### 6. Test the Functions

In an Excel cell, try:

```
=FT_INCOME("AAPL")
```

This should return a 2D array with the income statement data.

## Usage Examples

### Get Income Statement

```
=FT_INCOME("AAPL", "2020-01-01")
```

### Get Profitability Ratios

```
=FT_RATIOS("AAPL", "profitability")
```

### Get Specific Ratio

```
=FT_RATIO("AAPL", "Return on Equity")
```

### Get WACC

```
=FT_WACC("AAPL")
```

### Get Macro Data

```
=FT_MACRO("United States", "gdp", 2020)
```

## Troubleshooting

### Functions Not Appearing

1. Make sure xlwings add-in is installed: `xlwings addin install`
2. Check that macros are enabled in Excel
3. Verify Python path is correct in xlwings settings

### Import Errors

1. Ensure all dependencies are installed: `pip install -r api/requirements.txt`
2. Check that `my_finance_layer.py` and `config.py` are accessible
3. Verify `.env` file exists with `FMP_API_KEY`

### API Key Errors

1. Check that `.env` file is in the project root
2. Verify `FMP_API_KEY` is set correctly
3. Test API key: `python -c "from config import get_api_key; print(get_api_key())"`

## Advanced Usage

### Array Formulas

Some functions return arrays. In Excel:
1. Select a range of cells (e.g., A1:D10)
2. Type the formula: `=FT_INCOME("AAPL")`
3. Press Ctrl+Shift+Enter (Windows) or Cmd+Shift+Enter (Mac)

### Dynamic Arrays (Excel 365)

If you have Excel 365, arrays will automatically spill into adjacent cells.

## Notes

- Functions that return arrays will populate multiple cells
- Date parameters should be in YYYY-MM-DD format
- Ticker symbols are case-insensitive
- Functions cache results for performance

