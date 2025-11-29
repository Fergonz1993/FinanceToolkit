"""FastAPI backend for FinanceToolkit spreadsheet integrations.

This API exposes endpoints for company analysis, portfolio analysis,
and macro economic data retrieval, making it accessible from Excel
and Google Sheets.
"""

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent directory to path to import my_finance_layer
sys.path.insert(0, str(Path(__file__).parent.parent))

from my_finance_layer import analyze_company, analyze_portfolio, get_macro_snapshot

app = FastAPI(
    title="FinanceToolkit API",
    description="REST API for FinanceToolkit financial analysis",
    version="1.0.0",
)

# Enable CORS for Google Sheets and Excel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CompanyAnalysisRequest(BaseModel):
    """Request model for company analysis."""

    tickers: list[str] | str
    start_date: str | None = None
    end_date: str | None = None
    quarterly: bool = False
    include_models: bool = True
    include_ratios: bool = True
    include_historical: bool = True


class MacroSnapshotRequest(BaseModel):
    """Request model for macro snapshot."""

    countries: list[str] | str
    metrics: list[str] | tuple[str, ...] | None = None
    start_year: int | None = None
    end_year: int | None = None


def _dataframe_to_dict(df: pd.DataFrame) -> dict[str, Any]:
    """Convert DataFrame to JSON-serializable dict."""
    if df.empty:
        return {"data": [], "columns": [], "index": []}

    # Convert index to string for JSON serialization
    df_copy = df.copy()
    df_copy.index = df_copy.index.astype(str)

    return {
        "data": df_copy.values.tolist(),
        "columns": df_copy.columns.tolist() if isinstance(df_copy.columns, pd.Index) else list(df_copy.columns),
        "index": df_copy.index.tolist(),
    }


def _dict_to_dataframe(data: dict[str, Any]) -> pd.DataFrame:
    """Convert dict back to DataFrame."""
    if not data or not data.get("data"):
        return pd.DataFrame()

    df = pd.DataFrame(data["data"], columns=data.get("columns", []))
    if data.get("index"):
        df.index = data["index"]
    return df


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "FinanceToolkit API"}


@app.post("/analyze/company")
async def analyze_company_endpoint(request: CompanyAnalysisRequest):
    """
    Analyze one or more companies.

    Returns financial statements, ratios, models, and historical data.
    """
    try:
        result = analyze_company(
            tickers=request.tickers,
            start_date=request.start_date,
            end_date=request.end_date,
            quarterly=request.quarterly,
            include_models=request.include_models,
            include_ratios=request.include_ratios,
            include_historical=request.include_historical,
        )

        # Convert DataFrames to JSON-serializable format
        response: dict[str, Any] = {}

        if "statements" in result:
            response["statements"] = {}
            for stmt_type, df in result["statements"].items():
                if isinstance(df, pd.DataFrame):
                    response["statements"][stmt_type] = _dataframe_to_dict(df)
                else:
                    response["statements"][stmt_type] = df

        if "ratios" in result:
            response["ratios"] = {}
            for ratio_type, df in result["ratios"].items():
                if isinstance(df, pd.DataFrame):
                    response["ratios"][ratio_type] = _dataframe_to_dict(df)
                else:
                    response["ratios"][ratio_type] = df

        if "models" in result:
            response["models"] = {}
            for model_type, df in result["models"].items():
                if isinstance(df, pd.DataFrame):
                    response["models"][model_type] = _dataframe_to_dict(df)
                else:
                    response["models"][model_type] = df

        if "historical" in result:
            if isinstance(result["historical"], pd.DataFrame):
                response["historical"] = _dataframe_to_dict(result["historical"])
            else:
                response["historical"] = result["historical"]

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing company: {str(e)}")


@app.post("/analyze/portfolio")
async def analyze_portfolio_endpoint(
    file: UploadFile = File(...),
    benchmark: str | None = None,
    start_date: str | None = None,
    quarterly: bool = False,
):
    """
    Analyze a portfolio from uploaded file.

    Accepts CSV or Excel files with portfolio positions.
    """
    try:
        # Save uploaded file temporarily
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in [".csv", ".xlsx", ".xls"]:
            raise HTTPException(
                status_code=400,
                detail="File must be CSV or Excel format (.csv, .xlsx, .xls)",
            )

        # Read file content
        contents = await file.read()
        temp_path = Path(f"/tmp/{file.filename}")

        with open(temp_path, "wb") as f:
            f.write(contents)

        try:
            result = analyze_portfolio(
                positions_path=str(temp_path),
                benchmark=benchmark,
                start_date=start_date,
                quarterly=quarterly,
            )

            # Convert DataFrames to JSON-serializable format
            response: dict[str, Any] = {}

            if "overview" in result:
                if isinstance(result["overview"], pd.DataFrame):
                    response["overview"] = _dataframe_to_dict(result["overview"])
                else:
                    response["overview"] = result["overview"]

            if "performance" in result:
                response["performance"] = {}
                for perf_type, df in result["performance"].items():
                    if isinstance(df, pd.DataFrame):
                        response["performance"][perf_type] = _dataframe_to_dict(df)
                    else:
                        response["performance"][perf_type] = df

            if "risk" in result:
                response["risk"] = {}
                for risk_type, df in result["risk"].items():
                    if isinstance(df, pd.DataFrame):
                        response["risk"][risk_type] = _dataframe_to_dict(df)
                    else:
                        response["risk"][risk_type] = df

            return response

        finally:
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing portfolio: {str(e)}")


@app.post("/macro/snapshot")
async def macro_snapshot_endpoint(request: MacroSnapshotRequest):
    """
    Get macroeconomic indicators for specified countries.

    Returns GDP, unemployment, CPI, and other economic data.
    """
    try:
        result = get_macro_snapshot(
            countries=request.countries,
            metrics=request.metrics,
            start_year=request.start_year,
            end_year=request.end_year,
        )

        # Convert DataFrames to JSON-serializable format
        response: dict[str, Any] = {}
        for metric_name, df in result.items():
            if isinstance(df, pd.DataFrame):
                response[metric_name] = _dataframe_to_dict(df)
            else:
                response[metric_name] = df

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting macro snapshot: {str(e)}")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "FinanceToolkit API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "company_analysis": "/analyze/company",
            "portfolio_analysis": "/analyze/portfolio",
            "macro_snapshot": "/macro/snapshot",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

