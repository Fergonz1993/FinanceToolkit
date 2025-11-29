# Google Sheets Integration

This directory contains the Google Sheets Apps Script add-on for FinanceToolkit, allowing you to use financial analysis functions directly in Google Sheets.

## Features

- **Custom Functions**: Use formulas like `=FT_INCOME("AAPL")` directly in Sheets cells
- **Custom Menu**: Access analysis tools via FinanceToolkit menu
- **Sidebar UI**: User-friendly interface for complex analyses
- **Cloud-Based**: Works anywhere Google Sheets works

## Available Custom Functions

### Company Analysis

- `=FT_INCOME(ticker, start_date)` - Get income statement
- `=FT_BALANCE(ticker, start_date)` - Get balance sheet
- `=FT_RATIOS(ticker, ratio_type, start_date)` - Get financial ratios
  - ratio_type: "profitability", "liquidity", "solvency", "efficiency", "valuation"
- `=FT_RATIO(ticker, metric)` - Get specific ratio value
- `=FT_WACC(ticker)` - Calculate WACC

### Macro Economic Data

- `=FT_MACRO(country, metric, start_year)` - Get macroeconomic indicators
  - metric: "gdp", "unemployment", "cpi", "inflation"

## Setup Instructions

### Prerequisites

1. **Deploy the FastAPI Backend** (see `api/README.md`)
   - Deploy to Google Cloud Run or use localhost for testing
   - Note the API URL (e.g., `https://your-service-xxxxx-uc.a.run.app`)

2. **Google Account** with access to Google Sheets

### Installation

#### Option 1: Use in a Specific Spreadsheet (Recommended for Testing)

1. Open your Google Sheet
2. Go to **Extensions > Apps Script**
3. Delete the default code
4. Copy and paste the contents of `Code.gs` into the editor
5. Create HTML files:
   - Click **+** next to Files, select **HTML**
   - Name it `Sidebar` and paste contents of `Sidebar.html`
   - Repeat for `MacroSidebar.html`, `PortfolioSidebar.html`, `SettingsSidebar.html`
6. Update `API_BASE_URL` in `Code.gs` with your Cloud Run URL:
   ```javascript
   const API_BASE_URL = 'https://your-service-xxxxx-uc.a.run.app';
   ```
7. Save the project (Ctrl+S or Cmd+S)
8. Refresh your Google Sheet
9. You should see a **FinanceToolkit** menu in the menu bar

#### Option 2: Deploy as Add-on (For Distribution)

1. Follow steps 1-6 from Option 1
2. Click **Deploy > New deployment**
3. Select type: **Add-on**
4. Fill in add-on details
5. Set permissions and publish

### Configuration

Update the API URL in `Code.gs`:

```javascript
// For local testing
const API_BASE_URL = 'http://localhost:8000';

// For production (Cloud Run)
const API_BASE_URL = 'https://your-service-name-xxxxx-uc.a.run.app';
```

## Usage Examples

### Using Custom Functions

In any cell, you can use:

```
=FT_INCOME("AAPL", "2020-01-01")
```

This will return a 2D array with the income statement data.

### Using the Menu

1. Click **FinanceToolkit** in the menu bar
2. Select an option:
   - **Analyze Company** - Opens sidebar for company analysis
   - **Analyze Portfolio** - Opens sidebar for portfolio analysis
   - **Get Macro Snapshot** - Opens sidebar for macro data
   - **Settings** - View API configuration

### Example Workflows

#### Get Income Statement

1. Select a cell
2. Type: `=FT_INCOME("AAPL")`
3. Press Enter
4. The data will populate multiple cells (array formula)

#### Get Profitability Ratios

```
=FT_RATIOS("AAPL", "profitability", "2020-01-01")
```

#### Get Specific Ratio

```
=FT_RATIO("AAPL", "Return on Equity")
```

#### Get Macro Data

```
=FT_MACRO("United States", "gdp", 2020)
```

#### Using Sidebar

1. Click **FinanceToolkit > Analyze Company**
2. Enter ticker: `AAPL`
3. Optionally set start date
4. Click **Analyze Company**
5. Results are written to the active sheet

## Troubleshooting

### Functions Not Working

1. **Check API URL**: Verify `API_BASE_URL` in `Code.gs` is correct
2. **Check API Status**: Visit `https://your-api-url/health` in browser
3. **Check Permissions**: Ensure Apps Script has permission to make external requests
4. **Check Console**: Go to **Extensions > Apps Script > Executions** to see error logs

### API Errors

1. **CORS Errors**: Ensure your FastAPI backend has CORS enabled (already configured)
2. **Timeout Errors**: Cloud Run may need longer timeout for large requests
3. **Authentication**: If you added API key auth, update the fetch calls in `Code.gs`

### Function Returns #ERROR

1. Check the function syntax matches the examples
2. Verify ticker symbols are valid
3. Check that dates are in correct format (YYYY-MM-DD)
4. Look at Apps Script execution logs for detailed errors

## Advanced Configuration

### Adding API Key Authentication

If you secure your API with an API key, update the fetch calls:

```javascript
const response = UrlFetchApp.fetch(API_BASE_URL + '/analyze/company', {
  method: 'post',
  contentType: 'application/json',
  headers: {
    'X-API-Key': 'your-api-key-here'
  },
  payload: JSON.stringify(request)
});
```

### Customizing Sidebars

Edit the HTML files (`Sidebar.html`, `MacroSidebar.html`, etc.) to customize the UI.

### Adding New Functions

1. Add the function to `Code.gs`
2. Use `@customFunction` decorator (if using TypeScript)
3. Document the function parameters
4. Test in a spreadsheet

## API Endpoints Used

- `POST /analyze/company` - Company analysis
- `POST /macro/snapshot` - Macro economic data
- `GET /health` - Health check

See `api/README.md` for full API documentation.

## Notes

- Custom functions are recalculated when the sheet recalculates
- Large datasets may take time to load
- Some functions return arrays that populate multiple cells
- The add-on requires internet connection to call the API

