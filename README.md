# Django Algo Trading Platform

A comprehensive Django-based algorithmic trading platform built for Indian stock markets using Angel One API.

## Features

- **Django-based Architecture**: Scalable web application with REST API
- **Angel One Integration**: Full integration with Angel One trading API
- **Portfolio Management**: Track and manage multiple portfolios
- **Trading Strategies**: Implement and backtest various trading strategies
- **Risk Management**: Built-in risk controls and position sizing
- **Real-time Market Data**: Live market data integration
- **News Analysis**: News sentiment analysis for trading decisions
- **Web Dashboard**: Django admin interface for monitoring and control

## Project Structure

```
├── angel_api/          # Angel One API integration
│   ├── models.py      # API sessions, symbols, market data
│   ├── services.py    # Angel One API service class
│   ├── views.py       # REST API endpoints
│   └── serializers.py # DRF serializers
├── core/              # Core utilities and base models
│   ├── models.py      # Base timestamp model
│   ├── services.py    # Core services
│   └── management/    # Management commands
├── portfolio/         # Portfolio management
│   ├── models.py      # Portfolio, positions, transactions
│   ├── services.py    # Portfolio management logic
│   └── views.py       # Portfolio API endpoints
├── trading/           # Trading strategies and execution
│   ├── models.py      # Strategies, signals, executions
│   ├── services.py    # Trading logic and risk management
│   └── management/    # Trading bot commands
└── trading_platform/  # Django project settings
```

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/chakratechgeek/algo_trading.git
   cd algo_trading
   ```

2. **Setup the project**
   ```bash
   python main.py setup
   ```

3. **Start the Django server**
   ```bash
   python main.py server
   ```

## Quick Start

### 1. Setup
Run the setup command to install dependencies and initialize the database:
```bash
python main.py setup
```

### 2. Configure Angel One API
Add your Angel One credentials in the Django admin:
1. Go to http://127.0.0.1:8000/admin/
2. Login with admin/admin123
3. Add your Angel One credentials in the Angel API section

### 3. Start Trading Bot
```bash
python main.py bot
```

## API Endpoints

### Angel One API
- `GET /api/angel/symbols/` - List all NSE symbols
- `POST /api/angel/auth/` - Authenticate with Angel One
- `GET /api/angel/ltp/<symbol>/` - Get last traded price
- `GET /api/angel/portfolio/` - Get Angel One portfolio
- `POST /api/angel/place-order/` - Place orders

### Portfolio Management
- `GET /api/portfolio/portfolios/` - List portfolios
- `GET /api/portfolio/positions/` - List positions
- `GET /api/portfolio/transactions/` - List transactions

### Trading
- `GET /api/trading/strategies/` - List trading strategies
- `GET /api/trading/signals/` - List trading signals
- `GET /api/trading/bots/` - List trading bots

## Management Commands

### Run Trading Bot
```bash
python manage.py run_trading_bot
```

### Migrate Old Data
```bash
python manage.py migrate_old_data
```

### Check System Status
```bash
python manage.py check_system_status
```

## Environment Variables

Create a `.env` file in the project root:
```env
DEBUG=True
SECRET_KEY=your-secret-key-here
ANGEL_CLIENT_ID=your-angel-client-id
ANGEL_PASSWORD=your-angel-password
ANGEL_TOTP_SECRET=your-totp-secret
```

## Development

### Adding New Trading Strategies

1. Create a new strategy in Django admin
2. Implement strategy logic in `trading/services.py`
3. Configure strategy parameters in the admin interface

### Testing

```bash
python manage.py test
```

### Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

## Deployment

### Production Setup

1. Set `DEBUG=False` in settings
2. Configure proper database (PostgreSQL recommended)
3. Set up Redis for Celery
4. Configure static files serving
5. Set up proper logging

### Docker (Coming Soon)
Docker deployment configuration will be added in future releases.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is for educational purposes only. Trading in financial markets involves substantial risk. Always test strategies thoroughly before using real money.

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation in the `docs/` folder (coming soon)

## Roadmap

- [ ] Advanced backtesting framework
- [ ] Machine learning integration
- [ ] Options trading support
- [ ] Mobile app API
- [ ] Real-time dashboard
- [ ] Paper trading mode
- [ ] Strategy marketplace
