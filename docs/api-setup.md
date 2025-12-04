# Getting Your API Keys

Step-by-step guide to set up API access for FinanceToolkit.

---

## Financial Modeling Prep (FMP) API Key

FMP is the primary data source for financial statements, ratios, and company data.

### Step 1: Sign Up

1. Go to: **https://site.financialmodelingprep.com/register**
   - Or use the 15% discount link: https://www.jeroenbouma.com/fmp

2. Create an account with email/password or Google/GitHub

### Step 2: Choose a Plan

| Plan | Price | Limits | Best For |
|------|-------|--------|----------|
| **Free** | $0 | 250 calls/day, 5 years data, US only | Learning, testing |
| **Starter** | $14/mo | 300 calls/min, 30 years data | Personal use |
| **Professional** | $49/mo | Unlimited, all exchanges | Serious analysis |

**Recommendation:** Start with Free plan to learn, upgrade when needed.

### Step 3: Get Your API Key

1. Log in to FMP dashboard
2. Go to **Dashboard** → **API Key**
3. Copy your key (looks like: `abc123def456...`)

### Step 4: Set Up Your Key

**Option A: Environment Variable (Recommended)**
```bash
# Add to ~/.bashrc or ~/.zshrc
export FMP_API_KEY="your_api_key_here"

# Reload shell
source ~/.bashrc
```

**Option B: In Python Code**
```python
from financetoolkit import Toolkit

toolkit = Toolkit(
    tickers=['AAPL'],
    api_key="your_api_key_here"  # Direct in code
)
```

**Option C: .env File**
```bash
# Create .env file in project root
echo 'FMP_API_KEY=your_api_key_here' > .env
```

```python
# Load in Python
import os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('FMP_API_KEY')
```

### Step 5: Test Your Key

```python
from financetoolkit import Toolkit

toolkit = Toolkit(
    tickers=['AAPL'],
    api_key="your_api_key_here"
)

# If this works, your key is valid!
print(toolkit.get_income_statement())
```

---

## Telegram Bot Token (For Telegram Bot)

### Step 1: Create a Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Choose a name (e.g., "My Finance Bot")
4. Choose a username (must end in `bot`, e.g., `myfinance_bot`)

### Step 2: Get Your Token

BotFather will send you a token like:
```
123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

### Step 3: Set Up Token

```bash
export TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
```

### Step 4: Test Your Bot

```bash
python infrastructure/telegram_bot.py
```

Then message your bot on Telegram!

---

## Quick Setup Script

Create this file as `setup_keys.sh`:

```bash
#!/bin/bash

echo "FinanceToolkit API Setup"
echo "========================"

read -p "Enter FMP API Key: " fmp_key
read -p "Enter Telegram Bot Token (or press Enter to skip): " telegram_token

# Add to shell config
echo "" >> ~/.bashrc
echo "# FinanceToolkit API Keys" >> ~/.bashrc
echo "export FMP_API_KEY=\"$fmp_key\"" >> ~/.bashrc

if [ -n "$telegram_token" ]; then
    echo "export TELEGRAM_BOT_TOKEN=\"$telegram_token\"" >> ~/.bashrc
fi

echo ""
echo "Keys added to ~/.bashrc"
echo "Run: source ~/.bashrc"
echo ""
echo "Test with: python -c \"from financetoolkit import Toolkit; print('Success!')\""
```

Run with:
```bash
chmod +x setup_keys.sh
./setup_keys.sh
```

---

## Verify Everything Works

```python
import os

# Check FMP key
fmp_key = os.environ.get('FMP_API_KEY')
print(f"FMP Key: {'✅ Set' if fmp_key else '❌ Not set'}")

# Check Telegram token
telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
print(f"Telegram Token: {'✅ Set' if telegram_token else '❌ Not set (optional)'}")

# Test FMP connection
if fmp_key:
    from financetoolkit import Toolkit
    try:
        toolkit = Toolkit(['AAPL'], api_key=fmp_key)
        income = toolkit.get_income_statement()
        print(f"FMP Connection: ✅ Working ({len(income.columns)} years of data)")
    except Exception as e:
        print(f"FMP Connection: ❌ Error - {e}")
```

---

## Troubleshooting

### "API key invalid"
- Make sure you copied the entire key
- Check for extra spaces
- Regenerate key in FMP dashboard

### "Rate limit exceeded"
- Free plan: 250 calls/day
- Wait 24 hours or upgrade plan

### "No data returned"
- Check ticker is valid (US stocks for free plan)
- Check date range isn't too far back (5 years for free)

### Telegram bot not responding
- Check token is correct
- Make sure bot is running (`python telegram_bot.py`)
- Check you messaged the right bot username
