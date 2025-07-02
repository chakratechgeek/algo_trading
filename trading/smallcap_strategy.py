"""
Small Cap Trading Strategy
========================

Advanced small-cap trading strategy that:
1. Fetches small-cap symbols from Angel One
2. Checks portfolio balance 
3. Filters stocks by price range (75-150 INR)
4. Uses LLM + news analysis for buy/sell decisions
5. Manages existing positions with ±2 INR or LLM-based exits
6. Records detailed transaction history
"""

import logging
import json
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from together import Together

from .models import TradingStrategy, TradingSignal, TradingBot, TradingExecution
from .execution import trading_executor, risk_manager
from angel_api.services import AngelOneAPI
from angel_api.models import NSESymbol, MarketData
from portfolio.models import Portfolio, Position, Trade
from portfolio.services import PortfolioService


class SmallCapTradingStrategy:
    """Advanced small-cap trading strategy with LLM analysis."""
    
    def __init__(self):
        self.logger = logging.getLogger('smallcap_strategy')
        self.angel_api = AngelOneAPI()
        self.portfolio_service = PortfolioService()
        self.llm_client = Together(api_key=settings.LLM_CONFIG['API_KEY'])
        self.config = settings.SMALL_CAP_CONFIG
        
    def run_strategy(self, portfolio: Portfolio):
        """
        Main strategy execution logic.
        
        Args:
            portfolio: Portfolio instance to trade with
        """
        self.logger.info(f"[SMALLCAP] Starting small-cap strategy for portfolio: {portfolio.name}")
        
        try:
            # 1. Get current balance
            current_balance = self._get_portfolio_balance(portfolio)
            self.logger.info(f"[BALANCE] Current balance: ₹{current_balance}")
            
            # 2. Get existing holdings
            existing_holdings = self._get_existing_holdings(portfolio)
            self.logger.info(f"[HOLDINGS] Found {len(existing_holdings)} existing positions")
            
            # 3. Decide strategy based on balance
            if current_balance > 0:
                # Can buy new positions + manage existing
                self.logger.info("[STRATEGY] Balance > 0: Analyzing new buys + managing existing")
                
                # Analyze new buying opportunities
                self._analyze_new_opportunities(portfolio, current_balance)
                
                # Manage existing positions
                self._manage_existing_positions(portfolio, existing_holdings)
                
            else:
                # Only manage existing positions
                self.logger.info("[STRATEGY] Balance <= 0: Only managing existing positions")
                self._manage_existing_positions(portfolio, existing_holdings)
                
        except Exception as e:
            self.logger.error(f"[ERROR] Strategy execution failed: {e}")
            raise
    
    def _get_portfolio_balance(self, portfolio: Portfolio):
        """Get available cash balance from portfolio directly."""
        try:
            # Get balance directly from Portfolio model
            balance = portfolio.current_balance
            self.logger.info(f"[BALANCE] Retrieved from Portfolio.current_balance: ₹{balance}")
            return balance
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to get balance: {e}")
            return Decimal('0')
    
    def _get_existing_holdings(self, portfolio: Portfolio):
        """Get all existing stock holdings."""
        try:
            positions = Position.objects.filter(
                portfolio=portfolio,
                total_quantity__gt=0,
                is_open=True
            ).select_related('symbol')
            
            return list(positions)
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to get holdings: {e}")
            return []
    
    def _analyze_new_opportunities(self, portfolio: Portfolio, available_balance: Decimal):
        """Analyze new small-cap buying opportunities."""
        self.logger.info("[ANALYSIS] Analyzing new small-cap opportunities...")
        
        try:
            # 1. Get small-cap symbols in price range
            smallcap_symbols = self._get_smallcap_symbols_in_range()
            self.logger.info(f"[SYMBOLS] Found {len(smallcap_symbols)} small-cap symbols in range")
            
            if not smallcap_symbols:
                self.logger.info("[SYMBOLS] No symbols in target price range")
                return
            
            # 2. Filter by existing holdings (avoid duplicates)
            existing_symbols = set(
                position.symbol.symbol for position in 
                Position.objects.filter(portfolio=portfolio, total_quantity__gt=0, is_open=True)
            )
            
            new_opportunities = [
                symbol for symbol in smallcap_symbols 
                if symbol['symbol'] not in existing_symbols
            ]
            
            self.logger.info(f"[FILTER] {len(new_opportunities)} new opportunities after filtering existing holdings")
            
            # 3. Analyze each opportunity with LLM
            max_investments = min(3, len(new_opportunities))  # Analyze top 3
            
            for i, symbol_data in enumerate(new_opportunities[:max_investments]):
                if available_balance <= 0:
                    break
                    
                self.logger.info(f"[ANALYZE] {i+1}/{max_investments}: {symbol_data['symbol']}")
                
                # Get detailed analysis
                decision = self._analyze_symbol_for_purchase(symbol_data)
                
                if decision['action'] == 'BUY' and decision['confidence'] >= self.config['MIN_AI_CONFIDENCE']:
                    # Always buy exactly 20 shares per purchase (as per strategy requirement)
                    shares_to_buy = 20
                    total_cost = Decimal(str(symbol_data['price'])) * shares_to_buy
                    
                    if available_balance >= total_cost:
                        # Create buy signal with fixed quantity of 20 shares
                        self._create_buy_signal(symbol_data, decision, portfolio, shares_to_buy)
                        available_balance -= total_cost
                        
                        self.logger.info(f"[BUY SIGNAL] Created for {symbol_data['symbol']} - {shares_to_buy} shares @ ₹{symbol_data['price']} = ₹{total_cost} (Confidence: {decision['confidence']}%)")
                    else:
                        self.logger.info(f"[SKIP] Insufficient funds for {symbol_data['symbol']} - Need ₹{total_cost}, Available: ₹{available_balance}")
                else:
                    self.logger.info(f"[SKIP] {symbol_data['symbol']} - Action: {decision['action']}, Confidence: {decision['confidence']}%")
                    
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to analyze new opportunities: {e}")
    
    def _get_smallcap_symbols_in_range(self):
        """Get small-cap symbols in the target price range (75-150 INR) from AngelOne API."""
        try:
            self.logger.info("[API] Fetching small-cap symbols from AngelOne API...")
            
            # First, get all NSE symbols from the database
            symbols = NSESymbol.objects.filter(
                exchange='NSE',
                instrument_type='EQ',
                is_active=True
            )
            
            target_symbols = []
            
            # Get known small-cap symbols (you can expand this list)
            known_smallcap_symbols = [
                # Technology & IT Services
                'RATTANINDIA', 'IGARASHI', 'SYMPHONY', 'KPITTECH', 'CYIENT',
                # Healthcare & Pharmaceuticals  
                'LALPATHLAB', 'METROPOLIS', 'THYROCARE', 'KRSNAA',
                # Financial Services
                'IIFL', 'MOTILALOFS', 'ANGELONE', 'CDSL',
                # Consumer & Retail
                'VMART', 'SHOPRSTOP', 'TRENT', 'ABFRL',
                # Industrial & Manufacturing
                'POLYCAB', 'SCHAEFFLER', 'TIMKEN', 'CUMMINSIND',
                # Chemicals & Materials
                'CLEAN', 'TATACHEM', 'DEEPAKNTR', 'GNFC',
                # Auto Components
                'MOTHERSON', 'BALKRISIND', 'MRF', 'APOLLOTYRE'
            ]
            
            # Fetch current prices for known small-cap stocks
            for symbol_name in known_smallcap_symbols:
                try:
                    # Get current price from Angel One API
                    current_price = self.angel_api.get_ltp(symbol_name)
                    
                    # Check if price is in target range
                    if self.config['MIN_PRICE'] <= current_price <= self.config['MAX_PRICE']:
                        # Get or create symbol in database
                        symbol, created = NSESymbol.objects.get_or_create(
                            symbol=symbol_name,
                            exchange='NSE',
                            defaults={
                                'name': symbol_name,
                                'instrument_type': 'EQ',
                                'lot_size': 1,
                                'is_active': True
                            }
                        )
                        
                        # Estimate market cap (simplified for small-cap classification)
                        estimated_market_cap = self._estimate_market_cap(symbol, current_price)
                        
                        if estimated_market_cap <= self.config['MAX_MARKET_CAP']:
                            target_symbols.append({
                                'symbol': symbol_name,
                                'name': symbol.name or symbol_name,
                                'price': current_price,
                                'market_cap': estimated_market_cap,
                                'nse_symbol': symbol
                            })
                            
                            self.logger.info(f"[SYMBOL] Added {symbol_name} @ ₹{current_price} (MCap: ₹{estimated_market_cap:,.0f})")
                            
                except Exception as e:
                    self.logger.warning(f"[WARNING] Failed to get data for {symbol_name}: {e}")
                    continue
            
            # Sort by price (lower first for better opportunities)
            target_symbols.sort(key=lambda x: x['price'])
            
            self.logger.info(f"[SYMBOLS] Found {len(target_symbols)} small-cap symbols in price range ₹{self.config['MIN_PRICE']}-{self.config['MAX_PRICE']}")
            
            # Return top 20 for analysis
            return target_symbols[:20]
            
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to get small-cap symbols: {e}")
            # Fallback to basic symbols if API fails
            return self._get_fallback_symbols()
    
    def _get_fallback_symbols(self):
        """Fallback symbol list if API fails."""
        fallback_symbols = [
            {'symbol': 'RATTANINDIA', 'name': 'Rattan India Power', 'price': 120, 'market_cap': 2000000000},
            {'symbol': 'SYMPHONY', 'name': 'Symphony Limited', 'price': 140, 'market_cap': 3000000000},
            {'symbol': 'VMART', 'name': 'V-Mart Retail', 'price': 85, 'market_cap': 1800000000},
        ]
        
        result = []
        for symbol_data in fallback_symbols:
            try:
                symbol, created = NSESymbol.objects.get_or_create(
                    symbol=symbol_data['symbol'],
                    exchange='NSE',
                    defaults={
                        'name': symbol_data['name'],
                        'instrument_type': 'EQ',
                        'lot_size': 1,
                        'is_active': True
                    }
                )
                symbol_data['nse_symbol'] = symbol
                result.append(symbol_data)
            except Exception:
                continue
                
        return result
    
    def _estimate_market_cap(self, symbol, current_price):
        """Estimate market cap based on symbol and price."""
        # Enhanced market cap estimation with symbol-specific logic
        symbol_name = symbol.symbol
        
        # Different estimated outstanding shares based on company type/size
        if any(keyword in symbol_name.upper() for keyword in ['TECH', 'IT', 'SOFTWARE', 'CYBER']):
            # Tech companies typically have fewer shares
            estimated_shares = 8_000_000  # 80 lakh shares
        elif any(keyword in symbol_name.upper() for keyword in ['BANK', 'FIN', 'CAPITAL']):
            # Financial companies typically have more shares
            estimated_shares = 15_000_000  # 1.5 crore shares
        elif any(keyword in symbol_name.upper() for keyword in ['PHARMA', 'HEALTH', 'MED']):
            # Pharma companies - medium share count
            estimated_shares = 10_000_000  # 1 crore shares
        else:
            # General estimation for other companies
            estimated_shares = 12_000_000  # 1.2 crore shares
        
        market_cap = current_price * estimated_shares
        
        # Apply some randomization to avoid exact duplicates (±20%)
        import random
        variation = random.uniform(0.8, 1.2)
        return market_cap * variation
    
    def _analyze_symbol_for_purchase(self, symbol_data):
        """Use LLM and market data to analyze if symbol should be purchased."""
        try:
            # Get additional market data
            symbol_name = symbol_data['symbol']
            current_price = symbol_data['price']
            
            # Get recent news and market data
            news_data = self._get_recent_news(symbol_name)
            technical_data = self._get_technical_indicators(symbol_name)
            
            # Prepare LLM prompt
            prompt = self._create_analysis_prompt(symbol_data, news_data, technical_data)
            
            # Get LLM analysis
            response = self.llm_client.chat.completions.create(
                model=settings.LLM_CONFIG['MODEL'],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            
            analysis_text = response.choices[0].message.content
            
            # Parse LLM response
            decision = self._parse_llm_decision(analysis_text)
            
            self.logger.info(f"[LLM] {symbol_name}: {decision['action']} (Confidence: {decision['confidence']}%)")
            
            return decision
            
        except Exception as e:
            self.logger.error(f"[ERROR] LLM analysis failed for {symbol_data['symbol']}: {e}")
            return {
                'action': 'HOLD',
                'confidence': 0,
                'reasoning': f'Analysis failed: {str(e)}'
            }
    
    def _create_analysis_prompt(self, symbol_data, news_data, technical_data):
        """Create comprehensive analysis prompt for LLM."""
        prompt = f"""
Analyze this Indian small-cap stock for purchase decision:

STOCK DETAILS:
- Symbol: {symbol_data['symbol']}
- Name: {symbol_data['name']}
- Current Price: ₹{symbol_data['price']}
- Market Cap: ₹{symbol_data['market_cap']:,.0f}

RECENT NEWS:
{news_data['summary'] if news_data else 'No recent news available'}

TECHNICAL INDICATORS:
{technical_data['summary'] if technical_data else 'Limited technical data available'}

ANALYSIS CRITERIA:
- Price range: ₹75-150 (✓ Current: ₹{symbol_data['price']})
- Small-cap focus (market cap < ₹5000 crores)
- Risk tolerance: Moderate to high
- Investment horizon: Short to medium term
- Target profit: 5-15%

Please provide:
1. BUY/SELL/HOLD recommendation
2. Confidence level (0-100%)
3. Key reasons for decision
4. Risk factors
5. Target price (if BUY)

Format response as JSON:
{{
    "action": "BUY/SELL/HOLD",
    "confidence": 75,
    "reasoning": "Brief explanation",
    "target_price": 85.50,
    "risk_factors": ["factor1", "factor2"],
    "time_horizon": "short/medium/long"
}}
"""
        return prompt
    
    def _get_recent_news(self, symbol):
        """Get recent news for the symbol."""
        # Placeholder - implement news fetching
        return {
            'summary': f'Recent market activity for {symbol}. General market sentiment appears neutral.',
            'sentiment': 'neutral'
        }
    
    def _get_technical_indicators(self, symbol):
        """Get technical indicators for the symbol."""
        # Placeholder - implement technical analysis
        return {
            'summary': f'Technical analysis for {symbol} shows mixed signals.',
            'trend': 'neutral'
        }
    
    def _parse_llm_decision(self, analysis_text):
        """Parse LLM response into structured decision."""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
            
            if json_match:
                decision_data = json.loads(json_match.group())
                return {
                    'action': decision_data.get('action', 'HOLD'),
                    'confidence': int(decision_data.get('confidence', 50)),
                    'reasoning': decision_data.get('reasoning', 'LLM analysis'),
                    'target_price': decision_data.get('target_price'),
                    'risk_factors': decision_data.get('risk_factors', [])
                }
            else:
                # Fallback parsing
                if 'BUY' in analysis_text.upper():
                    action = 'BUY'
                    confidence = 60
                elif 'SELL' in analysis_text.upper():
                    action = 'SELL'
                    confidence = 60
                else:
                    action = 'HOLD'
                    confidence = 30
                
                return {
                    'action': action,
                    'confidence': confidence,
                    'reasoning': 'Fallback analysis',
                    'target_price': None,
                    'risk_factors': []
                }
                
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to parse LLM decision: {e}")
            return {
                'action': 'HOLD',
                'confidence': 0,
                'reasoning': 'Parse error'
            }
    
    def _create_buy_signal(self, symbol_data, decision, portfolio, quantity=20):
        """Create a buy signal based on analysis."""
        try:
            # Get or create strategy
            strategy = self._get_or_create_strategy()
            
            # Create trading signal
            signal = TradingSignal.objects.create(
                strategy=strategy,
                symbol=symbol_data['nse_symbol'],
                signal_type='BUY',
                confidence=Decimal(str(decision['confidence'])),
                entry_price=Decimal(str(symbol_data['price'])),
                target_price=Decimal(str(decision.get('target_price', symbol_data['price'] * 1.1))),
                stop_loss_price=Decimal(str(symbol_data['price'] * 0.98)),  # 2% stop loss
                signal_strength='STRONG' if decision['confidence'] >= 80 else 'MODERATE',
                analysis_data={
                    'llm_analysis': decision,
                    'symbol_data': symbol_data,
                    'strategy': 'small_cap_llm',
                    'fixed_quantity': quantity,  # Always 20 shares
                    'total_cost': float(Decimal(str(symbol_data['price'])) * quantity),
                    'timestamp': timezone.now().isoformat()
                },
                is_active=True,
                expires_at=timezone.now() + timedelta(hours=24)
            )
            
            return signal
            
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to create buy signal: {e}")
            return None
    
    def _manage_existing_positions(self, portfolio: Portfolio, holdings):
        """Manage existing positions for sell decisions."""
        self.logger.info(f"[MANAGE] Managing {len(holdings)} existing positions...")
        
        for holding in holdings:
            try:
                self._analyze_position_for_exit(portfolio, holding)
            except Exception as e:
                self.logger.error(f"[ERROR] Failed to analyze position {holding.symbol.symbol}: {e}")
    
    def _analyze_position_for_exit(self, portfolio: Portfolio, position: Position):
        """Analyze if a position should be sold."""
        try:
            symbol = position.symbol.symbol
            current_price = self.angel_api.get_ltp(symbol)
            purchase_price = position.average_price
            price_change = current_price - purchase_price
            
            self.logger.info(f"[POSITION] {symbol}: Current ₹{current_price}, Purchase ₹{purchase_price}, Change ₹{price_change:.2f}")
            
            # Check ±2 rupee rule
            should_sell_price = abs(price_change) >= 2
            
            # Get LLM recommendation
            llm_decision = self._analyze_position_with_llm(position, current_price)
            should_sell_llm = llm_decision['action'] == 'SELL' and llm_decision['confidence'] >= 60
            
            if should_sell_price or should_sell_llm:
                reason = "±2 INR rule" if should_sell_price else "LLM recommendation"
                self.logger.info(f"[SELL DECISION] {symbol}: {reason}")
                
                # Create sell signal
                self._create_sell_signal(position, current_price, reason, llm_decision)
            else:
                self.logger.info(f"[HOLD] {symbol}: No sell trigger")
                
        except Exception as e:
            self.logger.error(f"[ERROR] Position analysis failed for {position.symbol.symbol}: {e}")
    
    def _analyze_position_with_llm(self, position: Position, current_price: Decimal):
        """Use LLM to analyze if position should be sold."""
        try:
            symbol = position.symbol.symbol
            purchase_price = position.average_price
            price_change = current_price - purchase_price
            price_change_percent = (price_change / purchase_price) * 100
            
            prompt = f"""
Analyze this small-cap stock position for SELL decision:

POSITION DETAILS:
- Symbol: {symbol}
- Purchase Price: ₹{purchase_price}
- Current Price: ₹{current_price}
- Price Change: ₹{price_change:.2f} ({price_change_percent:.2f}%)
- Quantity: {position.total_quantity}
- Position Value: ₹{current_price * position.total_quantity:,.2f}

CONTEXT:
- Small-cap trading strategy
- Quick profit/loss realization
- Risk management focus

Should this position be SOLD now?
Consider:
1. Price movement significance
2. Market conditions
3. Risk/reward ratio
4. Opportunity cost

Respond with JSON:
{{
    "action": "SELL/HOLD",
    "confidence": 75,
    "reasoning": "Brief explanation",
    "urgency": "high/medium/low"
}}
"""
            
            response = self.llm_client.chat.completions.create(
                model=settings.LLM_CONFIG['MODEL'],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.3
            )
            
            return self._parse_llm_decision(response.choices[0].message.content)
            
        except Exception as e:
            self.logger.error(f"[ERROR] LLM position analysis failed: {e}")
            return {'action': 'HOLD', 'confidence': 0, 'reasoning': 'Analysis failed'}
    
    def _create_sell_signal(self, position: Position, current_price: Decimal, reason: str, llm_decision: dict):
        """Create sell signal for existing position."""
        try:
            strategy = self._get_or_create_strategy()
            
            signal = TradingSignal.objects.create(
                strategy=strategy,
                symbol=position.symbol,
                signal_type='SELL',
                confidence=Decimal('90'),  # High confidence for exit signals
                entry_price=current_price,
                signal_strength='STRONG',
                analysis_data={
                    'sell_reason': reason,
                    'llm_analysis': llm_decision,
                    'purchase_price': float(position.average_price),
                    'current_price': float(current_price),
                    'quantity': position.total_quantity,
                    'strategy': 'small_cap_exit',
                    'timestamp': timezone.now().isoformat()
                },
                is_active=True,
                expires_at=timezone.now() + timedelta(hours=1)
            )
            
            self.logger.info(f"[SELL SIGNAL] Created for {position.symbol.symbol} - Reason: {reason}")
            return signal
            
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to create sell signal: {e}")
            return None
    
    def _get_or_create_strategy(self):
        """Get or create the small-cap strategy."""
        strategy, created = TradingStrategy.objects.get_or_create(
            name='Small Cap LLM Strategy',
            defaults={
                'description': 'Advanced small-cap strategy with LLM analysis and ±2 INR rules',
                'strategy_type': 'CUSTOM',
                'config_parameters': self.config,
                'is_active': True
            }
        )
        return strategy


# Service function to run the strategy
def run_smallcap_strategy(portfolio_id: int):
    """
    Run the small-cap trading strategy for a specific portfolio.
    
    Args:
        portfolio_id: ID of the portfolio to trade with
    """
    try:
        portfolio = Portfolio.objects.get(id=portfolio_id)
        strategy = SmallCapTradingStrategy()
        strategy.run_strategy(portfolio)
        
    except Portfolio.DoesNotExist:
        raise ValueError(f"Portfolio with ID {portfolio_id} not found")
    except Exception as e:
        logging.getLogger('smallcap_strategy').error(f"Strategy execution failed: {e}")
        raise
