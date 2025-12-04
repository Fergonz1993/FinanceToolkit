"""
Strategy Framework for Backtesting

Pre-built strategies and tools for creating custom strategies.

Strategies:
- BuyAndHold: Simple buy and hold
- MovingAverageCrossover: MA cross signals
- MeanReversion: Buy dips, sell rallies
- MomentumStrategy: Follow trends
- ValueStrategy: Based on fundamental ratios
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np

from .engine import Order, Side, Portfolio, BacktestEngine


class Strategy(ABC):
    """
    Base class for all strategies.

    Subclass this to create custom strategies.

    Example:
        class MyStrategy(Strategy):
            def generate_signals(self, date, prices, portfolio, engine):
                # Your logic
                return [Order(...)]
    """

    def __init__(self, **params):
        """Initialize with parameters."""
        self.params = params

    @abstractmethod
    def generate_signals(
        self,
        date,
        prices: Dict[str, float],
        portfolio: Portfolio,
        engine: BacktestEngine
    ) -> List[Order]:
        """
        Generate trading signals for current date.

        Args:
            date: Current date
            prices: Dict of ticker -> current price
            portfolio: Current portfolio state
            engine: Backtest engine (for historical data access)

        Returns:
            List of Order objects
        """
        pass

    def __call__(self, date, prices, portfolio, engine) -> List[Order]:
        """Make strategy callable."""
        return self.generate_signals(date, prices, portfolio, engine)


class BuyAndHold(Strategy):
    """
    Simple buy and hold strategy.

    Buys specified tickers on first day and holds forever.

    Params:
        tickers: List of tickers to buy
        weights: Optional dict of ticker -> weight (default: equal weight)
    """

    def __init__(self, tickers: List[str], weights: Optional[Dict[str, float]] = None):
        super().__init__(tickers=tickers, weights=weights)
        self.tickers = tickers
        self.weights = weights or {t: 1/len(tickers) for t in tickers}
        self.bought = False

    def generate_signals(self, date, prices, portfolio, engine) -> List[Order]:
        if self.bought:
            return []

        orders = []
        total_cash = portfolio.cash

        for ticker in self.tickers:
            if ticker in prices:
                weight = self.weights.get(ticker, 1/len(self.tickers))
                amount = total_cash * weight
                quantity = int(amount / prices[ticker])
                if quantity > 0:
                    orders.append(Order(ticker, Side.BUY, quantity))

        self.bought = True
        return orders


class MovingAverageCrossover(Strategy):
    """
    Moving Average Crossover Strategy.

    Buys when short MA crosses above long MA.
    Sells when short MA crosses below long MA.

    Params:
        tickers: List of tickers to trade
        short_window: Short moving average period (default: 20)
        long_window: Long moving average period (default: 50)
        position_size: Fraction of portfolio per position (default: 0.2)
    """

    def __init__(
        self,
        tickers: List[str],
        short_window: int = 20,
        long_window: int = 50,
        position_size: float = 0.2
    ):
        super().__init__(
            tickers=tickers,
            short_window=short_window,
            long_window=long_window,
            position_size=position_size
        )
        self.tickers = tickers
        self.short_window = short_window
        self.long_window = long_window
        self.position_size = position_size
        self.prev_signals = {}

    def generate_signals(self, date, prices, portfolio, engine) -> List[Order]:
        orders = []

        # Get historical data
        lookback = engine.get_lookback(date, self.long_window + 1)

        if len(lookback) < self.long_window:
            return []  # Not enough data

        for ticker in self.tickers:
            if ticker not in lookback.columns:
                continue

            ticker_data = lookback[ticker]

            # Calculate MAs
            short_ma = ticker_data.rolling(self.short_window).mean().iloc[-1]
            long_ma = ticker_data.rolling(self.long_window).mean().iloc[-1]
            prev_short_ma = ticker_data.rolling(self.short_window).mean().iloc[-2]
            prev_long_ma = ticker_data.rolling(self.long_window).mean().iloc[-2]

            if pd.isna(short_ma) or pd.isna(long_ma):
                continue

            # Detect crossover
            current_signal = short_ma > long_ma
            prev_signal = prev_short_ma > prev_long_ma

            position = portfolio.get_position(ticker)
            current_price = prices.get(ticker, 0)

            # Buy signal: short crosses above long
            if current_signal and not prev_signal:
                if position.quantity == 0:
                    amount = portfolio.cash * self.position_size
                    quantity = int(amount / current_price)
                    if quantity > 0:
                        orders.append(Order(ticker, Side.BUY, quantity))

            # Sell signal: short crosses below long
            elif not current_signal and prev_signal:
                if position.quantity > 0:
                    orders.append(Order(ticker, Side.SELL, position.quantity))

        return orders


class MeanReversion(Strategy):
    """
    Mean Reversion Strategy.

    Buys when price is N standard deviations below moving average.
    Sells when price returns to moving average.

    Params:
        tickers: List of tickers to trade
        lookback: Period for calculating mean and std (default: 20)
        entry_zscore: Z-score for entry (default: -2.0)
        exit_zscore: Z-score for exit (default: 0.0)
        position_size: Fraction of portfolio per position (default: 0.2)
    """

    def __init__(
        self,
        tickers: List[str],
        lookback: int = 20,
        entry_zscore: float = -2.0,
        exit_zscore: float = 0.0,
        position_size: float = 0.2
    ):
        super().__init__(
            tickers=tickers,
            lookback=lookback,
            entry_zscore=entry_zscore,
            exit_zscore=exit_zscore,
            position_size=position_size
        )
        self.tickers = tickers
        self.lookback = lookback
        self.entry_zscore = entry_zscore
        self.exit_zscore = exit_zscore
        self.position_size = position_size

    def generate_signals(self, date, prices, portfolio, engine) -> List[Order]:
        orders = []

        lookback_data = engine.get_lookback(date, self.lookback + 1)

        if len(lookback_data) < self.lookback:
            return []

        for ticker in self.tickers:
            if ticker not in lookback_data.columns:
                continue

            ticker_data = lookback_data[ticker]
            current_price = prices.get(ticker, 0)

            # Calculate z-score
            mean = ticker_data.mean()
            std = ticker_data.std()

            if std == 0:
                continue

            zscore = (current_price - mean) / std
            position = portfolio.get_position(ticker)

            # Entry: price is oversold
            if zscore <= self.entry_zscore and position.quantity == 0:
                amount = portfolio.cash * self.position_size
                quantity = int(amount / current_price)
                if quantity > 0:
                    orders.append(Order(ticker, Side.BUY, quantity))

            # Exit: price reverted to mean
            elif zscore >= self.exit_zscore and position.quantity > 0:
                orders.append(Order(ticker, Side.SELL, position.quantity))

        return orders


class MomentumStrategy(Strategy):
    """
    Momentum Strategy.

    Buys top N performers over lookback period.
    Rebalances periodically.

    Params:
        tickers: Universe of tickers to consider
        lookback: Period for measuring momentum (default: 60 days)
        top_n: Number of top performers to hold (default: 3)
        rebalance_days: Days between rebalancing (default: 20)
    """

    def __init__(
        self,
        tickers: List[str],
        lookback: int = 60,
        top_n: int = 3,
        rebalance_days: int = 20
    ):
        super().__init__(
            tickers=tickers,
            lookback=lookback,
            top_n=top_n,
            rebalance_days=rebalance_days
        )
        self.tickers = tickers
        self.lookback = lookback
        self.top_n = top_n
        self.rebalance_days = rebalance_days
        self.days_since_rebalance = 0
        self.current_holdings = set()

    def generate_signals(self, date, prices, portfolio, engine) -> List[Order]:
        self.days_since_rebalance += 1

        # Only rebalance on schedule
        if self.days_since_rebalance < self.rebalance_days:
            return []

        self.days_since_rebalance = 0
        orders = []

        # Get lookback data
        lookback_data = engine.get_lookback(date, self.lookback + 1)

        if len(lookback_data) < self.lookback:
            return []

        # Calculate momentum (return over period)
        momentum = {}
        for ticker in self.tickers:
            if ticker in lookback_data.columns:
                start_price = lookback_data[ticker].iloc[0]
                end_price = lookback_data[ticker].iloc[-1]
                if start_price > 0:
                    momentum[ticker] = (end_price - start_price) / start_price

        # Rank and select top N
        sorted_momentum = sorted(momentum.items(), key=lambda x: x[1], reverse=True)
        top_tickers = set(t for t, _ in sorted_momentum[:self.top_n])

        # Sell tickers no longer in top N
        for ticker in self.current_holdings - top_tickers:
            position = portfolio.get_position(ticker)
            if position.quantity > 0:
                orders.append(Order(ticker, Side.SELL, position.quantity))

        # Buy new top tickers
        for ticker in top_tickers - self.current_holdings:
            if ticker in prices:
                amount = portfolio.cash / self.top_n
                quantity = int(amount / prices[ticker])
                if quantity > 0:
                    orders.append(Order(ticker, Side.BUY, quantity))

        self.current_holdings = top_tickers
        return orders


class ValueStrategy(Strategy):
    """
    Value-Based Strategy using FinanceToolkit ratios.

    Buys stocks with attractive valuations (low P/E, high Piotroski).
    Requires pre-computed fundamental data.

    Params:
        fundamental_data: Dict of ticker -> {metric: value}
        max_pe: Maximum P/E ratio to consider (default: 15)
        min_piotroski: Minimum Piotroski F-Score (default: 7)
        position_size: Fraction of portfolio per position (default: 0.1)
    """

    def __init__(
        self,
        fundamental_data: Dict[str, Dict[str, float]],
        max_pe: float = 15,
        min_piotroski: int = 7,
        position_size: float = 0.1
    ):
        super().__init__(
            max_pe=max_pe,
            min_piotroski=min_piotroski,
            position_size=position_size
        )
        self.fundamental_data = fundamental_data
        self.max_pe = max_pe
        self.min_piotroski = min_piotroski
        self.position_size = position_size
        self.bought = False

    def generate_signals(self, date, prices, portfolio, engine) -> List[Order]:
        # Only buy once at start
        if self.bought:
            return []

        orders = []

        # Filter stocks by fundamental criteria
        buy_candidates = []
        for ticker, data in self.fundamental_data.items():
            pe = data.get('pe_ratio', float('inf'))
            piotroski = data.get('piotroski_f_score', 0)

            if pe <= self.max_pe and piotroski >= self.min_piotroski:
                buy_candidates.append(ticker)

        # Buy qualifying stocks
        for ticker in buy_candidates:
            if ticker in prices:
                amount = portfolio.cash * self.position_size
                quantity = int(amount / prices[ticker])
                if quantity > 0:
                    orders.append(Order(ticker, Side.BUY, quantity))

        self.bought = True
        return orders


class RSIStrategy(Strategy):
    """
    RSI (Relative Strength Index) Strategy.

    Buys when RSI is oversold, sells when overbought.

    Params:
        tickers: List of tickers to trade
        period: RSI calculation period (default: 14)
        oversold: RSI level for buy signal (default: 30)
        overbought: RSI level for sell signal (default: 70)
        position_size: Fraction of portfolio per position (default: 0.2)
    """

    def __init__(
        self,
        tickers: List[str],
        period: int = 14,
        oversold: float = 30,
        overbought: float = 70,
        position_size: float = 0.2
    ):
        super().__init__(
            tickers=tickers,
            period=period,
            oversold=oversold,
            overbought=overbought,
            position_size=position_size
        )
        self.tickers = tickers
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.position_size = position_size

    def _calculate_rsi(self, prices: pd.Series) -> float:
        """Calculate RSI for a price series."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]

    def generate_signals(self, date, prices, portfolio, engine) -> List[Order]:
        orders = []

        lookback_data = engine.get_lookback(date, self.period + 5)

        if len(lookback_data) < self.period + 1:
            return []

        for ticker in self.tickers:
            if ticker not in lookback_data.columns:
                continue

            ticker_data = lookback_data[ticker]
            rsi = self._calculate_rsi(ticker_data)

            if pd.isna(rsi):
                continue

            position = portfolio.get_position(ticker)
            current_price = prices.get(ticker, 0)

            # Buy when oversold
            if rsi <= self.oversold and position.quantity == 0:
                amount = portfolio.cash * self.position_size
                quantity = int(amount / current_price)
                if quantity > 0:
                    orders.append(Order(ticker, Side.BUY, quantity))

            # Sell when overbought
            elif rsi >= self.overbought and position.quantity > 0:
                orders.append(Order(ticker, Side.SELL, position.quantity))

        return orders


# ============ STRATEGY COMBINERS ============

class CombinedStrategy(Strategy):
    """
    Combine multiple strategies.

    Only generates orders when multiple strategies agree.

    Params:
        strategies: List of Strategy instances
        require_all: If True, all strategies must agree (default: False)
        min_agree: Minimum strategies that must agree (default: 2)
    """

    def __init__(
        self,
        strategies: List[Strategy],
        require_all: bool = False,
        min_agree: int = 2
    ):
        super().__init__(strategies=strategies, require_all=require_all, min_agree=min_agree)
        self.strategies = strategies
        self.require_all = require_all
        self.min_agree = min_agree

    def generate_signals(self, date, prices, portfolio, engine) -> List[Order]:
        # Collect signals from all strategies
        all_orders = {}  # ticker -> {Side.BUY: count, Side.SELL: count}

        for strategy in self.strategies:
            orders = strategy.generate_signals(date, prices, portfolio, engine)
            for order in orders:
                if order.ticker not in all_orders:
                    all_orders[order.ticker] = {Side.BUY: 0, Side.SELL: 0}
                all_orders[order.ticker][order.side] += 1

        # Filter orders by agreement threshold
        final_orders = []
        threshold = len(self.strategies) if self.require_all else self.min_agree

        for ticker, sides in all_orders.items():
            if sides[Side.BUY] >= threshold:
                # Find largest quantity suggestion
                quantity = max(
                    o.quantity for s in self.strategies
                    for o in s.generate_signals(date, prices, portfolio, engine)
                    if o.ticker == ticker and o.side == Side.BUY
                )
                final_orders.append(Order(ticker, Side.BUY, quantity))

            elif sides[Side.SELL] >= threshold:
                position = portfolio.get_position(ticker)
                if position.quantity > 0:
                    final_orders.append(Order(ticker, Side.SELL, position.quantity))

        return final_orders


# ============ HELPER FUNCTIONS ============

def create_strategy_from_rules(rules: Dict[str, Any]) -> Strategy:
    """
    Create a strategy from a dictionary of rules.

    Example:
        rules = {
            'type': 'moving_average_crossover',
            'tickers': ['AAPL', 'MSFT'],
            'short_window': 10,
            'long_window': 30
        }
        strategy = create_strategy_from_rules(rules)
    """
    strategy_map = {
        'buy_and_hold': BuyAndHold,
        'moving_average_crossover': MovingAverageCrossover,
        'mean_reversion': MeanReversion,
        'momentum': MomentumStrategy,
        'rsi': RSIStrategy,
    }

    strategy_type = rules.pop('type', 'buy_and_hold')

    if strategy_type not in strategy_map:
        raise ValueError(f"Unknown strategy type: {strategy_type}")

    return strategy_map[strategy_type](**rules)
