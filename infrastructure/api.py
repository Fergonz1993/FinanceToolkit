"""
REST API for FinanceToolkit

FastAPI-based web service exposing financial analysis capabilities.

Run with: uvicorn infrastructure.api:app --reload
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os

# Import will work when FinanceToolkit is installed
try:
    from financetoolkit import Toolkit
except ImportError:
    Toolkit = None

from .database import FinanceDatabase

# Initialize FastAPI app
app = FastAPI(
    title="FinanceToolkit API",
    description="REST API for financial analysis using FinanceToolkit",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for web frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
db = FinanceDatabase("finance_api_cache.db")

# Get API key from environment variable
API_KEY = os.environ.get("FMP_API_KEY", "")


# Pydantic models for request/response
class TickerRequest(BaseModel):
    tickers: list[str]
    start_date: Optional[str] = "2020-01-01"
    end_date: Optional[str] = None


class RatioResponse(BaseModel):
    ticker: str
    period: str
    ratios: dict


class HealthScoreResponse(BaseModel):
    ticker: str
    altman_z_score: Optional[float] = None
    piotroski_f_score: Optional[int] = None
    interpretation: dict


# Helper function to get toolkit
def get_toolkit(tickers: list[str], start_date: str = "2020-01-01"):
    """Create a Toolkit instance."""
    if not Toolkit:
        raise HTTPException(
            status_code=500,
            detail="FinanceToolkit not installed. Run: pip install financetoolkit"
        )

    if not API_KEY:
        raise HTTPException(
            status_code=500,
            detail="FMP_API_KEY environment variable not set"
        )

    return Toolkit(
        tickers=tickers,
        api_key=API_KEY,
        start_date=start_date
    )


# ============ ENDPOINTS ============

@app.get("/")
async def root():
    """API health check."""
    return {
        "status": "running",
        "message": "FinanceToolkit API is ready",
        "docs": "/docs"
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check."""
    cache_stats = db.get_cache_stats()
    return {
        "status": "healthy",
        "api_key_configured": bool(API_KEY),
        "toolkit_available": Toolkit is not None,
        "cache_stats": cache_stats
    }


# ============ FINANCIAL STATEMENTS ============

@app.get("/api/statements/income/{ticker}")
async def get_income_statement(
    ticker: str,
    quarterly: bool = Query(False, description="Get quarterly data")
):
    """Get income statement for a ticker."""
    try:
        toolkit = get_toolkit([ticker])
        statement = toolkit.get_income_statement()

        return {
            "ticker": ticker,
            "type": "income_statement",
            "quarterly": quarterly,
            "data": statement.to_dict()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/statements/balance/{ticker}")
async def get_balance_sheet(
    ticker: str,
    quarterly: bool = Query(False, description="Get quarterly data")
):
    """Get balance sheet for a ticker."""
    try:
        toolkit = get_toolkit([ticker])
        statement = toolkit.get_balance_sheet_statement()

        return {
            "ticker": ticker,
            "type": "balance_sheet",
            "quarterly": quarterly,
            "data": statement.to_dict()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/statements/cashflow/{ticker}")
async def get_cash_flow(
    ticker: str,
    quarterly: bool = Query(False, description="Get quarterly data")
):
    """Get cash flow statement for a ticker."""
    try:
        toolkit = get_toolkit([ticker])
        statement = toolkit.get_cash_flow_statement()

        return {
            "ticker": ticker,
            "type": "cash_flow",
            "quarterly": quarterly,
            "data": statement.to_dict()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ RATIOS ============

@app.get("/api/ratios/profitability/{ticker}")
async def get_profitability_ratios(ticker: str):
    """Get profitability ratios for a ticker."""
    try:
        toolkit = get_toolkit([ticker])
        ratios = toolkit.ratios.collect_profitability_ratios()

        return {
            "ticker": ticker,
            "category": "profitability",
            "ratios": ratios.to_dict()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ratios/liquidity/{ticker}")
async def get_liquidity_ratios(ticker: str):
    """Get liquidity ratios for a ticker."""
    try:
        toolkit = get_toolkit([ticker])
        ratios = toolkit.ratios.collect_liquidity_ratios()

        return {
            "ticker": ticker,
            "category": "liquidity",
            "ratios": ratios.to_dict()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ratios/solvency/{ticker}")
async def get_solvency_ratios(ticker: str):
    """Get solvency ratios for a ticker."""
    try:
        toolkit = get_toolkit([ticker])
        ratios = toolkit.ratios.collect_solvency_ratios()

        return {
            "ticker": ticker,
            "category": "solvency",
            "ratios": ratios.to_dict()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ratios/valuation/{ticker}")
async def get_valuation_ratios(ticker: str):
    """Get valuation ratios for a ticker."""
    try:
        toolkit = get_toolkit([ticker])
        ratios = toolkit.ratios.collect_valuation_ratios()

        return {
            "ticker": ticker,
            "category": "valuation",
            "ratios": ratios.to_dict()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ratios/all/{ticker}")
async def get_all_ratios(ticker: str):
    """Get all financial ratios for a ticker."""
    try:
        toolkit = get_toolkit([ticker])
        ratios = toolkit.ratios.collect_all_ratios()

        return {
            "ticker": ticker,
            "category": "all",
            "ratios": ratios.to_dict()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ HEALTH SCORES ============

@app.get("/api/health-score/{ticker}")
async def get_health_scores(ticker: str):
    """
    Get financial health scores (Altman Z-Score, Piotroski F-Score).

    Returns:
        - altman_z_score: Bankruptcy prediction (>2.99 safe, <1.81 risky)
        - piotroski_f_score: Financial strength (0-9, higher is better)
        - interpretations: Plain English explanations
    """
    try:
        toolkit = get_toolkit([ticker])

        # Get scores
        altman = toolkit.models.get_altman_z_score()
        piotroski = toolkit.models.get_piotroski_f_score()

        # Get latest values
        altman_latest = float(altman.iloc[:, -1].values[0]) if not altman.empty else None
        piotroski_latest = int(piotroski.iloc[:, -1].values[0]) if not piotroski.empty else None

        # Interpret Altman Z-Score
        altman_interpretation = "Unknown"
        if altman_latest:
            if altman_latest > 2.99:
                altman_interpretation = "Safe Zone - Low bankruptcy risk"
            elif altman_latest > 1.81:
                altman_interpretation = "Grey Zone - Moderate risk, monitor closely"
            else:
                altman_interpretation = "Distress Zone - High bankruptcy risk"

        # Interpret Piotroski F-Score
        piotroski_interpretation = "Unknown"
        if piotroski_latest is not None:
            if piotroski_latest >= 8:
                piotroski_interpretation = "Excellent - Strong financial health"
            elif piotroski_latest >= 5:
                piotroski_interpretation = "Average - Mixed signals"
            else:
                piotroski_interpretation = "Poor - Financial weakness, caution advised"

        return {
            "ticker": ticker,
            "altman_z_score": altman_latest,
            "piotroski_f_score": piotroski_latest,
            "interpretation": {
                "altman": altman_interpretation,
                "piotroski": piotroski_interpretation
            },
            "historical": {
                "altman": altman.to_dict() if not altman.empty else {},
                "piotroski": piotroski.to_dict() if not piotroski.empty else {}
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dupont/{ticker}")
async def get_dupont_analysis(ticker: str):
    """
    Get DuPont Analysis - breaks down ROE into components.

    Components:
        - Net Profit Margin (profitability)
        - Asset Turnover (efficiency)
        - Equity Multiplier (leverage)
    """
    try:
        toolkit = get_toolkit([ticker])
        dupont = toolkit.models.get_dupont_analysis()

        return {
            "ticker": ticker,
            "analysis": "dupont",
            "explanation": "ROE = Net Margin × Asset Turnover × Equity Multiplier",
            "data": dupont.to_dict()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ RISK METRICS ============

@app.get("/api/risk/{ticker}")
async def get_risk_metrics(
    ticker: str,
    confidence_level: float = Query(0.95, description="Confidence level for VaR (0.9, 0.95, 0.99)")
):
    """
    Get risk metrics for a ticker.

    Returns:
        - value_at_risk: Maximum expected loss at confidence level
        - max_drawdown: Largest peak-to-trough decline
        - beta: Volatility relative to market
    """
    try:
        toolkit = get_toolkit([ticker])

        var = toolkit.risk.get_value_at_risk(confidence_level=confidence_level)
        max_dd = toolkit.risk.get_maximum_drawdown()

        return {
            "ticker": ticker,
            "confidence_level": confidence_level,
            "value_at_risk": var.to_dict() if hasattr(var, 'to_dict') else float(var),
            "max_drawdown": max_dd.to_dict() if hasattr(max_dd, 'to_dict') else float(max_dd),
            "interpretation": {
                "var": f"At {confidence_level*100}% confidence, daily loss won't exceed this amount",
                "max_drawdown": "Largest historical peak-to-trough decline"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ COMPARISON ============

@app.post("/api/compare")
async def compare_tickers(request: TickerRequest):
    """
    Compare multiple tickers side by side.

    Returns key metrics for all requested tickers.
    """
    try:
        toolkit = get_toolkit(request.tickers, request.start_date)

        profitability = toolkit.ratios.collect_profitability_ratios()
        valuation = toolkit.ratios.collect_valuation_ratios()

        return {
            "tickers": request.tickers,
            "comparison": {
                "profitability": profitability.to_dict(),
                "valuation": valuation.to_dict()
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ QUICK ANALYSIS ============

@app.get("/api/quick-analysis/{ticker}")
async def quick_analysis(ticker: str):
    """
    Quick comprehensive analysis of a ticker.

    Returns a summary of key metrics across all categories.
    """
    try:
        toolkit = get_toolkit([ticker])

        # Get key metrics
        profitability = toolkit.ratios.collect_profitability_ratios()
        altman = toolkit.models.get_altman_z_score()
        piotroski = toolkit.models.get_piotroski_f_score()

        # Extract latest values
        latest_year = profitability.columns[-1] if not profitability.empty else "N/A"

        summary = {
            "ticker": ticker,
            "latest_period": str(latest_year),
            "profitability": {},
            "health_scores": {},
            "overall_assessment": ""
        }

        # Extract key profitability metrics
        if not profitability.empty:
            for metric in ['Gross Margin', 'Net Profit Margin', 'Return on Equity']:
                try:
                    val = profitability.loc[(ticker, metric), latest_year]
                    summary["profitability"][metric] = round(float(val) * 100, 2) if val else None
                except (KeyError, TypeError):
                    pass

        # Extract health scores
        altman_val = float(altman.iloc[:, -1].values[0]) if not altman.empty else None
        piotroski_val = int(piotroski.iloc[:, -1].values[0]) if not piotroski.empty else None

        summary["health_scores"] = {
            "altman_z_score": round(altman_val, 2) if altman_val else None,
            "piotroski_f_score": piotroski_val
        }

        # Generate overall assessment
        assessment_points = []
        if altman_val and altman_val > 2.99:
            assessment_points.append("Low bankruptcy risk")
        elif altman_val and altman_val < 1.81:
            assessment_points.append("HIGH bankruptcy risk")

        if piotroski_val and piotroski_val >= 8:
            assessment_points.append("Strong financial health")
        elif piotroski_val and piotroski_val <= 4:
            assessment_points.append("Weak financial health")

        summary["overall_assessment"] = "; ".join(assessment_points) if assessment_points else "Moderate"

        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ CACHE MANAGEMENT ============

@app.get("/api/cache/stats")
async def cache_stats():
    """Get cache statistics."""
    return db.get_cache_stats()


@app.get("/api/cache/tickers")
async def cached_tickers():
    """List all cached tickers."""
    return {"tickers": db.list_cached_tickers()}


@app.delete("/api/cache/{ticker}")
async def clear_ticker_cache(ticker: str):
    """Clear cache for a specific ticker."""
    db.clear_cache(ticker)
    return {"message": f"Cache cleared for {ticker}"}


@app.delete("/api/cache")
async def clear_all_cache():
    """Clear all cached data."""
    db.clear_cache()
    return {"message": "All cache cleared"}


# Run with: uvicorn infrastructure.api:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
