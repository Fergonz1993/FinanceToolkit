"""
Database Caching Layer for FinanceToolkit

Provides SQLite-based persistent storage for financial data,
reducing API calls and enabling offline analysis.
"""

import sqlite3
import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Any
import pandas as pd


class FinanceDatabase:
    """
    SQLite database for caching financial data.

    Features:
    - Automatic table creation
    - Configurable cache expiration
    - Support for DataFrames, dicts, and JSON
    - Query by ticker, date range, or metric type

    Usage:
        db = FinanceDatabase()

        # Store data
        db.store_financial_data('AAPL', 'balance_sheet', balance_df)

        # Retrieve data
        data = db.get_financial_data('AAPL', 'balance_sheet')

        # Check if data is fresh
        if db.is_cache_valid('AAPL', 'balance_sheet', max_age_days=7):
            data = db.get_financial_data('AAPL', 'balance_sheet')
    """

    def __init__(self, db_path: str = "finance_cache.db"):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._create_tables()

    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        # Main financial data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financial_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                data_type TEXT NOT NULL,
                data BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ticker, data_type)
            )
        """)

        # Ratios cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ratios_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                ratio_name TEXT NOT NULL,
                period TEXT NOT NULL,
                value REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ticker, ratio_name, period)
            )
        """)

        # Historical prices table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historical_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                date TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                adj_close REAL,
                volume INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ticker, date)
            )
        """)

        # Analysis results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                analysis_type TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ticker, analysis_type)
            )
        """)

        # Create indexes for faster queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ticker ON financial_data(ticker)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_data_type ON financial_data(data_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prices_ticker ON historical_prices(ticker)")

        self.conn.commit()

    def store_financial_data(
        self,
        ticker: str,
        data_type: str,
        data: pd.DataFrame | dict
    ) -> bool:
        """
        Store financial data for a ticker.

        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL')
            data_type: Type of data ('balance_sheet', 'income_statement',
                      'cash_flow', 'historical', 'ratios')
            data: DataFrame or dict to store

        Returns:
            True if successful, False otherwise
        """
        try:
            cursor = self.conn.cursor()

            # Serialize data
            if isinstance(data, pd.DataFrame):
                serialized = pickle.dumps(data)
            else:
                serialized = pickle.dumps(data)

            cursor.execute("""
                INSERT OR REPLACE INTO financial_data (ticker, data_type, data, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (ticker.upper(), data_type, serialized))

            self.conn.commit()
            return True

        except Exception as e:
            print(f"Error storing data: {e}")
            return False

    def get_financial_data(
        self,
        ticker: str,
        data_type: str
    ) -> Optional[pd.DataFrame | dict]:
        """
        Retrieve financial data for a ticker.

        Args:
            ticker: Stock ticker symbol
            data_type: Type of data to retrieve

        Returns:
            DataFrame or dict if found, None otherwise
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT data FROM financial_data
                WHERE ticker = ? AND data_type = ?
            """, (ticker.upper(), data_type))

            row = cursor.fetchone()
            if row:
                return pickle.loads(row[0])
            return None

        except Exception as e:
            print(f"Error retrieving data: {e}")
            return None

    def is_cache_valid(
        self,
        ticker: str,
        data_type: str,
        max_age_days: int = 1
    ) -> bool:
        """
        Check if cached data is still valid (not expired).

        Args:
            ticker: Stock ticker symbol
            data_type: Type of data
            max_age_days: Maximum age in days before cache expires

        Returns:
            True if cache exists and is valid, False otherwise
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT updated_at FROM financial_data
                WHERE ticker = ? AND data_type = ?
            """, (ticker.upper(), data_type))

            row = cursor.fetchone()
            if not row:
                return False

            updated_at = datetime.fromisoformat(row[0])
            age = datetime.now() - updated_at

            return age < timedelta(days=max_age_days)

        except Exception as e:
            print(f"Error checking cache: {e}")
            return False

    def store_historical_prices(
        self,
        ticker: str,
        prices_df: pd.DataFrame
    ) -> bool:
        """
        Store historical price data.

        Args:
            ticker: Stock ticker symbol
            prices_df: DataFrame with OHLCV data (index should be dates)

        Returns:
            True if successful
        """
        try:
            cursor = self.conn.cursor()

            for date, row in prices_df.iterrows():
                cursor.execute("""
                    INSERT OR REPLACE INTO historical_prices
                    (ticker, date, open, high, low, close, adj_close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ticker.upper(),
                    str(date),
                    row.get('Open'),
                    row.get('High'),
                    row.get('Low'),
                    row.get('Close'),
                    row.get('Adj Close'),
                    row.get('Volume')
                ))

            self.conn.commit()
            return True

        except Exception as e:
            print(f"Error storing prices: {e}")
            return False

    def get_historical_prices(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Retrieve historical prices for a ticker.

        Args:
            ticker: Stock ticker symbol
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)

        Returns:
            DataFrame with OHLCV data
        """
        try:
            query = """
                SELECT date, open, high, low, close, adj_close, volume
                FROM historical_prices
                WHERE ticker = ?
            """
            params = [ticker.upper()]

            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)

            query += " ORDER BY date"

            df = pd.read_sql_query(query, self.conn, params=params)

            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                df.columns = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']

            return df

        except Exception as e:
            print(f"Error retrieving prices: {e}")
            return pd.DataFrame()

    def store_ratio(
        self,
        ticker: str,
        ratio_name: str,
        period: str,
        value: float
    ) -> bool:
        """
        Store a single ratio value.

        Args:
            ticker: Stock ticker symbol
            ratio_name: Name of the ratio (e.g., 'gross_margin')
            period: Period (e.g., '2023', 'Q1-2024')
            value: Ratio value
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO ratios_cache
                (ticker, ratio_name, period, value)
                VALUES (?, ?, ?, ?)
            """, (ticker.upper(), ratio_name, period, value))

            self.conn.commit()
            return True

        except Exception as e:
            print(f"Error storing ratio: {e}")
            return False

    def get_ratio(
        self,
        ticker: str,
        ratio_name: str,
        period: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Retrieve ratio values for a ticker.

        Args:
            ticker: Stock ticker symbol
            ratio_name: Name of the ratio
            period: Optional specific period

        Returns:
            DataFrame with ratio values by period
        """
        try:
            query = """
                SELECT period, value FROM ratios_cache
                WHERE ticker = ? AND ratio_name = ?
            """
            params = [ticker.upper(), ratio_name]

            if period:
                query += " AND period = ?"
                params.append(period)

            query += " ORDER BY period"

            return pd.read_sql_query(query, self.conn, params=params)

        except Exception as e:
            print(f"Error retrieving ratio: {e}")
            return pd.DataFrame()

    def store_analysis(
        self,
        ticker: str,
        analysis_type: str,
        result: dict
    ) -> bool:
        """
        Store analysis results (Altman Z-Score, Piotroski, etc.).

        Args:
            ticker: Stock ticker symbol
            analysis_type: Type of analysis ('altman_z', 'piotroski_f', 'dupont')
            result: Dictionary with analysis results
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO analysis_results
                (ticker, analysis_type, result_json)
                VALUES (?, ?, ?)
            """, (ticker.upper(), analysis_type, json.dumps(result)))

            self.conn.commit()
            return True

        except Exception as e:
            print(f"Error storing analysis: {e}")
            return False

    def get_analysis(
        self,
        ticker: str,
        analysis_type: str
    ) -> Optional[dict]:
        """
        Retrieve analysis results.

        Args:
            ticker: Stock ticker symbol
            analysis_type: Type of analysis

        Returns:
            Dictionary with analysis results, or None
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT result_json FROM analysis_results
                WHERE ticker = ? AND analysis_type = ?
            """, (ticker.upper(), analysis_type))

            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None

        except Exception as e:
            print(f"Error retrieving analysis: {e}")
            return None

    def list_cached_tickers(self) -> list[str]:
        """Get list of all tickers with cached data."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT ticker FROM financial_data ORDER BY ticker")
        return [row[0] for row in cursor.fetchall()]

    def get_cache_stats(self) -> dict:
        """Get statistics about cached data."""
        cursor = self.conn.cursor()

        stats = {
            "total_tickers": 0,
            "financial_data_entries": 0,
            "historical_price_records": 0,
            "ratio_entries": 0,
            "analysis_entries": 0,
            "database_size_mb": 0
        }

        cursor.execute("SELECT COUNT(DISTINCT ticker) FROM financial_data")
        stats["total_tickers"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM financial_data")
        stats["financial_data_entries"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM historical_prices")
        stats["historical_price_records"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM ratios_cache")
        stats["ratio_entries"] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM analysis_results")
        stats["analysis_entries"] = cursor.fetchone()[0]

        if self.db_path.exists():
            stats["database_size_mb"] = round(self.db_path.stat().st_size / (1024 * 1024), 2)

        return stats

    def clear_cache(self, ticker: Optional[str] = None):
        """
        Clear cached data.

        Args:
            ticker: Optional ticker to clear. If None, clears all data.
        """
        cursor = self.conn.cursor()

        if ticker:
            ticker = ticker.upper()
            cursor.execute("DELETE FROM financial_data WHERE ticker = ?", (ticker,))
            cursor.execute("DELETE FROM historical_prices WHERE ticker = ?", (ticker,))
            cursor.execute("DELETE FROM ratios_cache WHERE ticker = ?", (ticker,))
            cursor.execute("DELETE FROM analysis_results WHERE ticker = ?", (ticker,))
        else:
            cursor.execute("DELETE FROM financial_data")
            cursor.execute("DELETE FROM historical_prices")
            cursor.execute("DELETE FROM ratios_cache")
            cursor.execute("DELETE FROM analysis_results")

        self.conn.commit()

    def close(self):
        """Close database connection."""
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Convenience function for quick caching with Toolkit
def cache_toolkit_data(toolkit, db: FinanceDatabase):
    """
    Cache all data from a Toolkit instance.

    Args:
        toolkit: FinanceToolkit Toolkit instance
        db: FinanceDatabase instance

    Usage:
        from financetoolkit import Toolkit
        from infrastructure.database import FinanceDatabase, cache_toolkit_data

        toolkit = Toolkit(['AAPL', 'MSFT'], api_key="KEY")
        db = FinanceDatabase()
        cache_toolkit_data(toolkit, db)
    """
    for ticker in toolkit._tickers:
        # Cache financial statements
        if hasattr(toolkit, '_balance_sheet_statement') and not toolkit._balance_sheet_statement.empty:
            db.store_financial_data(ticker, 'balance_sheet', toolkit._balance_sheet_statement)

        if hasattr(toolkit, '_income_statement') and not toolkit._income_statement.empty:
            db.store_financial_data(ticker, 'income_statement', toolkit._income_statement)

        if hasattr(toolkit, '_cash_flow_statement') and not toolkit._cash_flow_statement.empty:
            db.store_financial_data(ticker, 'cash_flow', toolkit._cash_flow_statement)

        if hasattr(toolkit, '_historical_data') and not toolkit._historical_data.empty:
            db.store_financial_data(ticker, 'historical', toolkit._historical_data)

    print(f"Cached data for {len(toolkit._tickers)} ticker(s)")


if __name__ == "__main__":
    # Quick test
    db = FinanceDatabase("test_cache.db")

    # Test storing and retrieving
    test_df = pd.DataFrame({
        '2022': [100, 200, 300],
        '2023': [110, 220, 330]
    }, index=['Revenue', 'Expenses', 'Profit'])

    db.store_financial_data('TEST', 'income_statement', test_df)
    retrieved = db.get_financial_data('TEST', 'income_statement')

    print("Stored and retrieved successfully!")
    print(retrieved)
    print("\nCache stats:", db.get_cache_stats())

    db.close()
