# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FinanceToolkit is a Python library providing 150+ financial ratios, indicators, and performance measurements. It uses a Model-Controller architecture where controllers handle user-facing APIs and models contain calculation logic.

## Development Commands

```bash
# Install dependencies (uses uv package manager)
uv sync

# Run all tests
pytest

# Run specific test file
pytest tests/ratios/test_profitability_model.py

# Run tests with coverage
pytest --cov=financetoolkit tests/

# Run tests with recording for API cassettes
pytest tests --record-mode=rewrite

# Format code
black financetoolkit

# Lint
ruff check financetoolkit --fix

# Type checking
mypy financetoolkit --ignore-missing-imports

# Run all linting via pre-commit
pre-commit run --all-files
```

## Architecture

### Module Structure
Each financial module follows this pattern:
- `*_controller.py` - User-facing API, orchestrates data flow
- `*_model.py` - Pure calculation functions (can be used independently)
- `helpers.py` - Utility functions per module

### Main Entry Point
```python
from financetoolkit import Toolkit
toolkit = Toolkit(['AAPL', 'MSFT'], api_key="YOUR_KEY")
```

### Sub-controllers (accessed via Toolkit)
- `toolkit.ratios` - 50+ financial ratios (profitability, liquidity, efficiency, solvency, valuation)
- `toolkit.models` - DCF, DuPont, WACC, Altman Z-Score, Piotroski F-Score
- `toolkit.technicals` - Momentum, volatility, breadth, overlap indicators
- `toolkit.options` - Black-Scholes, Binomial Trees, Greeks
- `toolkit.risk` - VaR, CVaR, EVaR, GARCH
- `toolkit.performance` - Performance attribution metrics
- `toolkit.portfolio` - Portfolio analysis
- `toolkit.fixedincome` - Bonds, derivatives, rate data (FRED, Fed, ECB)
- `toolkit.economics` - OECD, macroeconomic indicators
- `toolkit.discovery` - Stock screening

### Data Sources
- **Financial Modeling Prep** (primary) - Financial statements, fundamentals
- **Yahoo Finance** (fallback) - Historical prices
- **FRED/Fed/ECB/OECD** - Economic data

## Code Style

- Line length: 122 characters
- Docstrings: Google-style (`__docformat__ = "google"`)
- Runtime warnings for division by zero in financial calculations are intentionally ignored
- Type hints used throughout

## Testing

Tests mirror the main package structure. Test infrastructure includes:
- Custom `Record` class in `conftest.py` for API response recording/playback
- Test datasets in `tests/datasets/`, `tests/csv/`, `tests/json/`
- Pytest timeout default: 2 minutes

## Key Files

- `financetoolkit/toolkit_controller.py` - Main entry point (3,800+ lines)
- `financetoolkit/fmp_model.py` - Financial Modeling Prep API integration
- `financetoolkit/normalization/` - CSV files for financial statement normalization
