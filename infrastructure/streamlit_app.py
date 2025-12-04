"""
Streamlit Web App for FinanceToolkit

A user-friendly web interface for financial analysis.

Run with: streamlit run infrastructure/streamlit_app.py
"""

import streamlit as st
import pandas as pd
import os

# Import FinanceToolkit
try:
    from financetoolkit import Toolkit
    TOOLKIT_AVAILABLE = True
except ImportError:
    TOOLKIT_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="FinanceToolkit Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .good { color: #28a745; }
    .warning { color: #ffc107; }
    .bad { color: #dc3545; }
    .stMetric {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)


def interpret_altman(score):
    """Interpret Altman Z-Score."""
    if score is None:
        return "N/A", "gray"
    if score > 2.99:
        return "Safe Zone", "good"
    elif score > 1.81:
        return "Grey Zone", "warning"
    else:
        return "Distress Zone", "bad"


def interpret_piotroski(score):
    """Interpret Piotroski F-Score."""
    if score is None:
        return "N/A", "gray"
    if score >= 8:
        return "Excellent", "good"
    elif score >= 5:
        return "Average", "warning"
    else:
        return "Poor", "bad"


def format_percentage(value):
    """Format value as percentage."""
    if pd.isna(value):
        return "N/A"
    return f"{value * 100:.2f}%"


def format_ratio(value):
    """Format ratio value."""
    if pd.isna(value):
        return "N/A"
    return f"{value:.2f}"


# ============ MAIN APP ============

def main():
    st.title("📊 FinanceToolkit Dashboard")
    st.markdown("*Analyze stocks with 150+ financial metrics*")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        # API Key input
        api_key = st.text_input(
            "FMP API Key",
            value=os.environ.get("FMP_API_KEY", ""),
            type="password",
            help="Get your free API key at financialmodelingprep.com"
        )

        if not api_key:
            st.warning("Enter an API key to analyze stocks")

        st.divider()

        # Ticker input
        ticker_input = st.text_input(
            "Enter Ticker(s)",
            value="AAPL",
            help="Enter one or more tickers separated by commas (e.g., AAPL, MSFT, GOOGL)"
        )

        tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

        # Date range
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=pd.to_datetime("2020-01-01"))
        with col2:
            end_date = st.date_input("End Date", value=pd.to_datetime("today"))

        # Analysis button
        analyze_button = st.button("🔍 Analyze", type="primary", use_container_width=True)

        st.divider()
        st.markdown("### Quick Links")
        st.markdown("[📚 Documentation](./docs/beginners-guide.md)")
        st.markdown("[🔗 GitHub](https://github.com/JerBouma/FinanceToolkit)")

    # Main content
    if not TOOLKIT_AVAILABLE:
        st.error("FinanceToolkit is not installed. Run: `pip install financetoolkit`")
        return

    if not api_key:
        st.info("👈 Enter your FMP API key in the sidebar to get started")

        # Show demo mode
        st.markdown("---")
        st.subheader("📖 What You Can Analyze")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### 📈 Profitability")
            st.markdown("""
            - Gross Margin
            - Net Profit Margin
            - Return on Equity (ROE)
            - Return on Assets (ROA)
            - Return on Invested Capital
            """)

        with col2:
            st.markdown("### 🏥 Health Scores")
            st.markdown("""
            - Altman Z-Score
            - Piotroski F-Score
            - DuPont Analysis
            - Liquidity Ratios
            - Solvency Ratios
            """)

        with col3:
            st.markdown("### 💰 Valuation")
            st.markdown("""
            - P/E Ratio
            - P/B Ratio
            - PEG Ratio
            - EV/EBITDA
            - Dividend Yield
            """)

        return

    if analyze_button and tickers:
        try:
            with st.spinner(f"Analyzing {', '.join(tickers)}..."):
                # Create toolkit
                toolkit = Toolkit(
                    tickers=tickers,
                    api_key=api_key,
                    start_date=str(start_date)
                )

                # Store in session state
                st.session_state['toolkit'] = toolkit
                st.session_state['tickers'] = tickers

        except Exception as e:
            st.error(f"Error: {str(e)}")
            return

    # Display results if toolkit is in session
    if 'toolkit' in st.session_state:
        toolkit = st.session_state['toolkit']
        tickers = st.session_state['tickers']

        # Create tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview",
            "📈 Profitability",
            "🏥 Health Scores",
            "💰 Valuation",
            "⚠️ Risk"
        ])

        # ============ TAB 1: OVERVIEW ============
        with tab1:
            st.header("Company Overview")

            for ticker in tickers:
                st.subheader(f"🏢 {ticker}")

                try:
                    # Get key metrics
                    profitability = toolkit.ratios.collect_profitability_ratios()
                    altman = toolkit.models.get_altman_z_score()
                    piotroski = toolkit.models.get_piotroski_f_score()

                    # Latest period
                    latest_period = profitability.columns[-1] if not profitability.empty else "N/A"

                    # Extract values
                    altman_val = float(altman.loc[ticker].iloc[-1]) if ticker in altman.index else None
                    piotroski_val = int(piotroski.loc[ticker].iloc[-1]) if ticker in piotroski.index else None

                    # Display metrics in columns
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        try:
                            roe = profitability.loc[(ticker, 'Return on Equity'), latest_period]
                            st.metric("ROE", format_percentage(roe))
                        except:
                            st.metric("ROE", "N/A")

                    with col2:
                        try:
                            net_margin = profitability.loc[(ticker, 'Net Profit Margin'), latest_period]
                            st.metric("Net Margin", format_percentage(net_margin))
                        except:
                            st.metric("Net Margin", "N/A")

                    with col3:
                        interpretation, color = interpret_altman(altman_val)
                        st.metric(
                            "Altman Z-Score",
                            f"{altman_val:.2f}" if altman_val else "N/A",
                            delta=interpretation
                        )

                    with col4:
                        interpretation, color = interpret_piotroski(piotroski_val)
                        st.metric(
                            "Piotroski F-Score",
                            f"{piotroski_val}/9" if piotroski_val else "N/A",
                            delta=interpretation
                        )

                    st.divider()

                except Exception as e:
                    st.error(f"Error analyzing {ticker}: {str(e)}")

        # ============ TAB 2: PROFITABILITY ============
        with tab2:
            st.header("Profitability Ratios")
            st.markdown("*How good is the company at making money?*")

            try:
                profitability = toolkit.ratios.collect_profitability_ratios()

                if not profitability.empty:
                    # Display as table
                    st.dataframe(
                        profitability.style.format("{:.2%}"),
                        use_container_width=True
                    )

                    # Key metrics explanation
                    with st.expander("📖 What these metrics mean"):
                        st.markdown("""
                        | Metric | Meaning | Good Value |
                        |--------|---------|------------|
                        | **Gross Margin** | % of revenue after production costs | > 40% |
                        | **Net Profit Margin** | % of revenue that becomes profit | > 15% |
                        | **ROE** | Return generated on shareholder equity | > 15% |
                        | **ROA** | Return generated on total assets | > 10% |
                        | **ROIC** | Return on all invested capital | > 12% |
                        """)

                else:
                    st.warning("No profitability data available")

            except Exception as e:
                st.error(f"Error: {str(e)}")

        # ============ TAB 3: HEALTH SCORES ============
        with tab3:
            st.header("Financial Health Scores")

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📊 Altman Z-Score")
                st.markdown("*Bankruptcy prediction model*")

                try:
                    altman = toolkit.models.get_altman_z_score()

                    if not altman.empty:
                        for ticker in tickers:
                            if ticker in altman.index:
                                score = float(altman.loc[ticker].iloc[-1])
                                interpretation, color = interpret_altman(score)

                                st.metric(
                                    ticker,
                                    f"{score:.2f}",
                                    delta=interpretation
                                )

                        st.markdown("""
                        **Interpretation:**
                        - **> 2.99**: Safe Zone (low risk)
                        - **1.81 - 2.99**: Grey Zone (monitor)
                        - **< 1.81**: Distress Zone (high risk)
                        """)

                        # Show historical trend
                        st.line_chart(altman.T)

                except Exception as e:
                    st.error(f"Error: {str(e)}")

            with col2:
                st.subheader("📊 Piotroski F-Score")
                st.markdown("*Financial strength score (0-9)*")

                try:
                    piotroski = toolkit.models.get_piotroski_f_score()

                    if not piotroski.empty:
                        for ticker in tickers:
                            if ticker in piotroski.index:
                                score = int(piotroski.loc[ticker].iloc[-1])
                                interpretation, color = interpret_piotroski(score)

                                st.metric(
                                    ticker,
                                    f"{score}/9",
                                    delta=interpretation
                                )

                        st.markdown("""
                        **Interpretation:**
                        - **8-9**: Excellent health
                        - **5-7**: Average
                        - **0-4**: Poor health
                        """)

                        # Show bar chart
                        st.bar_chart(piotroski.T)

                except Exception as e:
                    st.error(f"Error: {str(e)}")

            # DuPont Analysis
            st.divider()
            st.subheader("🔍 DuPont Analysis")
            st.markdown("*Breaking down ROE into components*")

            try:
                dupont = toolkit.models.get_dupont_analysis()

                if not dupont.empty:
                    st.dataframe(dupont.style.format("{:.2%}"), use_container_width=True)

                    st.info("""
                    **ROE = Net Margin × Asset Turnover × Equity Multiplier**

                    - High Net Margin = Strong profitability
                    - High Asset Turnover = Efficient use of assets
                    - High Equity Multiplier = Using more debt (risky)
                    """)

            except Exception as e:
                st.error(f"Error: {str(e)}")

        # ============ TAB 4: VALUATION ============
        with tab4:
            st.header("Valuation Metrics")
            st.markdown("*Is the stock cheap or expensive?*")

            try:
                valuation = toolkit.ratios.collect_valuation_ratios()

                if not valuation.empty:
                    st.dataframe(
                        valuation.style.format("{:.2f}"),
                        use_container_width=True
                    )

                    # Key metrics explanation
                    with st.expander("📖 What these metrics mean"):
                        st.markdown("""
                        | Metric | Meaning | Cheap | Expensive |
                        |--------|---------|-------|-----------|
                        | **P/E Ratio** | Price per $1 of earnings | < 15 | > 25 |
                        | **P/B Ratio** | Price vs book value | < 1 | > 3 |
                        | **PEG Ratio** | P/E adjusted for growth | < 1 | > 2 |
                        | **EV/EBITDA** | Enterprise value vs operating profit | < 8 | > 12 |
                        """)

                else:
                    st.warning("No valuation data available")

            except Exception as e:
                st.error(f"Error: {str(e)}")

        # ============ TAB 5: RISK ============
        with tab5:
            st.header("Risk Metrics")
            st.markdown("*How risky is this investment?*")

            try:
                # Get historical data for risk calculations
                historical = toolkit.get_historical_data()

                if not historical.empty:
                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("📉 Value at Risk (VaR)")
                        var = toolkit.risk.get_value_at_risk()

                        if hasattr(var, 'to_dict'):
                            st.dataframe(var.style.format("{:.2%}"))
                        else:
                            st.metric("Daily VaR (95%)", format_percentage(var))

                        st.info("VaR shows the maximum expected loss on 95% of days")

                    with col2:
                        st.subheader("📊 Maximum Drawdown")
                        max_dd = toolkit.risk.get_maximum_drawdown()

                        if hasattr(max_dd, 'to_dict'):
                            st.dataframe(max_dd.style.format("{:.2%}"))
                        else:
                            st.metric("Max Drawdown", format_percentage(max_dd))

                        st.info("Maximum peak-to-trough decline in history")

                    # Price chart
                    st.subheader("📈 Price History")
                    if len(tickers) == 1:
                        st.line_chart(historical[tickers[0]]['Close'])
                    else:
                        # Multi-ticker chart
                        close_prices = pd.DataFrame({
                            t: historical[t]['Close'] for t in tickers if t in historical.columns.get_level_values(0)
                        })
                        st.line_chart(close_prices)

                else:
                    st.warning("No historical data available for risk calculations")

            except Exception as e:
                st.error(f"Error: {str(e)}")

    else:
        st.info("👈 Enter ticker(s) and click Analyze to get started")


# ============ RUN APP ============
if __name__ == "__main__":
    main()
