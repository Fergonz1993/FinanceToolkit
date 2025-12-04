# FinanceToolkit Beginner's Guide

A plain English guide to understanding financial metrics and how to calculate them.

## Table of Contents
1. [What is FinanceToolkit?](#what-is-financetoolkit)
2. [Getting Started](#getting-started)
3. [Profitability Ratios](#profitability-ratios)
4. [Health Scores](#health-scores)
5. [Valuation Metrics](#valuation-metrics)
6. [Risk Metrics](#risk-metrics)
7. [Decision Guide](#decision-guide)

---

# What is FinanceToolkit?

FinanceToolkit is a Python library that calculates 150+ financial metrics for any publicly traded company. It answers questions like:
- Is this company profitable?
- Is this company at risk of bankruptcy?
- Is this stock cheap or expensive?
- How risky is this investment?

**Why use it?** Different financial websites report different numbers for the same metric. FinanceToolkit shows you exactly how each calculation is done - no black boxes.

---

# Getting Started

## Installation
```bash
pip install financetoolkit -U
```

## Basic Usage
```python
from financetoolkit import Toolkit

# Create a toolkit for companies you want to analyze
toolkit = Toolkit(
    tickers=['AAPL', 'MSFT'],  # Apple and Microsoft
    api_key="YOUR_API_KEY",    # Get from financialmodelingprep.com
    start_date="2020-01-01"
)

# Get profitability ratios
profitability = toolkit.ratios.collect_profitability_ratios()
print(profitability)
```

**No API key?** See [offline-tutorial.md](offline-tutorial.md) to use sample data.

---

# Profitability Ratios

These ratios answer: **"How good is this company at making money?"**

## Gross Margin

### What is it?
The percentage of revenue left after paying for the cost of making the product.

### Why it matters
Shows how much profit the company keeps from each sale before paying for other expenses like salaries, rent, and marketing.

### Formula
```
Gross Margin = (Revenue - Cost of Goods Sold) / Revenue
```

### How to Interpret
| Value | Meaning |
|-------|---------|
| > 50% | Excellent - strong pricing power or low production costs |
| 30-50% | Good - healthy margins for most industries |
| 10-30% | Average - typical for retail, manufacturing |
| < 10% | Low - commodity business, high competition |

### Industry Context
- Software/SaaS: 70-90% (no physical product)
- Luxury goods: 60-70%
- Retail: 20-40%
- Grocery: 10-15%
- Airlines: 5-15%

### Code Example
```python
gross_margin = toolkit.ratios.get_gross_margin()
print(gross_margin)
```

---

## Net Profit Margin

### What is it?
The percentage of revenue that becomes actual profit after ALL expenses (production, salaries, taxes, interest, everything).

### Why it matters
The "bottom line" - how much of every dollar in sales the company actually keeps.

### Formula
```
Net Profit Margin = Net Income / Revenue
```

### How to Interpret
| Value | Meaning |
|-------|---------|
| > 20% | Excellent - very profitable business |
| 10-20% | Good - healthy profitability |
| 5-10% | Average - typical for most industries |
| 0-5% | Low - tight margins, competitive industry |
| < 0% | Losing money on every sale |

### Industry Context
- Software: 20-30%
- Banks: 20-30%
- Healthcare: 10-15%
- Retail: 2-5%
- Airlines: 1-5%

### Code Example
```python
net_margin = toolkit.ratios.get_net_profit_margin()
```

---

## Return on Assets (ROA)

### What is it?
How much profit the company generates for every dollar of assets it owns.

### Why it matters
Measures how efficiently a company uses its assets (buildings, equipment, inventory, cash) to generate profit.

### Formula
```
ROA = Net Income / Average Total Assets
```

### How to Interpret
| Value | Meaning |
|-------|---------|
| > 10% | Excellent - very efficient use of assets |
| 5-10% | Good - solid efficiency |
| 2-5% | Average - typical for asset-heavy industries |
| < 2% | Poor - assets not generating much profit |

### Industry Context
- Technology: 10-20% (asset-light)
- Retail: 5-10%
- Manufacturing: 3-8%
- Utilities: 2-5% (asset-heavy)
- Banks: 1-2% (hold massive assets)

### Code Example
```python
roa = toolkit.ratios.get_return_on_assets()
```

---

## Return on Equity (ROE)

### What is it?
How much profit the company generates for every dollar shareholders have invested.

### Why it matters
Shows how well management uses shareholder money to generate profits. A key metric for comparing companies.

### Formula
```
ROE = Net Income / Average Shareholders' Equity
```

### How to Interpret
| Value | Meaning |
|-------|---------|
| > 20% | Excellent - great return for shareholders |
| 15-20% | Good - solid performance |
| 10-15% | Average - acceptable |
| < 10% | Below average - may be better investments elsewhere |
| < 0% | Company is losing money |

### Warning
High ROE can be good OR bad:
- Good: Company is genuinely profitable
- Bad: Company has lots of debt (low equity), inflating the ratio

Always check debt levels alongside ROE.

### Code Example
```python
roe = toolkit.ratios.get_return_on_equity()
```

---

## Return on Invested Capital (ROIC)

### What is it?
How much profit the company generates from all the capital invested in it (both shareholder equity AND debt).

### Why it matters
Unlike ROE, ROIC accounts for debt. It shows the true efficiency of capital allocation - useful for comparing companies with different debt levels.

### Formula
```
ROIC = (Net Income - Dividends) / (Total Equity + Total Debt)
```

### How to Interpret
| Value | Meaning |
|-------|---------|
| > 15% | Excellent - creating significant value |
| 10-15% | Good - solid returns on capital |
| 5-10% | Average |
| < Cost of Capital | Destroying value - earning less than it costs to raise money |

### The Golden Rule
**ROIC should be higher than the company's cost of capital (WACC)**. If a company earns 8% on invested capital but pays 10% for that capital, it's destroying value.

### Code Example
```python
roic = toolkit.ratios.get_return_on_invested_capital()
```

---

# Health Scores

These answer: **"Is this company financially healthy or at risk?"**

## Altman Z-Score

### What is it?
A bankruptcy prediction score. Combines 5 ratios into one number that predicts how likely a company is to go bankrupt in the next 2 years.

### Why it matters
Invented by Professor Edward Altman in 1968, this score has correctly predicted bankruptcies with ~80% accuracy.

### Formula
```
Z-Score = 1.2×A + 1.4×B + 3.3×C + 0.6×D + 1.0×E

Where:
A = Working Capital / Total Assets (liquidity)
B = Retained Earnings / Total Assets (cumulative profitability)
C = EBIT / Total Assets (operating efficiency)
D = Market Value of Equity / Total Liabilities (solvency)
E = Sales / Total Assets (asset efficiency)
```

### How to Interpret
| Z-Score | Zone | Meaning |
|---------|------|---------|
| > 2.99 | Safe Zone | Low probability of bankruptcy |
| 1.81 - 2.99 | Grey Zone | Moderate risk - needs monitoring |
| < 1.81 | Distress Zone | High probability of bankruptcy |

### The 5 Components Explained

1. **Working Capital / Total Assets** (Weight: 1.2)
   - Can the company pay its short-term bills?
   - Negative = company owes more short-term than it has

2. **Retained Earnings / Total Assets** (Weight: 1.4)
   - How much profit has accumulated over time?
   - Young companies naturally score lower here

3. **EBIT / Total Assets** (Weight: 3.3)
   - Is the company's core business profitable?
   - This has the highest weight - operating profit matters most

4. **Market Cap / Total Liabilities** (Weight: 0.6)
   - Does the market value exceed what the company owes?
   - Market's confidence in the company

5. **Sales / Total Assets** (Weight: 1.0)
   - How efficiently does the company use assets to generate sales?

### Code Example
```python
altman = toolkit.models.get_altman_z_score()
print(altman)

# Also get the individual components
components = toolkit.models.get_altman_z_score_components()
```

---

## Piotroski F-Score

### What is it?
A financial strength score from 0-9. Each point represents passing one of 9 financial health tests.

### Why it matters
Developed by Professor Joseph Piotroski in 2000. Research shows that high F-Score stocks (8-9) significantly outperform low F-Score stocks (0-2).

### The 9 Criteria

**Profitability (4 points):**

| # | Test | What it Checks | Score |
|---|------|----------------|-------|
| 1 | ROA > 0 | Is the company profitable? | 0 or 1 |
| 2 | Operating Cash Flow > 0 | Is cash actually coming in? | 0 or 1 |
| 3 | ROA Increasing | Is profitability improving? | 0 or 1 |
| 4 | Cash Flow > Net Income | Are earnings real (not accounting tricks)? | 0 or 1 |

**Leverage & Liquidity (3 points):**

| # | Test | What it Checks | Score |
|---|------|----------------|-------|
| 5 | Debt Ratio Decreasing | Is the company reducing debt? | 0 or 1 |
| 6 | Current Ratio Increasing | Can it pay short-term bills better? | 0 or 1 |
| 7 | No New Shares Issued | Is it NOT diluting shareholders? | 0 or 1 |

**Operating Efficiency (2 points):**

| # | Test | What it Checks | Score |
|---|------|----------------|-------|
| 8 | Gross Margin Increasing | Is pricing power/efficiency improving? | 0 or 1 |
| 9 | Asset Turnover Increasing | Is it using assets more efficiently? | 0 or 1 |

### How to Interpret
| F-Score | Rating | Meaning |
|---------|--------|---------|
| 8-9 | Excellent | Strong financial health, consider buying |
| 5-7 | Average | Mixed signals, dig deeper |
| 0-4 | Poor | Financial weakness, caution advised |

### Code Example
```python
piotroski = toolkit.models.get_piotroski_f_score()
print(piotroski)

# Get individual criteria to see what's passing/failing
criteria = toolkit.models.get_piotroski_f_score_components()
```

---

## DuPont Analysis

### What is it?
Breaks down Return on Equity (ROE) into three components to show *why* a company has high or low ROE.

### Why it matters
Two companies can have the same ROE but achieve it in completely different ways. DuPont shows you whether high ROE comes from:
- Being good at selling (profit margins)
- Using assets efficiently (turnover)
- Using lots of debt (leverage)

### Formula
```
ROE = Net Profit Margin × Asset Turnover × Equity Multiplier

Where:
- Net Profit Margin = Net Income / Revenue (profitability)
- Asset Turnover = Revenue / Total Assets (efficiency)
- Equity Multiplier = Total Assets / Shareholders' Equity (leverage)
```

### How to Interpret

**Example 1: Quality ROE**
- ROE = 20%
- Net Margin = 20%, Asset Turnover = 0.5, Equity Multiplier = 2
- Interpretation: High ROE from strong profitability. Good sign!

**Example 2: Risky ROE**
- ROE = 20%
- Net Margin = 5%, Asset Turnover = 0.8, Equity Multiplier = 5
- Interpretation: High ROE from heavy debt. Risky!

### What Each Component Tells You

| Component | High Value Means | Watch Out For |
|-----------|------------------|---------------|
| Net Margin | Strong pricing power, efficient operations | Declining margins over time |
| Asset Turnover | Efficient use of assets | Very low = assets sitting idle |
| Equity Multiplier | More debt being used | > 3 = very leveraged |

### Code Example
```python
dupont = toolkit.models.get_dupont_analysis()
print(dupont)

# Extended DuPont (5-way decomposition)
extended = toolkit.models.get_extended_dupont_analysis()
```

---

# Valuation Metrics

These answer: **"Is this stock cheap or expensive?"**

## Price-to-Earnings (P/E) Ratio

### What is it?
How much investors are willing to pay for each dollar of the company's earnings.

### Why it matters
The most common valuation metric. A P/E of 20 means investors pay $20 for every $1 of earnings.

### Formula
```
P/E Ratio = Stock Price / Earnings Per Share
```

### How to Interpret
| P/E | Meaning |
|-----|---------|
| < 10 | Cheap (or investors expect earnings to fall) |
| 10-20 | Average valuation |
| 20-30 | Expensive (or investors expect strong growth) |
| > 30 | Very expensive (high growth expected) |
| Negative | Company is losing money |

### Important Context
- **Growth companies** often have high P/E (Amazon traded at 100+ P/E for years)
- **Mature companies** usually have lower P/E (10-15)
- **Compare within industry** - tech P/E differs from utility P/E

### Code Example
```python
pe_ratio = toolkit.ratios.get_price_to_earnings_ratio()
```

---

## Price-to-Book (P/B) Ratio

### What is it?
How much investors pay relative to the company's book value (assets minus liabilities).

### Why it matters
Shows if you're paying more or less than what the company would be worth if liquidated today.

### Formula
```
P/B Ratio = Stock Price / Book Value Per Share
```

### How to Interpret
| P/B | Meaning |
|-----|---------|
| < 1 | Stock trades below liquidation value (cheap OR troubled) |
| 1-3 | Reasonable valuation |
| > 3 | Premium valuation (for strong brands, intellectual property) |

### Industry Context
- Banks: 0.5-1.5 (asset-based business)
- Manufacturing: 1-3
- Tech: 3-10+ (value is in IP, not physical assets)

### Code Example
```python
pb_ratio = toolkit.ratios.get_price_to_book_ratio()
```

---

## PEG Ratio

### What is it?
P/E ratio adjusted for growth. Answers: "Is the P/E justified by growth?"

### Why it matters
A company with P/E of 30 might be cheap if it's growing 40% per year, but expensive if growing 5%.

### Formula
```
PEG Ratio = P/E Ratio / Earnings Growth Rate
```

### How to Interpret
| PEG | Meaning |
|-----|---------|
| < 1 | Potentially undervalued relative to growth |
| 1 | Fairly valued |
| > 1 | Potentially overvalued relative to growth |
| > 2 | Expensive unless there's something special |

### Code Example
```python
peg = toolkit.ratios.get_price_to_earnings_growth_ratio()
```

---

## EV/EBITDA

### What is it?
Enterprise Value divided by operating profit (before interest, taxes, depreciation).

### Why it matters
Unlike P/E, this accounts for debt. Two companies with the same P/E but different debt loads will have different EV/EBITDA.

### Formula
```
EV/EBITDA = Enterprise Value / EBITDA

Where:
Enterprise Value = Market Cap + Total Debt - Cash
EBITDA = Earnings Before Interest, Taxes, Depreciation & Amortization
```

### How to Interpret
| EV/EBITDA | Meaning |
|-----------|---------|
| < 8 | Cheap |
| 8-12 | Fairly valued |
| 12-20 | Expensive |
| > 20 | Very expensive |

### Code Example
```python
ev_ebitda = toolkit.ratios.get_ev_to_ebitda()
```

---

# Risk Metrics

These answer: **"How risky is this investment?"**

## Value at Risk (VaR)

### What is it?
The maximum loss you can expect on a "normal bad day."

### Why it matters
VaR answers: "In 95% of days, what's the worst I can lose?"

### Example
```
VaR (95%) = -3%
```
This means: "95% of the time, you won't lose more than 3% in a single day."

### Plain English Interpretation
| VaR (95%) | Meaning |
|-----------|---------|
| -1% | Very low risk - most days are calm |
| -2% to -3% | Moderate risk - typical for large stocks |
| -4% to -5% | Higher risk - volatile stock |
| > -5% | High risk - expect big swings |

### Code Example
```python
var = toolkit.risk.get_value_at_risk(confidence_level=0.95)
print(var)  # Returns daily VaR
```

---

## Maximum Drawdown

### What is it?
The largest peak-to-trough drop in value over a period.

### Why it matters
Shows the worst case scenario that actually happened. If maximum drawdown is -50%, the stock lost half its value at some point.

### Formula
```
Maximum Drawdown = (Trough Value - Peak Value) / Peak Value
```

### How to Interpret
| Max Drawdown | Risk Level | Example |
|--------------|------------|---------|
| -10% | Low | Conservative stocks, bonds |
| -20% | Moderate | Large stable companies |
| -30% to -40% | High | Growth stocks, small caps |
| > -50% | Very High | Speculative investments |

### Code Example
```python
max_dd = toolkit.risk.get_maximum_drawdown()
```

---

## Sharpe Ratio

### What is it?
Return earned per unit of risk taken. Measures risk-adjusted performance.

### Why it matters
Answers: "Am I being compensated enough for the risk I'm taking?"

### Formula
```
Sharpe Ratio = (Portfolio Return - Risk-Free Rate) / Portfolio Standard Deviation
```

### How to Interpret
| Sharpe | Rating | Meaning |
|--------|--------|---------|
| < 0 | Bad | Losing money or worse than risk-free |
| 0-0.5 | Poor | Not enough return for the risk |
| 0.5-1.0 | Average | Acceptable risk-adjusted return |
| 1.0-2.0 | Good | Good return for risk taken |
| > 2.0 | Excellent | Great risk-adjusted performance |

### Code Example
```python
sharpe = toolkit.performance.get_sharpe_ratio()
```

---

## Beta

### What is it?
How much the stock moves relative to the overall market.

### Why it matters
Beta tells you if a stock is more or less volatile than the market.

### Formula
```
Beta = Covariance(Stock, Market) / Variance(Market)
```

### How to Interpret
| Beta | Meaning | Example |
|------|---------|---------|
| < 0 | Moves opposite to market | Gold stocks (sometimes) |
| 0 | No correlation to market | Some bonds |
| 0.5 | Half as volatile as market | Utilities |
| 1.0 | Moves with market | Index funds |
| 1.5 | 50% more volatile than market | Tech stocks |
| > 2 | Very volatile | Speculative stocks |

### Code Example
```python
beta = toolkit.risk.get_beta()
```

---

# Decision Guide

**What do you want to know?** Use this guide to pick the right metric.

## "Is the company profitable?"
Start with:
1. **Net Profit Margin** - Are they making money on sales?
2. **ROE** - Are they generating returns for shareholders?
3. **ROIC** - Are they using capital efficiently?

## "Is the company healthy or at risk?"
Start with:
1. **Altman Z-Score** - Quick bankruptcy risk check
2. **Piotroski F-Score** - Overall financial health (0-9)
3. **DuPont Analysis** - Understand WHY ROE is what it is

## "Is the stock cheap or expensive?"
Start with:
1. **P/E Ratio** - Basic valuation
2. **PEG Ratio** - P/E adjusted for growth
3. **EV/EBITDA** - Valuation accounting for debt

## "How risky is this investment?"
Start with:
1. **Beta** - Volatility vs market
2. **Maximum Drawdown** - Worst historical loss
3. **Sharpe Ratio** - Return per unit of risk

## "Should I compare two companies?"
Use these for side-by-side comparison:
1. Same industry P/E comparison
2. ROE and ROIC comparison
3. Piotroski F-Score comparison

---

# Quick Start Examples

## Full Company Analysis
```python
from financetoolkit import Toolkit

toolkit = Toolkit(['AAPL', 'MSFT'], api_key="YOUR_KEY")

# Profitability
print("=== PROFITABILITY ===")
print(toolkit.ratios.collect_profitability_ratios())

# Health
print("\n=== HEALTH SCORES ===")
print("Altman Z-Score:", toolkit.models.get_altman_z_score())
print("Piotroski F-Score:", toolkit.models.get_piotroski_f_score())

# Valuation
print("\n=== VALUATION ===")
print(toolkit.ratios.collect_valuation_ratios())

# Risk
print("\n=== RISK ===")
print("VaR (95%):", toolkit.risk.get_value_at_risk())
print("Max Drawdown:", toolkit.risk.get_maximum_drawdown())
```

## Compare Two Stocks
```python
toolkit = Toolkit(['AAPL', 'GOOGL'], api_key="YOUR_KEY")

# Side by side comparison
comparison = toolkit.ratios.collect_all_ratios()
print(comparison)
```

---

## Next Steps

1. **Practice with sample data** - See [offline-tutorial.md](offline-tutorial.md)
2. **Get an API key** - Visit [Financial Modeling Prep](https://www.jeroenbouma.com/fmp)
3. **Explore more metrics** - See [quick-reference.md](quick-reference.md) for the full list
4. **Look up terms** - See [glossary.md](glossary.md) for definitions
