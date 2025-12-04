# FinanceToolkit Infrastructure

This folder contains infrastructure components for deploying FinanceToolkit as a service.

## Components

| Component | File | Description |
|-----------|------|-------------|
| Database Cache | `database.py` | SQLite caching for financial data |
| REST API | `api.py` | FastAPI web service |
| Web Dashboard | `streamlit_app.py` | Interactive web UI |
| Telegram Bot | `telegram_bot.py` | Chat-based queries |

---

## Quick Start

### 1. Install Dependencies

```bash
# Core dependencies
pip install financetoolkit

# API dependencies
pip install fastapi uvicorn

# Streamlit dependencies
pip install streamlit

# Telegram bot dependencies
pip install python-telegram-bot
```

Or install all at once:
```bash
pip install financetoolkit fastapi uvicorn streamlit python-telegram-bot
```

### 2. Set Environment Variables

```bash
export FMP_API_KEY="your_financial_modeling_prep_key"
export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"  # Only for Telegram bot
```

---

## Database Caching

SQLite-based caching to reduce API calls and enable offline analysis.

### Usage

```python
from infrastructure.database import FinanceDatabase

# Initialize database
db = FinanceDatabase("my_cache.db")

# Store data
db.store_financial_data('AAPL', 'balance_sheet', balance_df)

# Retrieve data
data = db.get_financial_data('AAPL', 'balance_sheet')

# Check if cache is fresh
if db.is_cache_valid('AAPL', 'balance_sheet', max_age_days=7):
    data = db.get_financial_data('AAPL', 'balance_sheet')

# Get cache statistics
print(db.get_cache_stats())
```

### With Toolkit

```python
from financetoolkit import Toolkit
from infrastructure.database import FinanceDatabase, cache_toolkit_data

toolkit = Toolkit(['AAPL', 'MSFT'], api_key="YOUR_KEY")
db = FinanceDatabase()

# Cache all toolkit data
cache_toolkit_data(toolkit, db)
```

---

## REST API

FastAPI-based web service exposing financial analysis endpoints.

### Run the API

```bash
cd FinanceToolkit
uvicorn infrastructure.api:app --reload --port 8000
```

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/api/health` | GET | Detailed status |
| `/api/statements/income/{ticker}` | GET | Income statement |
| `/api/statements/balance/{ticker}` | GET | Balance sheet |
| `/api/ratios/profitability/{ticker}` | GET | Profitability ratios |
| `/api/ratios/all/{ticker}` | GET | All ratios |
| `/api/health-score/{ticker}` | GET | Altman Z & Piotroski F |
| `/api/dupont/{ticker}` | GET | DuPont analysis |
| `/api/risk/{ticker}` | GET | Risk metrics |
| `/api/quick-analysis/{ticker}` | GET | Quick summary |
| `/api/compare` | POST | Compare tickers |

### Example Requests

```bash
# Get health scores
curl http://localhost:8000/api/health-score/AAPL

# Get all ratios
curl http://localhost:8000/api/ratios/all/MSFT

# Quick analysis
curl http://localhost:8000/api/quick-analysis/GOOGL
```

### Interactive Docs

Visit `http://localhost:8000/docs` for Swagger UI documentation.

---

## Streamlit Web App

Interactive web dashboard for financial analysis.

### Run the App

```bash
cd FinanceToolkit
streamlit run infrastructure/streamlit_app.py
```

### Features

- Enter any ticker symbol
- View profitability ratios
- Check health scores (Altman Z, Piotroski F)
- DuPont analysis visualization
- Valuation metrics
- Risk analysis
- Price history charts

### Access

Open `http://localhost:8501` in your browser.

---

## Telegram Bot

Query financial data via Telegram chat.

### Setup

1. **Create a bot with @BotFather:**
   - Open Telegram and search for @BotFather
   - Send `/newbot`
   - Follow prompts to create your bot
   - Copy the bot token

2. **Set environment variables:**
   ```bash
   export TELEGRAM_BOT_TOKEN="your_bot_token"
   export FMP_API_KEY="your_fmp_key"
   ```

3. **Run the bot:**
   ```bash
   python infrastructure/telegram_bot.py
   ```

### Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/help` | List all commands |
| `/analyze TICKER` | Full analysis |
| `/health TICKER` | Health scores |
| `/ratios TICKER` | Profitability ratios |
| `/valuation TICKER` | Valuation metrics |
| `/compare TICKER1 TICKER2` | Compare two stocks |
| `TICKER` | Quick lookup (just type a ticker) |

### Example Conversation

```
You: AAPL
Bot: 📊 AAPL Quick Overview
     • Altman Z-Score: 4.52 ✅
     • Piotroski F-Score: 7/9 ⚠️

You: /health MSFT
Bot: 🏥 MSFT Health Scores
     Altman Z-Score: 5.23
     ✅ Safe Zone (low bankruptcy risk)
     ...
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Users                                │
└─────────────────────────────────────────────────────────────┘
            │                  │                  │
            ▼                  ▼                  ▼
┌───────────────┐    ┌─────────────────┐    ┌──────────────┐
│  Streamlit    │    │    REST API     │    │  Telegram    │
│  Web App      │    │    (FastAPI)    │    │    Bot       │
└───────────────┘    └─────────────────┘    └──────────────┘
            │                  │                  │
            └──────────────────┼──────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │   FinanceToolkit    │
                    │   (Core Library)    │
                    └─────────────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
┌───────────────┐    ┌─────────────────┐    ┌──────────────┐
│   Database    │    │  Financial      │    │   Yahoo      │
│   Cache       │    │  Modeling Prep  │    │   Finance    │
│   (SQLite)    │    │     API         │    │   (Fallback) │
└───────────────┘    └─────────────────┘    └──────────────┘
```

---

## Deployment Options

### Local Development
```bash
# API
uvicorn infrastructure.api:app --reload

# Streamlit
streamlit run infrastructure/streamlit_app.py

# Telegram
python infrastructure/telegram_bot.py
```

### Docker (Coming Soon)
```dockerfile
# Dockerfile for API
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install financetoolkit fastapi uvicorn
CMD ["uvicorn", "infrastructure.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Cloud Deployment
- **Streamlit Cloud**: Deploy `streamlit_app.py` directly
- **Railway/Render**: Deploy FastAPI with `api.py`
- **Heroku**: Use Procfile with uvicorn

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FMP_API_KEY` | Yes | Financial Modeling Prep API key |
| `TELEGRAM_BOT_TOKEN` | For bot | Telegram bot token from @BotFather |

### Database Location

By default, SQLite databases are created in the current directory:
- `finance_cache.db` - General cache
- `finance_api_cache.db` - API cache

Change location:
```python
db = FinanceDatabase("/path/to/my/cache.db")
```
