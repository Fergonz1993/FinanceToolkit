# Backtesting Engine for FinanceToolkit

A complete framework for testing trading strategies on historical data.

## Features

- Event-driven backtesting engine
- Pre-built strategies (Buy & Hold, MA Crossover, Mean Reversion, Momentum, RSI)
- Custom strategy support
- Transaction costs and commissions
- Comprehensive performance metrics
- Works with FinanceToolkit data or any price DataFrame

---

## Quick Start

```python
from backtesting import BacktestEngine, BuyAndHold
import pandas as pd

# Your price data (or use FinanceToolkit to fetch)
prices = pd.DataFrame({
    'AAPL': [...],
    'MSFT': [...]
}, index=dates)

# Create engine
engine = BacktestEngine(
    data=prices,
    initial_cash=100000,
    commission=0.001  # 0.1%
)

# Create strategy
strategy = BuyAndHold(['AAPL', 'MSFT'])

# Run backtest
results = engine.run(strategy)

# View results
print(results.summary())
```

---

## Pre-Built Strategies

### 1. Buy and Hold
```python
from backtesting import BuyAndHold

strategy = BuyAndHold(
    tickers=['AAPL', 'MSFT', 'GOOGL'],
    weights={'AAPL': 0.4, 'MSFT': 0.4, 'GOOGL': 0.2}
)
```

### 2. Moving Average Crossover
```python
from backtesting import MovingAverageCrossover

strategy = MovingAverageCrossover(
    tickers=['AAPL', 'MSFT'],
    short_window=10,   # 10-day MA
    long_window=30,    # 30-day MA
    position_size=0.3  # 30% per position
)
```

### 3. Mean Reversion
```python
from backtesting import MeanReversion

strategy = MeanReversion(
    tickers=['AAPL'],
    lookback=20,        # 20-day lookback
    entry_zscore=-2.0,  # Buy when 2 std below mean
    exit_zscore=0.0,    # Sell when at mean
    position_size=0.5
)
```

### 4. Momentum
```python
from backtesting import MomentumStrategy

strategy = MomentumStrategy(
    tickers=['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META'],
    lookback=60,       # 60-day momentum
    top_n=3,           # Hold top 3 performers
    rebalance_days=20  # Rebalance monthly
)
```

### 5. RSI
```python
from backtesting import RSIStrategy

strategy = RSIStrategy(
    tickers=['AAPL', 'MSFT'],
    period=14,
    oversold=30,    # Buy when RSI < 30
    overbought=70,  # Sell when RSI > 70
    position_size=0.3
)
```

---

## Custom Strategies

### Option 1: Function-Based
```python
from backtesting import Order, Side

def my_strategy(date, prices, portfolio, engine):
    orders = []

    for ticker in ['AAPL']:
        # Your logic here
        if should_buy:
            quantity = int(portfolio.cash * 0.5 / prices[ticker])
            orders.append(Order(ticker, Side.BUY, quantity))
        elif should_sell:
            position = portfolio.get_position(ticker)
            orders.append(Order(ticker, Side.SELL, position.quantity))

    return orders

results = engine.run(my_strategy)
```

### Option 2: Class-Based
```python
from backtesting import Strategy, Order, Side

class MyStrategy(Strategy):
    def __init__(self, threshold=0.05):
        super().__init__(threshold=threshold)
        self.threshold = threshold

    def generate_signals(self, date, prices, portfolio, engine):
        orders = []
        # Your logic here
        return orders

strategy = MyStrategy(threshold=0.03)
results = engine.run(strategy)
```

---

## Using with FinanceToolkit

```python
from financetoolkit import Toolkit
from backtesting import BacktestEngine, MovingAverageCrossover

# Get real data
toolkit = Toolkit(
    tickers=['AAPL', 'MSFT'],
    api_key="YOUR_API_KEY",
    start_date="2022-01-01"
)

historical = toolkit.get_historical_data()

# Backtest
engine = BacktestEngine(historical, initial_cash=100000)
strategy = MovingAverageCrossover(['AAPL', 'MSFT'], 10, 30)
results = engine.run(strategy)

print(results.summary())
```

---

## Results Analysis

### Summary Statistics
```python
results.summary()
```
Output:
```
╔══════════════════════════════════════════════════════╗
║            BACKTEST RESULTS SUMMARY                  ║
╠══════════════════════════════════════════════════════╣
║  Initial Capital:     $      100,000.00              ║
║  Final Value:         $      125,432.10              ║
║  Total Return:                25.43%                 ║
║  CAGR:                        12.15%                 ║
╠══════════════════════════════════════════════════════╣
║  Volatility (Ann.):           18.52%                 ║
║  Sharpe Ratio:                 0.66                  ║
║  Max Drawdown:               -15.32%                 ║
╠══════════════════════════════════════════════════════╣
║  Total Trades:                   24                  ║
║  Win Rate:                    58.33%                 ║
║  Total Commission:    $          432.10              ║
╚══════════════════════════════════════════════════════╝
```

### Available Metrics
```python
results.total_return      # Total return (decimal)
results.total_return_pct  # Total return (percentage)
results.cagr              # Compound Annual Growth Rate
results.volatility        # Annualized volatility
results.sharpe_ratio      # Sharpe ratio
results.max_drawdown      # Maximum drawdown
results.win_rate          # Win rate of trades
results.num_trades        # Number of trades
results.total_commission  # Total commission paid
```

### Export Data
```python
# Daily values as DataFrame
daily_df = results.to_dataframe()
daily_df.to_csv('backtest_results.csv')

# Plot equity curve (requires matplotlib)
results.plot()
```

---

## Run Examples

```bash
# Run all examples
python backtesting/examples.py
```

---

## Strategy Parameters Reference

| Strategy | Key Parameters |
|----------|---------------|
| BuyAndHold | tickers, weights |
| MovingAverageCrossover | short_window, long_window, position_size |
| MeanReversion | lookback, entry_zscore, exit_zscore, position_size |
| MomentumStrategy | lookback, top_n, rebalance_days |
| RSIStrategy | period, oversold, overbought, position_size |

---

## Tips for Better Backtests

1. **Use realistic commission rates** (0.1% is typical)
2. **Test on out-of-sample data** to avoid overfitting
3. **Compare against buy-and-hold benchmark**
4. **Check max drawdown** - can you stomach that loss?
5. **Consider slippage** for high-frequency strategies
6. **Test across different market conditions** (bull, bear, sideways)
