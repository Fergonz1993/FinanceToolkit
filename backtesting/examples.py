"""
Backtesting Examples

Complete examples demonstrating how to use the backtesting engine.

Run: python backtesting/examples.py
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backtesting.engine import BacktestEngine, Order, Side
from backtesting.strategies import (
    BuyAndHold,
    MovingAverageCrossover,
    MeanReversion,
    MomentumStrategy,
    RSIStrategy
)


def generate_sample_data(
    tickers: list,
    start_date: str = "2020-01-01",
    end_date: str = "2023-12-31",
    seed: int = 42
) -> pd.DataFrame:
    """Generate synthetic price data for testing."""
    np.random.seed(seed)

    dates = pd.date_range(start_date, end_date, freq='B')  # Business days

    data = {}
    base_prices = {'AAPL': 150, 'MSFT': 300, 'GOOGL': 2500, 'AMZN': 3000, 'META': 200}

    for ticker in tickers:
        base = base_prices.get(ticker, 100)
        # Random walk with drift
        returns = np.random.randn(len(dates)) * 0.02 + 0.0003  # ~0.03% daily drift
        prices = base * (1 + returns).cumprod()
        data[ticker] = prices

    return pd.DataFrame(data, index=dates)


def example_buy_and_hold():
    """Example 1: Simple Buy and Hold Strategy."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Buy and Hold Strategy")
    print("="*60)

    # Generate data
    tickers = ['AAPL', 'MSFT', 'GOOGL']
    prices = generate_sample_data(tickers)

    # Create engine
    engine = BacktestEngine(
        data=prices,
        initial_cash=100000,
        commission=0.001  # 0.1%
    )

    # Create strategy
    strategy = BuyAndHold(
        tickers=tickers,
        weights={'AAPL': 0.4, 'MSFT': 0.4, 'GOOGL': 0.2}
    )

    # Run backtest
    results = engine.run(strategy)

    print(results.summary())

    return results


def example_moving_average():
    """Example 2: Moving Average Crossover Strategy."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Moving Average Crossover Strategy")
    print("="*60)

    # Generate data
    tickers = ['AAPL', 'MSFT']
    prices = generate_sample_data(tickers)

    # Create engine
    engine = BacktestEngine(
        data=prices,
        initial_cash=100000,
        commission=0.001
    )

    # Create strategy: 10-day vs 30-day MA
    strategy = MovingAverageCrossover(
        tickers=tickers,
        short_window=10,
        long_window=30,
        position_size=0.4  # 40% of portfolio per position
    )

    # Run backtest
    results = engine.run(strategy, verbose=True)

    print(results.summary())

    return results


def example_mean_reversion():
    """Example 3: Mean Reversion Strategy."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Mean Reversion Strategy")
    print("="*60)

    # Generate data
    tickers = ['AAPL']
    prices = generate_sample_data(tickers)

    # Create engine
    engine = BacktestEngine(
        data=prices,
        initial_cash=100000,
        commission=0.001
    )

    # Create strategy
    strategy = MeanReversion(
        tickers=tickers,
        lookback=20,
        entry_zscore=-1.5,  # Buy when 1.5 std below mean
        exit_zscore=0.5,    # Sell when 0.5 std above mean
        position_size=0.5
    )

    # Run backtest
    results = engine.run(strategy, verbose=True)

    print(results.summary())

    return results


def example_momentum():
    """Example 4: Momentum Strategy."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Momentum Strategy")
    print("="*60)

    # Generate data - larger universe
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']
    prices = generate_sample_data(tickers)

    # Create engine
    engine = BacktestEngine(
        data=prices,
        initial_cash=100000,
        commission=0.001
    )

    # Create strategy: Hold top 2 performers
    strategy = MomentumStrategy(
        tickers=tickers,
        lookback=60,      # 60-day momentum
        top_n=2,          # Hold top 2
        rebalance_days=20 # Rebalance monthly
    )

    # Run backtest
    results = engine.run(strategy, verbose=True)

    print(results.summary())

    return results


def example_rsi():
    """Example 5: RSI Strategy."""
    print("\n" + "="*60)
    print("EXAMPLE 5: RSI Strategy")
    print("="*60)

    # Generate data
    tickers = ['AAPL', 'MSFT']
    prices = generate_sample_data(tickers)

    # Create engine
    engine = BacktestEngine(
        data=prices,
        initial_cash=100000,
        commission=0.001
    )

    # Create strategy
    strategy = RSIStrategy(
        tickers=tickers,
        period=14,
        oversold=30,   # Buy when RSI < 30
        overbought=70, # Sell when RSI > 70
        position_size=0.3
    )

    # Run backtest
    results = engine.run(strategy, verbose=True)

    print(results.summary())

    return results


def example_custom_strategy():
    """Example 6: Custom Strategy Function."""
    print("\n" + "="*60)
    print("EXAMPLE 6: Custom Strategy (Simple SMA)")
    print("="*60)

    # Generate data
    tickers = ['AAPL']
    prices = generate_sample_data(tickers)

    # Create engine
    engine = BacktestEngine(
        data=prices,
        initial_cash=100000,
        commission=0.001
    )

    # Define custom strategy as function
    def simple_sma_strategy(date, prices, portfolio, engine):
        """Buy when price > 20-day SMA, sell when below."""
        orders = []

        lookback = engine.get_lookback(date, 21)
        if len(lookback) < 20:
            return []

        for ticker in ['AAPL']:
            if ticker not in lookback.columns:
                continue

            sma = lookback[ticker].rolling(20).mean().iloc[-1]
            price = prices.get(ticker, 0)
            position = portfolio.get_position(ticker)

            if price > sma and position.quantity == 0:
                # Buy
                quantity = int(portfolio.cash * 0.9 / price)
                if quantity > 0:
                    orders.append(Order(ticker, Side.BUY, quantity))
            elif price < sma and position.quantity > 0:
                # Sell
                orders.append(Order(ticker, Side.SELL, position.quantity))

        return orders

    # Run backtest
    results = engine.run(simple_sma_strategy, verbose=True)

    print(results.summary())

    return results


def example_with_financetoolkit():
    """Example 7: Using Real Data from FinanceToolkit."""
    print("\n" + "="*60)
    print("EXAMPLE 7: Using FinanceToolkit Data")
    print("="*60)

    try:
        import os
        from financetoolkit import Toolkit

        api_key = os.environ.get('FMP_API_KEY')
        if not api_key:
            print("⚠️  FMP_API_KEY not set. Using sample data instead.")
            return example_buy_and_hold()

        print("Fetching real data from FinanceToolkit...")

        # Get real historical data
        toolkit = Toolkit(
            tickers=['AAPL', 'MSFT'],
            api_key=api_key,
            start_date="2022-01-01"
        )

        historical = toolkit.get_historical_data()

        # Create engine with real data
        engine = BacktestEngine(
            data=historical,
            initial_cash=100000,
            commission=0.001
        )

        # Use Moving Average strategy
        strategy = MovingAverageCrossover(
            tickers=['AAPL', 'MSFT'],
            short_window=10,
            long_window=30,
            position_size=0.4
        )

        # Run backtest
        results = engine.run(strategy, verbose=True)

        print(results.summary())

        return results

    except ImportError:
        print("FinanceToolkit not installed. Using sample data.")
        return example_buy_and_hold()
    except Exception as e:
        print(f"Error: {e}")
        print("Using sample data instead.")
        return example_buy_and_hold()


def compare_strategies():
    """Compare multiple strategies on same data."""
    print("\n" + "="*60)
    print("STRATEGY COMPARISON")
    print("="*60)

    # Generate data
    tickers = ['AAPL', 'MSFT', 'GOOGL']
    prices = generate_sample_data(tickers)

    strategies = {
        'Buy & Hold': BuyAndHold(tickers),
        'MA Crossover': MovingAverageCrossover(tickers, 10, 30, 0.3),
        'Mean Reversion': MeanReversion(tickers, 20, -1.5, 0.5, 0.3),
        'RSI': RSIStrategy(tickers, 14, 30, 70, 0.3),
    }

    results_summary = []

    for name, strategy in strategies.items():
        engine = BacktestEngine(prices, initial_cash=100000)

        # Need to reset strategy state
        if hasattr(strategy, 'bought'):
            strategy.bought = False
        if hasattr(strategy, 'current_holdings'):
            strategy.current_holdings = set()
        if hasattr(strategy, 'days_since_rebalance'):
            strategy.days_since_rebalance = 0

        results = engine.run(strategy)

        results_summary.append({
            'Strategy': name,
            'Total Return': f"{results.total_return_pct:.2f}%",
            'CAGR': f"{results.cagr * 100:.2f}%",
            'Sharpe': f"{results.sharpe_ratio:.2f}",
            'Max DD': f"{results.max_drawdown_pct:.2f}%",
            'Trades': results.num_trades
        })

    # Display comparison
    comparison_df = pd.DataFrame(results_summary)
    print("\n")
    print(comparison_df.to_string(index=False))

    return comparison_df


def main():
    """Run all examples."""
    print("╔══════════════════════════════════════════════════════╗")
    print("║         BACKTESTING ENGINE EXAMPLES                  ║")
    print("╚══════════════════════════════════════════════════════╝")

    # Run examples
    example_buy_and_hold()
    example_moving_average()
    example_mean_reversion()
    example_momentum()
    example_rsi()
    example_custom_strategy()
    example_with_financetoolkit()

    # Strategy comparison
    compare_strategies()

    print("\n" + "="*60)
    print("All examples completed!")
    print("="*60)


if __name__ == "__main__":
    main()
