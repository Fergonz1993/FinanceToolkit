"""
Backtesting Engine for FinanceToolkit

A framework for testing trading strategies on historical data.

Features:
- Event-driven backtesting
- Multiple strategy support
- Transaction costs
- Portfolio tracking
- Performance metrics
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, Callable
from datetime import datetime
from enum import Enum


class OrderType(Enum):
    """Types of orders."""
    MARKET = "market"
    LIMIT = "limit"


class Side(Enum):
    """Order side."""
    BUY = "buy"
    SELL = "sell"


@dataclass
class Order:
    """Represents a trading order."""
    ticker: str
    side: Side
    quantity: int
    order_type: OrderType = OrderType.MARKET
    limit_price: Optional[float] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class Trade:
    """Represents an executed trade."""
    ticker: str
    side: Side
    quantity: int
    price: float
    timestamp: datetime
    commission: float = 0.0

    @property
    def value(self) -> float:
        """Total value of trade (including commission)."""
        base_value = self.quantity * self.price
        if self.side == Side.BUY:
            return base_value + self.commission
        return base_value - self.commission


@dataclass
class Position:
    """Represents a position in a security."""
    ticker: str
    quantity: int = 0
    avg_cost: float = 0.0

    @property
    def market_value(self) -> float:
        """Current market value (needs current price)."""
        return 0  # Updated by portfolio

    def update(self, trade: Trade):
        """Update position based on trade."""
        if trade.side == Side.BUY:
            # Update average cost
            total_cost = (self.quantity * self.avg_cost) + (trade.quantity * trade.price)
            self.quantity += trade.quantity
            if self.quantity > 0:
                self.avg_cost = total_cost / self.quantity
        else:
            self.quantity -= trade.quantity
            if self.quantity <= 0:
                self.quantity = 0
                self.avg_cost = 0.0


@dataclass
class Portfolio:
    """Manages portfolio state during backtest."""
    initial_cash: float = 100000.0
    cash: float = field(init=False)
    positions: dict = field(default_factory=dict)
    trades: list = field(default_factory=list)
    commission_rate: float = 0.001  # 0.1% per trade

    def __post_init__(self):
        self.cash = self.initial_cash

    def get_position(self, ticker: str) -> Position:
        """Get or create position for ticker."""
        if ticker not in self.positions:
            self.positions[ticker] = Position(ticker=ticker)
        return self.positions[ticker]

    def execute_order(self, order: Order, current_price: float) -> Optional[Trade]:
        """Execute an order at current price."""
        # Check if order can be filled
        if order.order_type == OrderType.LIMIT:
            if order.side == Side.BUY and current_price > order.limit_price:
                return None
            if order.side == Side.SELL and current_price < order.limit_price:
                return None

        # Calculate commission
        trade_value = order.quantity * current_price
        commission = trade_value * self.commission_rate

        # Check cash for buys
        if order.side == Side.BUY:
            total_cost = trade_value + commission
            if total_cost > self.cash:
                # Reduce quantity to fit cash
                max_quantity = int((self.cash - commission) / current_price)
                if max_quantity <= 0:
                    return None
                order.quantity = max_quantity
                trade_value = order.quantity * current_price
                commission = trade_value * self.commission_rate

        # Check position for sells
        if order.side == Side.SELL:
            position = self.get_position(order.ticker)
            if order.quantity > position.quantity:
                order.quantity = position.quantity
            if order.quantity <= 0:
                return None

        # Create trade
        trade = Trade(
            ticker=order.ticker,
            side=order.side,
            quantity=order.quantity,
            price=current_price,
            timestamp=order.timestamp,
            commission=commission
        )

        # Update cash
        if order.side == Side.BUY:
            self.cash -= trade.value
        else:
            self.cash += trade.value

        # Update position
        position = self.get_position(order.ticker)
        position.update(trade)

        # Record trade
        self.trades.append(trade)

        return trade

    def get_total_value(self, prices: dict) -> float:
        """Get total portfolio value at given prices."""
        total = self.cash
        for ticker, position in self.positions.items():
            if ticker in prices and position.quantity > 0:
                total += position.quantity * prices[ticker]
        return total

    def get_positions_value(self, prices: dict) -> float:
        """Get total value of positions."""
        total = 0
        for ticker, position in self.positions.items():
            if ticker in prices and position.quantity > 0:
                total += position.quantity * prices[ticker]
        return total


class BacktestEngine:
    """
    Main backtesting engine.

    Usage:
        engine = BacktestEngine(
            data=historical_prices_df,
            initial_cash=100000,
            commission=0.001
        )

        # Define strategy
        def my_strategy(date, prices, portfolio, data):
            # Your logic here
            return [Order(...)]

        # Run backtest
        results = engine.run(my_strategy)

        # Analyze results
        print(results.summary())
    """

    def __init__(
        self,
        data: pd.DataFrame,
        initial_cash: float = 100000.0,
        commission: float = 0.001,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        """
        Initialize backtesting engine.

        Args:
            data: DataFrame with price data. Expected format:
                  - Index: DatetimeIndex
                  - Columns: MultiIndex with (Ticker, 'Close'/'Open'/etc.)
                  OR simple columns with ticker names (assumes Close prices)
            initial_cash: Starting capital
            commission: Commission rate (0.001 = 0.1%)
            start_date: Optional start date for backtest
            end_date: Optional end date for backtest
        """
        self.raw_data = data
        self.initial_cash = initial_cash
        self.commission = commission

        # Process data
        self._process_data(start_date, end_date)

    def _process_data(self, start_date, end_date):
        """Process input data into standard format."""
        data = self.raw_data.copy()

        # Handle date filtering
        if start_date:
            data = data[data.index >= start_date]
        if end_date:
            data = data[data.index <= end_date]

        # Ensure datetime index
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)

        # Extract close prices
        if isinstance(data.columns, pd.MultiIndex):
            # MultiIndex columns - extract Close prices
            tickers = data.columns.get_level_values(0).unique()
            close_data = pd.DataFrame(index=data.index)
            for ticker in tickers:
                if (ticker, 'Close') in data.columns:
                    close_data[ticker] = data[(ticker, 'Close')]
                elif (ticker, 'Adj Close') in data.columns:
                    close_data[ticker] = data[(ticker, 'Adj Close')]
            self.prices = close_data
        else:
            # Simple columns
            self.prices = data

        self.tickers = list(self.prices.columns)
        self.dates = list(self.prices.index)

    def run(
        self,
        strategy: Callable,
        verbose: bool = False
    ) -> 'BacktestResults':
        """
        Run backtest with given strategy.

        Args:
            strategy: Strategy function with signature:
                     strategy(date, prices, portfolio, engine) -> List[Order]
            verbose: Print progress

        Returns:
            BacktestResults object with performance data
        """
        # Initialize portfolio
        portfolio = Portfolio(
            initial_cash=self.initial_cash,
            commission_rate=self.commission
        )

        # Track daily values
        daily_values = []
        daily_cash = []
        daily_positions_value = []

        # Run through each day
        for i, date in enumerate(self.dates):
            # Get current prices
            current_prices = self.prices.loc[date].to_dict()

            # Get strategy signals
            orders = strategy(
                date=date,
                prices=current_prices,
                portfolio=portfolio,
                engine=self
            )

            # Execute orders
            if orders:
                for order in orders:
                    if order.ticker in current_prices:
                        price = current_prices[order.ticker]
                        trade = portfolio.execute_order(order, price)

                        if verbose and trade:
                            print(f"{date}: {trade.side.value.upper()} {trade.quantity} "
                                  f"{trade.ticker} @ ${trade.price:.2f}")

            # Record daily values
            total_value = portfolio.get_total_value(current_prices)
            daily_values.append({
                'date': date,
                'total_value': total_value,
                'cash': portfolio.cash,
                'positions_value': portfolio.get_positions_value(current_prices)
            })

        # Create results
        return BacktestResults(
            portfolio=portfolio,
            daily_values=pd.DataFrame(daily_values).set_index('date'),
            initial_cash=self.initial_cash,
            tickers=self.tickers,
            prices=self.prices
        )

    def get_lookback(self, date: datetime, periods: int) -> pd.DataFrame:
        """Get historical data up to given date."""
        idx = self.dates.index(date) if date in self.dates else 0
        start_idx = max(0, idx - periods)
        return self.prices.iloc[start_idx:idx + 1]


@dataclass
class BacktestResults:
    """Results from a backtest run."""
    portfolio: Portfolio
    daily_values: pd.DataFrame
    initial_cash: float
    tickers: list
    prices: pd.DataFrame

    @property
    def total_return(self) -> float:
        """Total return as decimal."""
        final = self.daily_values['total_value'].iloc[-1]
        return (final - self.initial_cash) / self.initial_cash

    @property
    def total_return_pct(self) -> float:
        """Total return as percentage."""
        return self.total_return * 100

    @property
    def cagr(self) -> float:
        """Compound Annual Growth Rate."""
        final = self.daily_values['total_value'].iloc[-1]
        days = len(self.daily_values)
        years = days / 252
        if years <= 0:
            return 0
        return (final / self.initial_cash) ** (1 / years) - 1

    @property
    def daily_returns(self) -> pd.Series:
        """Daily returns series."""
        return self.daily_values['total_value'].pct_change().dropna()

    @property
    def volatility(self) -> float:
        """Annualized volatility."""
        return self.daily_returns.std() * np.sqrt(252)

    @property
    def sharpe_ratio(self) -> float:
        """Sharpe ratio (assuming 0% risk-free rate)."""
        if self.volatility == 0:
            return 0
        return self.cagr / self.volatility

    @property
    def max_drawdown(self) -> float:
        """Maximum drawdown."""
        values = self.daily_values['total_value']
        peak = values.expanding(min_periods=1).max()
        drawdown = (values - peak) / peak
        return drawdown.min()

    @property
    def max_drawdown_pct(self) -> float:
        """Maximum drawdown as percentage."""
        return self.max_drawdown * 100

    @property
    def win_rate(self) -> float:
        """Percentage of winning trades."""
        if not self.portfolio.trades:
            return 0

        # Group trades by ticker
        trades_by_ticker = {}
        for trade in self.portfolio.trades:
            if trade.ticker not in trades_by_ticker:
                trades_by_ticker[trade.ticker] = []
            trades_by_ticker[trade.ticker].append(trade)

        # Calculate P&L for round trips
        wins = 0
        total = 0
        for ticker, trades in trades_by_ticker.items():
            cost_basis = 0
            quantity = 0
            for trade in trades:
                if trade.side == Side.BUY:
                    cost_basis += trade.quantity * trade.price
                    quantity += trade.quantity
                else:
                    if quantity > 0:
                        avg_cost = cost_basis / quantity
                        pnl = (trade.price - avg_cost) * trade.quantity
                        if pnl > 0:
                            wins += 1
                        total += 1
                        # Update
                        sold_cost = avg_cost * trade.quantity
                        cost_basis -= sold_cost
                        quantity -= trade.quantity

        return wins / total if total > 0 else 0

    @property
    def num_trades(self) -> int:
        """Total number of trades."""
        return len(self.portfolio.trades)

    @property
    def total_commission(self) -> float:
        """Total commission paid."""
        return sum(t.commission for t in self.portfolio.trades)

    def summary(self) -> str:
        """Generate summary report."""
        return f"""
╔══════════════════════════════════════════════════════╗
║            BACKTEST RESULTS SUMMARY                  ║
╠══════════════════════════════════════════════════════╣
║  Initial Capital:     ${self.initial_cash:>15,.2f}       ║
║  Final Value:         ${self.daily_values['total_value'].iloc[-1]:>15,.2f}       ║
║  Total Return:        {self.total_return_pct:>15.2f}%       ║
║  CAGR:                {self.cagr * 100:>15.2f}%       ║
╠══════════════════════════════════════════════════════╣
║  Volatility (Ann.):   {self.volatility * 100:>15.2f}%       ║
║  Sharpe Ratio:        {self.sharpe_ratio:>15.2f}        ║
║  Max Drawdown:        {self.max_drawdown_pct:>15.2f}%       ║
╠══════════════════════════════════════════════════════╣
║  Total Trades:        {self.num_trades:>15}        ║
║  Win Rate:            {self.win_rate * 100:>15.2f}%       ║
║  Total Commission:    ${self.total_commission:>15,.2f}       ║
╚══════════════════════════════════════════════════════╝
"""

    def to_dataframe(self) -> pd.DataFrame:
        """Export daily values as DataFrame."""
        return self.daily_values.copy()

    def plot(self, benchmark: Optional[pd.Series] = None):
        """
        Plot equity curve.

        Note: Requires matplotlib. Returns figure for customization.
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("Install matplotlib for plotting: pip install matplotlib")
            return None

        fig, axes = plt.subplots(2, 1, figsize=(12, 8), height_ratios=[3, 1])

        # Equity curve
        ax1 = axes[0]
        ax1.plot(self.daily_values.index, self.daily_values['total_value'],
                 label='Portfolio', linewidth=2)

        if benchmark is not None:
            # Normalize benchmark to same starting value
            benchmark_normalized = benchmark / benchmark.iloc[0] * self.initial_cash
            ax1.plot(benchmark_normalized.index, benchmark_normalized,
                     label='Benchmark', linewidth=1, alpha=0.7)

        ax1.set_title('Portfolio Value Over Time')
        ax1.set_ylabel('Value ($)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Drawdown
        ax2 = axes[1]
        values = self.daily_values['total_value']
        peak = values.expanding(min_periods=1).max()
        drawdown = (values - peak) / peak * 100
        ax2.fill_between(drawdown.index, drawdown, 0, alpha=0.3, color='red')
        ax2.set_title('Drawdown')
        ax2.set_ylabel('Drawdown (%)')
        ax2.set_xlabel('Date')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig


if __name__ == "__main__":
    # Quick test with dummy data
    dates = pd.date_range('2023-01-01', '2023-12-31', freq='D')
    np.random.seed(42)

    # Create dummy price data
    prices = pd.DataFrame({
        'AAPL': 150 * (1 + np.random.randn(len(dates)).cumsum() * 0.02),
        'MSFT': 300 * (1 + np.random.randn(len(dates)).cumsum() * 0.02),
    }, index=dates)

    # Simple buy and hold strategy
    def buy_and_hold(date, prices, portfolio, engine):
        if date == engine.dates[0]:
            # Buy on first day
            return [
                Order('AAPL', Side.BUY, 100),
                Order('MSFT', Side.BUY, 50),
            ]
        return []

    # Run backtest
    engine = BacktestEngine(prices, initial_cash=100000)
    results = engine.run(buy_and_hold, verbose=True)

    print(results.summary())
