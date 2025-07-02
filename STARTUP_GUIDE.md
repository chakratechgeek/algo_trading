# 🚀 Algo Trading Platform - Clean Startup Guide

## 📋 Project Status ✅
- ✅ Database migrations applied
- ✅ Models configured and working
- ✅ Small-cap trading strategy implemented 
- ✅ Admin interface setup
- ✅ Automated 10-minute scheduler ready
- ✅ All import issues resolved
- ✅ Unused files cleaned up

## 🎯 Super Quick Start

### Option 1: Use Startup Script (Recommended)
```bash
python start.py
```
Then select:
- **Option 1**: Start Django Server Only
- **Option 2**: Test Small-Cap Strategy  
- **Option 3**: Start Automated Scheduler (10-min intervals)
- **Option 4**: Start Server + Open Admin automatically
- **Option 5**: Create Test Data

### Option 2: Manual Commands

#### Start Django Server
```bash
python manage.py runserver
```

#### Run Small-Cap Strategy
```bash
python manage.py run_small_cap_strategy
```

#### Start Automated Trading (Every 10 minutes)
```bash
python manage.py start_scheduler --interval 10 --market-hours-only --weekdays-only
```

## 🌐 Access Points

### Django Admin Dashboard
- **URL**: http://127.0.0.1:8000/admin/
- **Login**: admin / admin123
- **Real-time monitoring**: Trading Signals, Executions, Portfolio Balance

### Key Admin Sections
- **Trading → Trading Signals**: See all buy/sell signals generated
- **Trading → Trading Executions**: Monitor actual trades
- **Portfolio → Portfolios**: Check balance and positions
- **Trading → Trading Strategies**: View strategy performance

## 📊 How the 10-Minute Automation Works

### Schedule
- **Frequency**: Every 10 minutes
- **Active Hours**: 9:15 AM - 3:30 PM IST (Market hours only)
- **Days**: Monday to Friday (Weekdays only)
- **Auto-skip**: Weekends and after-hours

### Strategy Logic
1. **Balance Check**: Gets current portfolio balance from `portfolio_portfolio.current_balance`
2. **Symbol Fetch**: Retrieves small-cap stocks in ₹75-150 price range
3. **Position Analysis**: Checks existing positions for ±2 INR sell triggers
4. **Buy Decisions**: Uses LLM analysis for new purchases (always 20 shares each)
5. **Record Keeping**: Saves all transactions to database tables

### Database Tables Used
- **Balance**: `portfolio_portfolio.current_balance`
- **Positions**: `portfolio_position` (current holdings)
- **Trades**: `portfolio_trade` (all buy/sell records)
- **Signals**: `trading_tradingsignal` (strategy decisions)

## � Real-Time Progress Monitoring

### Command Line Output
```bash
[SCHEDULER] Starting automated trading scheduler...
[SCHEDULER] Running small-cap strategy for active portfolios...
[SMALLCAP] Starting small-cap strategy for portfolio: Test Portfolio
[BALANCE] Current balance: ₹25,000.00
[SYMBOLS] Found 12 small-cap symbols in price range ₹75-150
[BUY SIGNAL] Created for SYMPHONY - 20 shares @ ₹140 = ₹2,800
[POSITION] TESTCAP1: Current ₹87, Purchase ₹83, Change ₹4.00
[SELL DECISION] TESTCAP1: ±2 INR rule triggered
```

### Django Admin Live View
1. **Go to**: Admin → Trading → Trading Signals
2. **Refresh**: Page auto-updates with new signals
3. **Filter**: By date to see today's activity
4. **Details**: Click individual signals for full analysis

## 🎮 Testing & Verification

### 1. Quick Test
```bash
python start.py
# Select Option 2: Test Small-Cap Strategy
```

### 2. View Results
- Open admin dashboard
- Check Trading Signals section
- Verify portfolio balance updates

### 3. Start Live Trading
```bash
python start.py  
# Select Option 3: Start Automated Scheduler
```

## 🛠️ Configuration

### Strategy Settings (trading_platform/settings.py)
```python
SMALL_CAP_CONFIG = {
    'MIN_PRICE': 75,           # Minimum stock price ₹75
    'MAX_PRICE': 150,          # Maximum stock price ₹150
    'PRICE_CHANGE_THRESHOLD': 2.0,  # ±2 rupees sell trigger
    'MIN_AI_CONFIDENCE': 60,   # Minimum LLM confidence for trades
}
```

### Scheduler Settings
- **Interval**: 10 minutes (configurable)
- **Market Hours**: 9:15 AM - 3:30 PM IST
- **Trading Days**: Monday-Friday only

## � Troubleshooting

### No Trading Signals Generated
- ✅ Check: Market hours (9:15 AM - 3:30 PM IST)
- ✅ Check: Portfolio balance > 0
- ✅ Check: Symbols in database
- ✅ Check: Weekday (not weekend)

### Admin Login Issues
```bash
python manage.py createsuperuser
# Create: admin / admin123
```

### Database Issues
```bash
python manage.py migrate
```

## 📈 Success Indicators

### ✅ Working Correctly When You See:
- Trading signals appearing in admin every 10 minutes during market hours
- Portfolio balance decreasing when buys are made
- Positions being created in portfolio section
- ±2 INR rule triggering sell signals for existing positions
- Exactly 20 shares purchased per buy signal

---

## 🎯 Ready to Trade!

Your algo trading platform is **fully cleaned up** and ready for automated small-cap trading with:
- ✅ **10-minute automated execution**
- ✅ **Real-time progress monitoring** 
- ✅ **Clean, error-free codebase**
- ✅ **Production-ready structure**

**Start now with**: `python start.py`
