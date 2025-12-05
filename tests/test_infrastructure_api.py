import hashlib
import importlib
import os

import pandas as pd
import pytest
from fastapi.testclient import TestClient

TEST_API_KEY = "test-key"


@pytest.fixture()
def api_app(monkeypatch):
    """
    Reload the API module with test-friendly settings and stubbed Toolkit.

    - Auth enabled with a known API key hash
    - Rate limiting disabled (in-memory) to avoid Redis dependency
    - API cache disabled to keep tests deterministic
    - Metrics enabled to validate /metrics endpoint
    """
    os.environ.update(
        {
            "AUTH_ENABLED": "true",
            "VALID_API_KEY_HASHES": hashlib.sha256(TEST_API_KEY.encode()).hexdigest(),
            "FMP_API_KEY": "dummy-key",
            "API_CACHE_ENABLED": "false",
            "RATE_LIMIT_ENABLED": "false",
            "RATE_LIMIT_STORAGE": "memory",
            "ENVIRONMENT": "test",
            "METRICS_ENABLED": "true",
        }
    )

    # Reload modules so they pick up the test env vars
    importlib.reload(importlib.import_module("infrastructure.security.rate_limiter"))
    importlib.reload(importlib.import_module("infrastructure.security.auth"))
    api_module = importlib.reload(importlib.import_module("infrastructure.api"))

    class StubToolkit:
        """Lightweight Toolkit stub to avoid external calls."""

        def __init__(self, tickers, api_key=None, start_date=None, quarterly=False, **_):
            self._tickers = tickers
            self.ratios = self
            self.models = self
            self.risk = self
            self._income_statement = pd.DataFrame({"2023": [100.0]}, index=["Revenue"])
            self._balance_sheet = pd.DataFrame({"2023": [200.0]}, index=["Assets"])
            self._cash_flow = pd.DataFrame({"2023": [50.0]}, index=["CFO"])

        # Statements
        def get_income_statement(self):
            return self._income_statement

        def get_balance_sheet_statement(self):
            return self._balance_sheet

        def get_cash_flow_statement(self):
            return self._cash_flow

        # Ratios
        def collect_profitability_ratios(self):
            idx = pd.MultiIndex.from_tuples(
                [
                    (self._tickers[0].upper(), "Gross Margin"),
                    (self._tickers[0].upper(), "Net Profit Margin"),
                    (self._tickers[0].upper(), "Return on Equity"),
                ],
                names=["ticker", "metric"],
            )
            return pd.DataFrame({"2023": [0.3, 0.2, 0.1]}, index=idx)

        def collect_liquidity_ratios(self):
            return pd.DataFrame({"2023": [1.5]}, index=["Current Ratio"])

        def collect_solvency_ratios(self):
            return pd.DataFrame({"2023": [0.4]}, index=["Debt Ratio"])

        def collect_valuation_ratios(self):
            return pd.DataFrame({"2023": [15.0]}, index=["P/E"])

        def collect_all_ratios(self):
            return self.collect_profitability_ratios()

        # Models
        def get_altman_z_score(self):
            return pd.DataFrame({"2023": [3.2]}, index=["Z-Score"])

        def get_piotroski_f_score(self):
            return pd.DataFrame({"2023": [8]}, index=["F-Score"])

        def get_dupont_analysis(self):
            return pd.DataFrame({"Net Margin": [0.2], "Asset Turnover": [1.1], "Equity Multiplier": [2.0]})

        # Risk
        def get_value_at_risk(self, confidence_level=0.95):
            return pd.Series({"VaR": -0.05})

        def get_maximum_drawdown(self):
            return -0.12

    # Replace Toolkit with stub and clear caches
    monkeypatch.setattr(api_module, "Toolkit", StubToolkit)
    api_module._get_toolkit_cached.cache_clear()

    return api_module


@pytest.fixture()
def client(api_app):
    return TestClient(api_app.app)


def test_auth_required(client):
    response = client.get("/api/statements/income/AAPL")
    assert response.status_code == 401
    body = response.json()
    assert body["code"].startswith("http_")
    assert body["request_id"]


def test_income_statement_success(client):
    response = client.get("/api/statements/income/AAPL", headers={"X-API-Key": TEST_API_KEY})
    assert response.status_code == 200
    payload = response.json()
    assert payload["ticker"] == "AAPL"
    assert payload["data"]["Revenue"] == {"2023": 100.0}


def test_validation_error_payload(client):
    response = client.get("/api/ratios/profitability/!!!", headers={"X-API-Key": TEST_API_KEY})
    assert response.status_code == 400
    body = response.json()
    assert body["code"].startswith("http_400")
    assert body["message"]
    assert body["request_id"]


def test_metrics_and_health(client):
    # Prime some requests to have metrics
    client.get("/api/statements/income/AAPL", headers={"X-API-Key": TEST_API_KEY})

    metrics_resp = client.get("/metrics")
    assert metrics_resp.status_code == 200
    assert b"ftk_api_requests_total" in metrics_resp.content

    readiness = client.get("/health/ready")
    assert readiness.status_code in (200, 503)
    body = readiness.json()
    assert "checks" in body
