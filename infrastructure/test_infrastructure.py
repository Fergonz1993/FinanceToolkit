"""
Infrastructure Test Script

Run this to verify all components are working correctly.

Usage: python infrastructure/test_infrastructure.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def print_header(title):
    print(f"\n{'='*50}")
    print(f"  {title}")
    print('='*50)


def print_result(name, success, message=""):
    status = "✅" if success else "❌"
    print(f"{status} {name}: {message}")


def test_imports():
    """Test that all required packages are installed."""
    print_header("Testing Package Imports")

    results = {}

    # Core
    try:
        import pandas as pd
        results['pandas'] = (True, f"v{pd.__version__}")
    except ImportError:
        results['pandas'] = (False, "Not installed")

    # FinanceToolkit
    try:
        from financetoolkit import Toolkit
        results['financetoolkit'] = (True, "Installed")
    except ImportError:
        results['financetoolkit'] = (False, "Run: pip install financetoolkit")

    # FastAPI
    try:
        import fastapi
        results['fastapi'] = (True, f"v{fastapi.__version__}")
    except ImportError:
        results['fastapi'] = (False, "Run: pip install fastapi uvicorn")

    # Streamlit
    try:
        import streamlit
        results['streamlit'] = (True, f"v{streamlit.__version__}")
    except ImportError:
        results['streamlit'] = (False, "Run: pip install streamlit")

    # Telegram
    try:
        import telegram
        results['python-telegram-bot'] = (True, f"v{telegram.__version__}")
    except ImportError:
        results['python-telegram-bot'] = (False, "Run: pip install python-telegram-bot")

    for name, (success, msg) in results.items():
        print_result(name, success, msg)

    return all(s for s, _ in results.values())


def test_environment():
    """Test environment variables."""
    print_header("Testing Environment Variables")

    fmp_key = os.environ.get('FMP_API_KEY')
    telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')

    print_result("FMP_API_KEY", bool(fmp_key),
                 f"Set ({len(fmp_key)} chars)" if fmp_key else "Not set - see docs/api-setup.md")
    print_result("TELEGRAM_BOT_TOKEN", bool(telegram_token),
                 "Set" if telegram_token else "Not set (optional)")

    return bool(fmp_key)


def test_database():
    """Test database caching."""
    print_header("Testing Database Cache")

    try:
        from infrastructure.database import FinanceDatabase
        import pandas as pd

        # Create test database
        db = FinanceDatabase(":memory:")  # In-memory for testing

        # Test store and retrieve
        test_df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
        db.store_financial_data('TEST', 'test_data', test_df)
        retrieved = db.get_financial_data('TEST', 'test_data')

        if retrieved is not None and retrieved.equals(test_df):
            print_result("Store/Retrieve", True, "Working")
        else:
            print_result("Store/Retrieve", False, "Data mismatch")
            return False

        # Test cache validity
        valid = db.is_cache_valid('TEST', 'test_data', max_age_days=1)
        print_result("Cache Validity Check", valid, "Working")

        # Test stats
        stats = db.get_cache_stats()
        print_result("Cache Stats", True, f"{stats['financial_data_entries']} entries")

        db.close()
        return True

    except Exception as e:
        print_result("Database", False, str(e))
        return False


def test_api():
    """Test FastAPI endpoints."""
    print_header("Testing REST API")

    try:
        from fastapi.testclient import TestClient
        from infrastructure.api import app

        client = TestClient(app)

        # Test root endpoint
        response = client.get("/")
        print_result("GET /", response.status_code == 200, f"Status {response.status_code}")

        # Test health endpoint
        response = client.get("/api/health")
        print_result("GET /api/health", response.status_code == 200, f"Status {response.status_code}")

        # Test cache stats
        response = client.get("/api/cache/stats")
        print_result("GET /api/cache/stats", response.status_code == 200, f"Status {response.status_code}")

        return True

    except Exception as e:
        print_result("API", False, str(e))
        return False


def test_toolkit_connection():
    """Test actual connection to Financial Modeling Prep."""
    print_header("Testing FinanceToolkit Connection")

    api_key = os.environ.get('FMP_API_KEY')
    if not api_key:
        print_result("Connection Test", False, "No API key set")
        return False

    try:
        from financetoolkit import Toolkit

        print("  Connecting to FMP API...")
        toolkit = Toolkit(
            tickers=['AAPL'],
            api_key=api_key,
            start_date="2023-01-01"
        )

        # Test income statement
        income = toolkit.get_income_statement()
        print_result("Income Statement", not income.empty,
                     f"{len(income.columns)} periods")

        # Test ratios
        ratios = toolkit.ratios.collect_profitability_ratios()
        print_result("Profitability Ratios", not ratios.empty,
                     f"{len(ratios)} metrics")

        # Test health scores
        altman = toolkit.models.get_altman_z_score()
        print_result("Altman Z-Score", not altman.empty,
                     f"Latest: {altman.iloc[0, -1]:.2f}")

        return True

    except Exception as e:
        print_result("Connection", False, str(e))
        return False


def test_sample_data():
    """Test loading sample data for offline use."""
    print_header("Testing Sample Data")

    import pickle

    sample_files = [
        'tests/datasets/balance_dataset.pickle',
        'tests/datasets/income_dataset.pickle',
        'tests/datasets/cash_dataset.pickle',
        'tests/datasets/historical_dataset.pickle',
    ]

    all_found = True
    for filepath in sample_files:
        full_path = Path(__file__).parent.parent / filepath
        if full_path.exists():
            try:
                with open(full_path, 'rb') as f:
                    data = pickle.load(f)
                print_result(filepath.split('/')[-1], True, f"{type(data).__name__}")
            except Exception as e:
                print_result(filepath.split('/')[-1], False, str(e))
                all_found = False
        else:
            print_result(filepath.split('/')[-1], False, "File not found")
            all_found = False

    return all_found


def main():
    """Run all tests."""
    print("\n" + "="*50)
    print("  FinanceToolkit Infrastructure Tests")
    print("="*50)

    results = {}

    # Run tests
    results['imports'] = test_imports()
    results['environment'] = test_environment()
    results['database'] = test_database()
    results['api'] = test_api()
    results['sample_data'] = test_sample_data()

    # Only test connection if API key is set
    if os.environ.get('FMP_API_KEY'):
        results['connection'] = test_toolkit_connection()

    # Summary
    print_header("Summary")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\nTests passed: {passed}/{total}")

    if all(results.values()):
        print("\n✅ All tests passed! Infrastructure is ready.")
        print("\nNext steps:")
        print("  1. Run API: uvicorn infrastructure.api:app --reload")
        print("  2. Run Streamlit: streamlit run infrastructure/streamlit_app.py")
        print("  3. Run Telegram: python infrastructure/telegram_bot.py")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")

        if not results.get('imports', True):
            print("\n📦 Install missing packages:")
            print("   pip install financetoolkit fastapi uvicorn streamlit python-telegram-bot")

        if not results.get('environment', True):
            print("\n🔑 Set up API keys:")
            print("   export FMP_API_KEY='your_key_here'")
            print("   See docs/api-setup.md for details")

    return all(results.values())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
