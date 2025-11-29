# Spreadsheet Integration Guide

This guide covers integrating FinanceToolkit with Excel and Google Sheets.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FinanceToolkit                           │
│                   my_finance_layer.py                       │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────────┐
│   xlwings (Excel)       │     │   FastAPI REST API          │
│   Direct Python UDFs    │     │   (Google Cloud Run)        │
│   Offline, Mac+Windows  │     └─────────────────────────────┘
└─────────────────────────┘                   │
                              ┌───────────────┴───────────────┐
                              ▼                               ▼
                    ┌─────────────────┐           ┌───────────────────┐
                    │ Excel Power     │           │ Google Sheets     │
                    │ Query Connector │           │ Apps Script Addon │
                    └─────────────────┘           └───────────────────┘
```

## Quick Start

### Excel (xlwings)

1. **Install xlwings:**
   ```bash
   pip install xlwings
   xlwings addin install
   ```

2. **Set up the add-in:**
   - Copy `excel/financetoolkit.py` to xlwings UDF directory
   - Or add project root to PYTHONPATH

3. **Use in Excel:**
   ```
   =FT_INCOME("AAPL")
   ```

See [excel/README.md](excel/README.md) for detailed instructions.

### Google Sheets

1. **Deploy the API:**
   - Deploy to Google Cloud Run (see [api/README.md](api/README.md))
   - Note the API URL

2. **Set up Apps Script:**
   - Open your Google Sheet
   - Go to **Extensions > Apps Script**
   - Copy `sheets/Code.gs` and HTML files
   - Update `API_BASE_URL` in `Code.gs`

3. **Use in Sheets:**
   ```
   =FT_INCOME("AAPL")
   ```

See [sheets/README.md](sheets/README.md) for detailed instructions.

## Comparison

| Feature | Excel (xlwings) | Google Sheets |
|---------|----------------|---------------|
| **Setup Complexity** | Medium | Easy |
| **Offline Support** | Yes | No (requires API) |
| **Platform** | Mac & Windows | Web (anywhere) |
| **Performance** | Fast (local) | Depends on API |
| **Cost** | Free | Free (API hosting costs) |
| **Customization** | High | Medium |

## Choosing the Right Integration

### Use Excel (xlwings) if:
- You work primarily on Mac or Windows
- You need offline functionality
- You want the fastest performance
- You're comfortable with Python setup

### Use Google Sheets if:
- You need cross-platform access
- You collaborate with others online
- You prefer cloud-based solutions
- You want easier setup (no Python required)

### Use Both:
- Excel for power users and offline work
- Google Sheets for collaboration and sharing

## Common Functions

Both integrations support similar functions:

### Company Analysis
- `FT_INCOME(ticker, start_date)` - Income statement
- `FT_BALANCE(ticker, start_date)` - Balance sheet
- `FT_RATIOS(ticker, ratio_type, start_date)` - Financial ratios
- `FT_RATIO(ticker, metric)` - Specific ratio value
- `FT_WACC(ticker)` - WACC calculation

### Macro Data
- `FT_MACRO(country, metric, start_year)` - Economic indicators

## API Deployment

The Google Sheets integration requires the FastAPI backend to be deployed. See [api/README.md](api/README.md) for deployment instructions.

**Quick Deploy to Cloud Run:**
```bash
# Build and deploy
docker build -t financetoolkit-api .
docker tag financetoolkit-api gcr.io/YOUR_PROJECT/financetoolkit-api
docker push gcr.io/YOUR_PROJECT/financetoolkit-api

gcloud run deploy financetoolkit-api \
  --image gcr.io/YOUR_PROJECT/financetoolkit-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars FMP_API_KEY=your_key
```

## Troubleshooting

### Excel Issues

- **Functions not appearing**: Check xlwings add-in is installed
- **Import errors**: Verify Python path and dependencies
- **API key errors**: Check `.env` file exists

### Google Sheets Issues

- **Functions not working**: Verify API URL in `Code.gs`
- **CORS errors**: Check API CORS configuration
- **Timeout errors**: Check Cloud Run timeout settings

## Next Steps

1. **Set up your preferred integration** (Excel or Sheets)
2. **Test with sample data** (e.g., `=FT_INCOME("AAPL")`)
3. **Explore advanced features** (ratios, models, macro data)
4. **Customize for your workflow** (add functions, modify UI)

## Support

- Excel: See [excel/README.md](excel/README.md)
- Google Sheets: See [sheets/README.md](sheets/README.md)
- API: See [api/README.md](api/README.md)

