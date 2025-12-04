# FinanceToolkit Quick Reference

One-page cheat sheet for financial metrics.

---

## Profitability Ratios

| Metric | Formula | Good | Average | Bad | Code |
|--------|---------|------|---------|-----|------|
| Gross Margin | (Revenue - COGS) / Revenue | > 40% | 20-40% | < 20% | `get_gross_margin()` |
| Operating Margin | Operating Income / Revenue | > 20% | 10-20% | < 10% | `get_operating_margin()` |
| Net Profit Margin | Net Income / Revenue | > 15% | 5-15% | < 5% | `get_net_profit_margin()` |
| ROA | Net Income / Avg Assets | > 10% | 5-10% | < 5% | `get_return_on_assets()` |
| ROE | Net Income / Avg Equity | > 15% | 10-15% | < 10% | `get_return_on_equity()` |
| ROIC | (Net Income - Div) / (Equity + Debt) | > 12% | 8-12% | < 8% | `get_return_on_invested_capital()` |

---

## Liquidity Ratios

| Metric | Formula | Good | Warning | Bad | Code |
|--------|---------|------|---------|-----|------|
| Current Ratio | Current Assets / Current Liabilities | > 2 | 1-2 | < 1 | `get_current_ratio()` |
| Quick Ratio | (Current Assets - Inventory) / Current Liab | > 1 | 0.5-1 | < 0.5 | `get_quick_ratio()` |
| Cash Ratio | Cash / Current Liabilities | > 0.5 | 0.2-0.5 | < 0.2 | `get_cash_ratio()` |

---

## Solvency Ratios

| Metric | Formula | Good | Warning | Risky | Code |
|--------|---------|------|---------|-------|------|
| Debt-to-Equity | Total Debt / Total Equity | < 0.5 | 0.5-1.5 | > 1.5 | `get_debt_to_equity_ratio()` |
| Debt-to-Assets | Total Debt / Total Assets | < 0.3 | 0.3-0.6 | > 0.6 | `get_debt_to_assets_ratio()` |
| Interest Coverage | EBIT / Interest Expense | > 5 | 2-5 | < 2 | `get_interest_coverage_ratio()` |

---

## Valuation Ratios

| Metric | Formula | Cheap | Fair | Expensive | Code |
|--------|---------|-------|------|-----------|------|
| P/E Ratio | Price / EPS | < 15 | 15-25 | > 25 | `get_price_to_earnings_ratio()` |
| P/B Ratio | Price / Book Value | < 1 | 1-3 | > 3 | `get_price_to_book_ratio()` |
| P/S Ratio | Price / Sales | < 1 | 1-3 | > 3 | `get_price_to_sales_ratio()` |
| PEG Ratio | P/E / Growth Rate | < 1 | 1-2 | > 2 | `get_price_to_earnings_growth_ratio()` |
| EV/EBITDA | Enterprise Value / EBITDA | < 8 | 8-12 | > 12 | `get_ev_to_ebitda()` |

---

## Financial Health Scores

### Altman Z-Score
```python
z_score = toolkit.models.get_altman_z_score()
```
| Score | Zone | Interpretation |
|-------|------|----------------|
| > 2.99 | Safe | Low bankruptcy risk |
| 1.81-2.99 | Grey | Moderate risk |
| < 1.81 | Distress | High bankruptcy risk |

### Piotroski F-Score
```python
f_score = toolkit.models.get_piotroski_f_score()
```
| Score | Rating | Interpretation |
|-------|--------|----------------|
| 8-9 | Excellent | Strong financial health |
| 5-7 | Average | Mixed signals |
| 0-4 | Poor | Financial weakness |

---

## Risk Metrics

| Metric | What It Measures | Good | Average | High Risk | Code |
|--------|------------------|------|---------|-----------|------|
| Beta | Market correlation | 0.5-1.0 | 1.0-1.5 | > 1.5 | `get_beta()` |
| VaR (95%) | Daily max loss | -1% | -2-3% | > -4% | `get_value_at_risk()` |
| Max Drawdown | Worst peak-to-trough | -10% | -20-30% | > -40% | `get_maximum_drawdown()` |
| Sharpe Ratio | Return per risk | > 1.5 | 0.5-1.5 | < 0.5 | `get_sharpe_ratio()` |
| Sortino Ratio | Return per downside risk | > 2.0 | 1.0-2.0 | < 1.0 | `get_sortino_ratio()` |

---

## Common Code Patterns

### Initialize Toolkit
```python
from financetoolkit import Toolkit

toolkit = Toolkit(
    tickers=['AAPL', 'MSFT'],
    api_key="YOUR_KEY",
    start_date="2020-01-01"
)
```

### Get All Ratios by Category
```python
# Profitability
toolkit.ratios.collect_profitability_ratios()

# Liquidity
toolkit.ratios.collect_liquidity_ratios()

# Solvency
toolkit.ratios.collect_solvency_ratios()

# Efficiency
toolkit.ratios.collect_efficiency_ratios()

# Valuation
toolkit.ratios.collect_valuation_ratios()

# ALL ratios at once
toolkit.ratios.collect_all_ratios()
```

### Financial Statements
```python
toolkit.get_income_statement()
toolkit.get_balance_sheet_statement()
toolkit.get_cash_flow_statement()
```

### Health Models
```python
toolkit.models.get_altman_z_score()
toolkit.models.get_piotroski_f_score()
toolkit.models.get_dupont_analysis()
toolkit.models.get_extended_dupont_analysis()
```

### Risk Analysis
```python
toolkit.risk.get_value_at_risk()
toolkit.risk.get_conditional_value_at_risk()
toolkit.risk.get_maximum_drawdown()
toolkit.risk.get_beta()
```

### Performance Metrics
```python
toolkit.performance.get_sharpe_ratio()
toolkit.performance.get_sortino_ratio()
toolkit.performance.get_treynor_ratio()
toolkit.performance.get_jensens_alpha()
```

---

## Decision Matrix

| Goal | Primary Metrics | Secondary Metrics |
|------|-----------------|-------------------|
| Check profitability | Net Margin, ROE | ROA, ROIC |
| Assess bankruptcy risk | Altman Z-Score | Debt-to-Equity, Interest Coverage |
| Evaluate financial health | Piotroski F-Score | Current Ratio, Cash Ratio |
| Determine stock value | P/E, EV/EBITDA | P/B, PEG |
| Measure investment risk | Beta, Max Drawdown | VaR, Sharpe Ratio |
| Compare companies | ROE, P/E | ROIC, Piotroski F-Score |

---

## Industry Benchmarks

| Industry | Typical P/E | Typical Net Margin | Typical ROE |
|----------|-------------|-------------------|-------------|
| Technology | 25-40 | 15-25% | 15-25% |
| Healthcare | 20-30 | 10-20% | 12-20% |
| Financials | 10-15 | 20-30% | 10-15% |
| Retail | 15-25 | 2-5% | 15-25% |
| Utilities | 15-20 | 10-15% | 8-12% |
| Energy | 10-20 | 5-15% | 10-20% |

---

## Output to File
```python
# Export to Excel
ratios = toolkit.ratios.collect_all_ratios()
ratios.to_excel('financial_analysis.xlsx')

# Export to CSV
ratios.to_csv('financial_analysis.csv')
```
