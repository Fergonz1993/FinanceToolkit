"""
Backtesting Module for FinanceToolkit

A complete framework for testing trading strategies on historical data.

Components:
- engine.py: Core backtesting engine
- strategies.py: Pre-built strategy classes
- examples.py: Usage examples

Quick Start:
    from backtesting import BacktestEngine, BuyAndHold

    # Create engine with price data
    engine = BacktestEngine(prices_df, initial_cash=100000)

    # Create strategy
    strategy = BuyAndHold(['AAPL', 'MSFT'])

    # Run backtest
    results = engine.run(strategy)

    # View results
    print(results.summary())
"""

from .engine import (
    BacktestEngine,
    BacktestResults,
    Order,
    Trade,
    Position,
    Portfolio,
    Side,
    OrderType,
)

from .strategies import (
    Strategy,
    BuyAndHold,
    MovingAverageCrossover,
    MeanReversion,
    MomentumStrategy,
    RSIStrategy,
    ValueStrategy,
    CombinedStrategy,
    create_strategy_from_rules,
)

__all__ = [
    # Engine
    'BacktestEngine',
    'BacktestResults',
    'Order',
    'Trade',
    'Position',
    'Portfolio',
    'Side',
    'OrderType',
    # Strategies
    'Strategy',
    'BuyAndHold',
    'MovingAverageCrossover',
    'MeanReversion',
    'MomentumStrategy',
    'RSIStrategy',
    'ValueStrategy',
    'CombinedStrategy',
    'create_strategy_from_rules',
]
