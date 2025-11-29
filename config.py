"""Configuration helper for FinanceToolkit wrapper layer.

This module handles loading environment variables from .env files
and provides simple getters for configuration values.
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    # If python-dotenv is not installed, we'll just use os.getenv
    # which reads from actual environment variables
    load_dotenv = None


def _load_env_file():
    """Load .env file if python-dotenv is available."""
    if load_dotenv is not None:
        # Load from project root
        env_path = Path(__file__).parent / ".env"
        load_dotenv(dotenv_path=env_path)


# Load environment variables on import
_load_env_file()


def get_api_key() -> str:
    """
    Get the Financial Modeling Prep API key from environment.
    
    Returns:
        str: The API key, or empty string if not found.
        
    Raises:
        ValueError: If API key is not set and python-dotenv is not installed.
    """
    api_key = os.getenv("FMP_API_KEY", "")
    
    if not api_key:
        if load_dotenv is None:
            raise ValueError(
                "FMP_API_KEY not found in environment variables. "
                "Either:\n"
                "1. Set FMP_API_KEY environment variable, or\n"
                "2. Install python-dotenv: pip install python-dotenv\n"
                "   and create a .env file with FMP_API_KEY=your_key"
            )
        else:
            raise ValueError(
                "FMP_API_KEY not found. Please create a .env file in the project root "
                "with: FMP_API_KEY=your_api_key_here\n"
                "Get your free API key at: https://www.jeroenbouma.com/fmp"
            )
    
    return api_key


def get_default_tickers() -> list[str]:
    """
    Get default tickers from environment variable.
    
    Returns:
        list[str]: List of ticker symbols, or empty list if not set.
    """
    tickers_str = os.getenv("DEFAULT_TICKERS", "")
    if tickers_str:
        return [t.strip() for t in tickers_str.split(",") if t.strip()]
    return []


def get_default_benchmark() -> str:
    """
    Get default benchmark ticker from environment variable.
    
    Returns:
        str: Benchmark ticker, defaults to "SPY".
    """
    return os.getenv("DEFAULT_BENCHMARK", "SPY")


def get_default_start_date() -> str | None:
    """
    Get default start date from environment variable.
    
    Returns:
        str | None: Start date in YYYY-MM-DD format, or None if not set.
    """
    return os.getenv("DEFAULT_START_DATE", None)


def get_default_risk_free_rate() -> str:
    """
    Get default risk-free rate identifier from environment variable.
    
    Returns:
        str: Risk-free rate identifier, defaults to "10y".
    """
    return os.getenv("DEFAULT_RISK_FREE_RATE", "10y")

