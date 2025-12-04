"""
Telegram Bot for FinanceToolkit

Query financial data via Telegram chat.

Setup:
1. Create a bot with @BotFather on Telegram
2. Get your bot token
3. Set environment variables:
   - TELEGRAM_BOT_TOKEN=your_bot_token
   - FMP_API_KEY=your_fmp_key
4. Run: python infrastructure/telegram_bot.py
"""

import os
import logging
from typing import Optional

# Telegram library
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application,
        CommandHandler,
        MessageHandler,
        CallbackQueryHandler,
        ContextTypes,
        filters
    )
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("Install python-telegram-bot: pip install python-telegram-bot")

# FinanceToolkit
try:
    from financetoolkit import Toolkit
    TOOLKIT_AVAILABLE = True
except ImportError:
    TOOLKIT_AVAILABLE = False

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
FMP_API_KEY = os.environ.get("FMP_API_KEY", "")


def get_toolkit(ticker: str) -> Optional[Toolkit]:
    """Create a Toolkit instance for a single ticker."""
    if not TOOLKIT_AVAILABLE:
        return None
    if not FMP_API_KEY:
        return None

    try:
        return Toolkit(
            tickers=[ticker.upper()],
            api_key=FMP_API_KEY,
            start_date="2020-01-01"
        )
    except Exception as e:
        logger.error(f"Error creating toolkit: {e}")
        return None


def format_number(value, is_percentage=False):
    """Format numbers for display."""
    if value is None:
        return "N/A"
    try:
        if is_percentage:
            return f"{float(value) * 100:.2f}%"
        return f"{float(value):.2f}"
    except:
        return "N/A"


def interpret_altman(score):
    """Interpret Altman Z-Score."""
    if score is None:
        return "N/A"
    if score > 2.99:
        return "✅ Safe Zone (low bankruptcy risk)"
    elif score > 1.81:
        return "⚠️ Grey Zone (moderate risk)"
    else:
        return "🔴 Distress Zone (high risk)"


def interpret_piotroski(score):
    """Interpret Piotroski F-Score."""
    if score is None:
        return "N/A"
    if score >= 8:
        return "✅ Excellent financial health"
    elif score >= 5:
        return "⚠️ Average financial health"
    else:
        return "🔴 Poor financial health"


# ============ COMMAND HANDLERS ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    welcome_message = """
🤖 *FinanceToolkit Bot*

I can analyze stocks and provide financial metrics!

*Commands:*
/analyze AAPL - Full analysis of a stock
/health AAPL - Health scores (Altman & Piotroski)
/ratios AAPL - Key financial ratios
/compare AAPL MSFT - Compare two stocks
/help - Show all commands

Just type a ticker symbol to get a quick overview!

_Powered by FinanceToolkit_
"""
    await update.message.reply_text(welcome_message, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = """
📚 *Available Commands*

*Analysis Commands:*
/analyze TICKER - Comprehensive analysis
/health TICKER - Altman Z-Score & Piotroski F-Score
/ratios TICKER - Profitability & valuation ratios
/valuation TICKER - P/E, P/B, PEG ratios
/risk TICKER - Risk metrics (VaR, drawdown)

*Comparison:*
/compare TICKER1 TICKER2 - Side-by-side comparison

*Other:*
/help - This help message
/status - Check bot status

*Quick Access:*
Just type a ticker (e.g., AAPL) for a quick overview!

_Examples:_
`/analyze AAPL`
`/health MSFT`
`/compare AAPL GOOGL`
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command."""
    status_text = f"""
🔧 *Bot Status*

• Telegram: ✅ Connected
• FinanceToolkit: {"✅ Installed" if TOOLKIT_AVAILABLE else "❌ Not installed"}
• FMP API Key: {"✅ Configured" if FMP_API_KEY else "❌ Not set"}
"""
    await update.message.reply_text(status_text, parse_mode='Markdown')


async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /analyze command - comprehensive analysis."""
    if not context.args:
        await update.message.reply_text("Usage: /analyze TICKER\nExample: /analyze AAPL")
        return

    ticker = context.args[0].upper()
    await update.message.reply_text(f"🔍 Analyzing {ticker}...")

    toolkit = get_toolkit(ticker)
    if not toolkit:
        await update.message.reply_text("❌ Error: Could not initialize toolkit. Check API key.")
        return

    try:
        # Get data
        profitability = toolkit.ratios.collect_profitability_ratios()
        altman = toolkit.models.get_altman_z_score()
        piotroski = toolkit.models.get_piotroski_f_score()
        valuation = toolkit.ratios.collect_valuation_ratios()

        # Extract latest values
        latest = profitability.columns[-1] if not profitability.empty else "N/A"

        # Build response
        response = f"""
📊 *{ticker} Analysis*
_Period: {latest}_

*💰 Profitability*
• Gross Margin: {format_number(profitability.loc[(ticker, 'Gross Margin'), latest] if (ticker, 'Gross Margin') in profitability.index else None, True)}
• Net Margin: {format_number(profitability.loc[(ticker, 'Net Profit Margin'), latest] if (ticker, 'Net Profit Margin') in profitability.index else None, True)}
• ROE: {format_number(profitability.loc[(ticker, 'Return on Equity'), latest] if (ticker, 'Return on Equity') in profitability.index else None, True)}
• ROA: {format_number(profitability.loc[(ticker, 'Return on Assets'), latest] if (ticker, 'Return on Assets') in profitability.index else None, True)}

*🏥 Health Scores*
• Altman Z-Score: {format_number(altman.loc[ticker].iloc[-1] if ticker in altman.index else None)}
  {interpret_altman(altman.loc[ticker].iloc[-1] if ticker in altman.index else None)}
• Piotroski F-Score: {int(piotroski.loc[ticker].iloc[-1]) if ticker in piotroski.index else 'N/A'}/9
  {interpret_piotroski(int(piotroski.loc[ticker].iloc[-1]) if ticker in piotroski.index else None)}

*💵 Valuation*
• P/E Ratio: {format_number(valuation.loc[(ticker, 'Price-to-Earnings'), latest] if (ticker, 'Price-to-Earnings') in valuation.index else None)}
• P/B Ratio: {format_number(valuation.loc[(ticker, 'Price-to-Book'), latest] if (ticker, 'Price-to-Book') in valuation.index else None)}
"""
        await update.message.reply_text(response, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Error analyzing {ticker}: {e}")
        await update.message.reply_text(f"❌ Error analyzing {ticker}: {str(e)}")


async def health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /health command - health scores only."""
    if not context.args:
        await update.message.reply_text("Usage: /health TICKER\nExample: /health AAPL")
        return

    ticker = context.args[0].upper()
    await update.message.reply_text(f"🏥 Getting health scores for {ticker}...")

    toolkit = get_toolkit(ticker)
    if not toolkit:
        await update.message.reply_text("❌ Error: Could not initialize toolkit.")
        return

    try:
        altman = toolkit.models.get_altman_z_score()
        piotroski = toolkit.models.get_piotroski_f_score()

        altman_val = float(altman.loc[ticker].iloc[-1]) if ticker in altman.index else None
        piotroski_val = int(piotroski.loc[ticker].iloc[-1]) if ticker in piotroski.index else None

        response = f"""
🏥 *{ticker} Health Scores*

*Altman Z-Score: {format_number(altman_val)}*
{interpret_altman(altman_val)}

_Interpretation:_
• > 2.99: Safe Zone
• 1.81-2.99: Grey Zone
• < 1.81: Distress Zone

---

*Piotroski F-Score: {piotroski_val}/9*
{interpret_piotroski(piotroski_val)}

_Interpretation:_
• 8-9: Excellent
• 5-7: Average
• 0-4: Poor
"""
        await update.message.reply_text(response, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def ratios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ratios command."""
    if not context.args:
        await update.message.reply_text("Usage: /ratios TICKER\nExample: /ratios AAPL")
        return

    ticker = context.args[0].upper()
    await update.message.reply_text(f"📊 Getting ratios for {ticker}...")

    toolkit = get_toolkit(ticker)
    if not toolkit:
        await update.message.reply_text("❌ Error: Could not initialize toolkit.")
        return

    try:
        profitability = toolkit.ratios.collect_profitability_ratios()
        latest = profitability.columns[-1] if not profitability.empty else "N/A"

        # Get specific ratios
        metrics = [
            ('Gross Margin', True),
            ('Operating Margin', True),
            ('Net Profit Margin', True),
            ('Return on Assets', True),
            ('Return on Equity', True),
            ('Return on Invested Capital', True),
        ]

        lines = [f"📊 *{ticker} Profitability Ratios*\n_Period: {latest}_\n"]

        for metric, is_pct in metrics:
            try:
                val = profitability.loc[(ticker, metric), latest]
                lines.append(f"• {metric}: {format_number(val, is_pct)}")
            except:
                lines.append(f"• {metric}: N/A")

        await update.message.reply_text('\n'.join(lines), parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def valuation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /valuation command."""
    if not context.args:
        await update.message.reply_text("Usage: /valuation TICKER\nExample: /valuation AAPL")
        return

    ticker = context.args[0].upper()
    await update.message.reply_text(f"💰 Getting valuation for {ticker}...")

    toolkit = get_toolkit(ticker)
    if not toolkit:
        await update.message.reply_text("❌ Error: Could not initialize toolkit.")
        return

    try:
        val_ratios = toolkit.ratios.collect_valuation_ratios()
        latest = val_ratios.columns[-1] if not val_ratios.empty else "N/A"

        response = f"""
💰 *{ticker} Valuation Metrics*
_Period: {latest}_

• P/E Ratio: {format_number(val_ratios.loc[(ticker, 'Price-to-Earnings'), latest] if (ticker, 'Price-to-Earnings') in val_ratios.index else None)}
• P/B Ratio: {format_number(val_ratios.loc[(ticker, 'Price-to-Book'), latest] if (ticker, 'Price-to-Book') in val_ratios.index else None)}
• P/S Ratio: {format_number(val_ratios.loc[(ticker, 'Price-to-Sales'), latest] if (ticker, 'Price-to-Sales') in val_ratios.index else None)}
• EV/EBITDA: {format_number(val_ratios.loc[(ticker, 'EV-to-EBITDA'), latest] if (ticker, 'EV-to-EBITDA') in val_ratios.index else None)}

_Interpretation:_
• P/E < 15: Cheap | > 25: Expensive
• P/B < 1: Cheap | > 3: Expensive
• EV/EBITDA < 8: Cheap | > 12: Expensive
"""
        await update.message.reply_text(response, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def compare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /compare command."""
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /compare TICKER1 TICKER2\nExample: /compare AAPL MSFT")
        return

    ticker1 = context.args[0].upper()
    ticker2 = context.args[1].upper()

    await update.message.reply_text(f"📊 Comparing {ticker1} vs {ticker2}...")

    if not FMP_API_KEY:
        await update.message.reply_text("❌ Error: API key not configured.")
        return

    try:
        toolkit = Toolkit(
            tickers=[ticker1, ticker2],
            api_key=FMP_API_KEY,
            start_date="2020-01-01"
        )

        profitability = toolkit.ratios.collect_profitability_ratios()
        altman = toolkit.models.get_altman_z_score()
        piotroski = toolkit.models.get_piotroski_f_score()

        latest = profitability.columns[-1] if not profitability.empty else "N/A"

        def get_val(df, ticker, metric):
            try:
                return df.loc[(ticker, metric), latest]
            except:
                return None

        response = f"""
⚔️ *{ticker1} vs {ticker2}*
_Period: {latest}_

*Metric* | *{ticker1}* | *{ticker2}*
━━━━━━━━━━━━━━━━━━━━━━
Net Margin | {format_number(get_val(profitability, ticker1, 'Net Profit Margin'), True)} | {format_number(get_val(profitability, ticker2, 'Net Profit Margin'), True)}
ROE | {format_number(get_val(profitability, ticker1, 'Return on Equity'), True)} | {format_number(get_val(profitability, ticker2, 'Return on Equity'), True)}
ROA | {format_number(get_val(profitability, ticker1, 'Return on Assets'), True)} | {format_number(get_val(profitability, ticker2, 'Return on Assets'), True)}
Altman Z | {format_number(altman.loc[ticker1].iloc[-1] if ticker1 in altman.index else None)} | {format_number(altman.loc[ticker2].iloc[-1] if ticker2 in altman.index else None)}
F-Score | {int(piotroski.loc[ticker1].iloc[-1]) if ticker1 in piotroski.index else 'N/A'} | {int(piotroski.loc[ticker2].iloc[-1]) if ticker2 in piotroski.index else 'N/A'}
"""
        await update.message.reply_text(response, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


async def handle_ticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plain ticker input (quick overview)."""
    text = update.message.text.strip().upper()

    # Check if it looks like a ticker (1-5 uppercase letters)
    if len(text) <= 5 and text.isalpha():
        await update.message.reply_text(f"🔍 Quick lookup for {text}...")

        toolkit = get_toolkit(text)
        if not toolkit:
            await update.message.reply_text("❌ Could not fetch data. Check if ticker is valid.")
            return

        try:
            altman = toolkit.models.get_altman_z_score()
            piotroski = toolkit.models.get_piotroski_f_score()

            altman_val = float(altman.loc[text].iloc[-1]) if text in altman.index else None
            piotroski_val = int(piotroski.loc[text].iloc[-1]) if text in piotroski.index else None

            response = f"""
📊 *{text} Quick Overview*

• Altman Z-Score: {format_number(altman_val)} {interpret_altman(altman_val).split()[0]}
• Piotroski F-Score: {piotroski_val}/9 {interpret_piotroski(piotroski_val).split()[0]}

_Use /analyze {text} for full analysis_
"""
            # Add inline keyboard for more options
            keyboard = [
                [
                    InlineKeyboardButton("📊 Full Analysis", callback_data=f"analyze_{text}"),
                    InlineKeyboardButton("🏥 Health", callback_data=f"health_{text}"),
                ],
                [
                    InlineKeyboardButton("💰 Valuation", callback_data=f"valuation_{text}"),
                    InlineKeyboardButton("📈 Ratios", callback_data=f"ratios_{text}"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(response, parse_mode='Markdown', reply_markup=reply_markup)

        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button callbacks."""
    query = update.callback_query
    await query.answer()

    data = query.data
    action, ticker = data.split('_', 1)

    # Simulate the appropriate command
    context.args = [ticker]

    if action == "analyze":
        await analyze(update, context)
    elif action == "health":
        await health(update, context)
    elif action == "valuation":
        await valuation(update, context)
    elif action == "ratios":
        await ratios(update, context)


def main():
    """Start the bot."""
    if not TELEGRAM_AVAILABLE:
        print("❌ python-telegram-bot not installed")
        print("Run: pip install python-telegram-bot")
        return

    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN environment variable not set")
        print("Get a token from @BotFather on Telegram")
        return

    if not FMP_API_KEY:
        print("⚠️ FMP_API_KEY not set - bot will have limited functionality")

    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("analyze", analyze))
    application.add_handler(CommandHandler("health", health))
    application.add_handler(CommandHandler("ratios", ratios))
    application.add_handler(CommandHandler("valuation", valuation))
    application.add_handler(CommandHandler("compare", compare))

    # Handle inline buttons
    application.add_handler(CallbackQueryHandler(button_callback))

    # Handle plain text (ticker lookups)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ticker))

    # Start polling
    print("🤖 FinanceToolkit Bot starting...")
    print(f"API Key configured: {'✅' if FMP_API_KEY else '❌'}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
