# FinanceToolkit FastAPI Backend

REST API backend for FinanceToolkit, enabling integration with Excel, Google Sheets, and other applications.

## Features

- **RESTful API**: Standard HTTP endpoints for all FinanceToolkit operations
- **JSON Responses**: All data returned as JSON-serializable format
- **CORS Enabled**: Ready for web-based integrations
- **Cloud Ready**: Dockerized for easy deployment to Google Cloud Run

## API Endpoints

### Health Check

```
GET /health
```

Returns API health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "FinanceToolkit API"
}
```

### Company Analysis

```
POST /analyze/company
```

Analyze one or more companies.

**Request Body:**
```json
{
  "tickers": "AAPL" or ["AAPL", "MSFT"],
  "start_date": "2020-01-01" (optional),
  "end_date": "2023-12-31" (optional),
  "quarterly": false (optional),
  "include_models": true (optional),
  "include_ratios": true (optional),
  "include_historical": true (optional)
}
```

**Response:**
```json
{
  "statements": {
    "income": {
      "data": [[...], [...]],
      "columns": ["2023", "2022", ...],
      "index": ["Revenue", "Cost of Revenue", ...]
    },
    "balance": {...},
    "cashflow": {...}
  },
  "ratios": {
    "profitability": {...},
    "liquidity": {...},
    ...
  },
  "models": {
    "dupont": {...},
    "wacc": {...},
    ...
  },
  "historical": {...}
}
```

### Portfolio Analysis

```
POST /analyze/portfolio
```

Analyze a portfolio from uploaded file.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body:
  - `file`: CSV or Excel file with portfolio positions
  - `benchmark`: Benchmark ticker (optional, default: "SPY")
  - `start_date`: Start date (optional)
  - `quarterly`: Boolean (optional)

**Response:**
```json
{
  "overview": {
    "data": [[...], [...]],
    "columns": [...],
    "index": [...]
  },
  "performance": {
    "returns": {...},
    "correlations": {...}
  },
  "risk": {
    "var": {...},
    "cvar": {...}
  }
}
```

### Macro Snapshot

```
POST /macro/snapshot
```

Get macroeconomic indicators.

**Request Body:**
```json
{
  "countries": "United States" or ["United States", "Germany"],
  "metrics": ["gdp", "unemployment", "cpi"] (optional),
  "start_year": 2020 (optional),
  "end_year": 2023 (optional)
}
```

**Response:**
```json
{
  "gdp": {
    "data": [[...], [...]],
    "columns": ["United States", "Germany"],
    "index": ["2020", "2021", ...]
  },
  "unemployment": {...},
  "cpi": {...}
}
```

## Local Development

### Prerequisites

- Python 3.10+
- All FinanceToolkit dependencies installed

### Setup

1. **Install dependencies:**
   ```bash
   pip install -r api/requirements.txt
   ```

2. **Set environment variables:**
   Create `.env` file in project root:
   ```env
   FMP_API_KEY=your_api_key_here
   ```

3. **Run the API:**
   ```bash
   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Test the API:**
   ```bash
   curl http://localhost:8000/health
   ```

### Testing Endpoints

**Company Analysis:**
```bash
curl -X POST http://localhost:8000/analyze/company \
  -H "Content-Type: application/json" \
  -d '{
    "tickers": "AAPL",
    "start_date": "2020-01-01"
  }'
```

**Macro Snapshot:**
```bash
curl -X POST http://localhost:8000/macro/snapshot \
  -H "Content-Type: application/json" \
  -d '{
    "countries": "United States",
    "metrics": ["gdp", "unemployment"]
  }'
```

## Deployment to Google Cloud Run

### Prerequisites

- Google Cloud account
- `gcloud` CLI installed
- Docker installed

### Steps

1. **Build the Docker image:**
   ```bash
   docker build -t financetoolkit-api .
   ```

2. **Tag for Google Container Registry:**
   ```bash
   docker tag financetoolkit-api gcr.io/YOUR_PROJECT_ID/financetoolkit-api
   ```

3. **Push to GCR:**
   ```bash
   docker push gcr.io/YOUR_PROJECT_ID/financetoolkit-api
   ```

4. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy financetoolkit-api \
     --image gcr.io/YOUR_PROJECT_ID/financetoolkit-api \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars FMP_API_KEY=your_api_key_here
   ```

5. **Get the service URL:**
   ```bash
   gcloud run services describe financetoolkit-api --region us-central1
   ```

### Environment Variables

Set these in Cloud Run:

- `FMP_API_KEY`: Your Financial Modeling Prep API key (required)
- `DEFAULT_BENCHMARK`: Default benchmark ticker (optional, default: "SPY")
- `DEFAULT_START_DATE`: Default start date (optional)
- `DEFAULT_RISK_FREE_RATE`: Default risk-free rate (optional, default: "10y")

### Using Cloud Build (Alternative)

1. **Create `cloudbuild.yaml`:**
   ```yaml
   steps:
     - name: 'gcr.io/cloud-builders/docker'
       args: ['build', '-t', 'gcr.io/$PROJECT_ID/financetoolkit-api', '.']
     - name: 'gcr.io/cloud-builders/docker'
       args: ['push', 'gcr.io/$PROJECT_ID/financetoolkit-api']
     - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
       entrypoint: gcloud
       args:
         - 'run'
         - 'deploy'
         - 'financetoolkit-api'
         - '--image'
         - 'gcr.io/$PROJECT_ID/financetoolkit-api'
         - '--region'
         - 'us-central1'
         - '--platform'
         - 'managed'
         - '--allow-unauthenticated'
   ```

2. **Submit build:**
   ```bash
   gcloud builds submit --config cloudbuild.yaml
   ```

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Error Handling

All endpoints return standard HTTP status codes:

- `200`: Success
- `400`: Bad Request (invalid parameters)
- `500`: Internal Server Error

Error responses include a `detail` field:

```json
{
  "detail": "Error message here"
}
```

## Rate Limiting

Currently no rate limiting is implemented. For production:

1. Add rate limiting middleware
2. Implement API key authentication
3. Set up request quotas per user/IP

## Security Considerations

1. **API Key Protection**: Store `FMP_API_KEY` as environment variable, never in code
2. **CORS**: Currently allows all origins (`*`). Restrict in production:
   ```python
   allow_origins=["https://your-sheets-domain.com"]
   ```
3. **Authentication**: Consider adding API key authentication for production use
4. **HTTPS**: Always use HTTPS in production (Cloud Run provides this)

## Performance

- Responses are cached at the Toolkit level (per session)
- Large datasets may take 10-30 seconds to process
- Consider implementing response caching (Redis) for production

## Monitoring

Cloud Run provides:
- Request logs
- Error tracking
- Performance metrics

Set up alerts for:
- High error rates
- Slow response times
- High memory usage

## Troubleshooting

### Import Errors

Ensure all dependencies are installed:
```bash
pip install -r api/requirements.txt
```

### API Key Errors

Check that `.env` file exists and contains `FMP_API_KEY`.

### CORS Errors

Verify CORS middleware is configured correctly in `api/main.py`.

### Timeout Errors

Cloud Run has a 60-second timeout by default. For longer operations:
- Increase timeout: `--timeout 300`
- Or implement async processing with task queues

