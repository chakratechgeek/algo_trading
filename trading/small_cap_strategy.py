"""
Small Cap Trading Strategy Implementation
This implements the specific trading logic requested:
1. Fetch small cap symbols between 50-100 price range
2. Check portfolio balance and analyze for buy decisions
3. Sell at +/- 2 rupees or based on agent suggestion
4. Buy based on agent analysis and volume indicators
"""

import logging
import json
import yfinance as yf
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from together import Together
from .models import TradingStrategy, TradingBot, TradingSignal, TradingExecution
from angel_api.models import NSESymbol, MarketData
from angel_api.services import AngelOneAPI
from portfolio.models import Portfolio, Position, Transaction
from portfolio.services import PortfolioService


class SmallCapTradingService:
    """Service for small cap trading strategy with AI agent analysis."""
    
    def __init__(self):
        self.logger = logging.getLogger('small_cap_trading')
        self.angel_api = AngelOneAPI()
        self.portfolio_service = PortfolioService()
        
        # Initialize AI agent if API key is configured
        try:
            api_key = getattr(settings, 'TOGETHER_API_KEY', '')
            if api_key:
                self.ai_agent = Together(api_key=api_key)
                self.ai_enabled = True
            else:
                self.ai_agent = None
                self.ai_enabled = False
                self.logger.warning("Together API key not configured")
        except Exception as e:
            self.ai_agent = None
            self.ai_enabled = False
            self.logger.warning(f"AI agent initialization failed: {e}")
    
    def get_small_cap_symbols_in_range(self, min_price=50, max_price=100):
        """
        Fetch small cap symbols with price between min_price and max_price.
        Returns list of symbols that meet criteria.
        """
        try:
            # Get all NSE symbols from database
            nse_symbols = NSESymbol.objects.filter(exchange='NSE', is_active=True)
            
            qualified_symbols = []
            
            for symbol in nse_symbols:
                try:
                    # Fetch current price using yfinance as backup
                    ticker = yf.Ticker(f"{symbol.symbol}.NS")
                    info = ticker.info
                    current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
                    
                    # Check if price is in range
                    if min_price <= current_price <= max_price:
                        # Additional small cap criteria
                        market_cap = info.get('marketCap', 0)
                        avg_volume = info.get('averageVolume', 0)
                        
                        # Small cap criteria: Market cap < 5000 crores, decent volume
                        if market_cap < 5000_000_000_000 and avg_volume > 50000:  # 5000 cr, 50k volume
                            qualified_symbols.append({
                                'symbol': symbol.symbol,
                                'current_price': current_price,
                                'market_cap': market_cap,
                                'volume': avg_volume,
                                'symbol_obj': symbol
                            })
                            
                except Exception as e:
                    self.logger.warning(f"Error fetching data for {symbol.symbol}: {e}")
                    continue
            
            # Sort by volume (higher volume first)
            qualified_symbols.sort(key=lambda x: x['volume'], reverse=True)
            
            self.logger.info(f"Found {len(qualified_symbols)} small cap symbols in price range {min_price}-{max_price}")
            return qualified_symbols[:50]  # Limit to top 50 by volume
            
        except Exception as e:
            self.logger.error(f"Error fetching small cap symbols: {e}")
            return []
    
    def check_portfolio_balance(self, portfolio_id):
        """Check portfolio balance and return available cash."""
        try:
            portfolio = Portfolio.objects.get(id=portfolio_id)
            
            # Calculate available balance
            total_positions_value = sum([
                pos.quantity * pos.current_price 
                for pos in portfolio.positions.filter(quantity__gt=0)
            ])
            
            available_balance = portfolio.current_balance - total_positions_value
            
            return {
                'total_balance': portfolio.current_balance,
                'positions_value': total_positions_value,
                'available_balance': available_balance,
                'can_trade': available_balance > 1000  # Minimum 1000 to trade
            }
            
        except Portfolio.DoesNotExist:
            self.logger.error(f"Portfolio {portfolio_id} not found")
            return {'available_balance': 0, 'can_trade': False}
    
    def analyze_stock_with_ai_agent(self, symbol_data):
        """
        Use AI agent to analyze stock and decide buy/sell.
        Returns analysis with recommendation.
        """
        if not self.ai_enabled:
            # Fallback to basic analysis
            return self._basic_stock_analysis(symbol_data)
        
        try:
            # Fetch additional data for analysis
            ticker = yf.Ticker(f"{symbol_data['symbol']}.NS")
            
            # Get recent price history
            hist = ticker.history(period="30d")
            recent_prices = hist['Close'].tail(10).tolist()
            
            # Get basic info
            info = ticker.info
            
            # Prepare analysis prompt
            prompt = f"""
            Analyze this small cap Indian stock for trading decision:
            
            Stock: {symbol_data['symbol']}
            Current Price: ₹{symbol_data['current_price']}
            Market Cap: ₹{symbol_data['market_cap']:,.0f}
            Average Volume: {symbol_data['volume']:,}
            
            Recent 10-day prices: {recent_prices}
            
            Additional Info:
            - P/E Ratio: {info.get('trailingPE', 'N/A')}
            - 52 Week High: ₹{info.get('fiftyTwoWeekHigh', 'N/A')}
            - 52 Week Low: ₹{info.get('fiftyTwoWeekLow', 'N/A')}
            - Beta: {info.get('beta', 'N/A')}
            
            Please provide:
            1. BUY/SELL/HOLD recommendation
            2. Confidence score (0-100)
            3. Key reasons for recommendation
            4. Risk assessment (LOW/MEDIUM/HIGH)
            5. Target price for entry/exit
            
            Consider:
            - Current market conditions
            - Price momentum and volume
            - Technical indicators
            - Risk-reward ratio
            
            Respond in JSON format with keys: recommendation, confidence, reasons, risk_level, target_price
            """
            
            response = self.ai_agent.chat.completions.create(
                model="deepseek-ai/DeepSeek-V3",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            
            # Parse AI response
            try:
                analysis = json.loads(response.choices[0].message.content)
                analysis['ai_powered'] = True
                return analysis
            except json.JSONDecodeError:
                # Fallback to basic analysis if JSON parsing fails
                return self._basic_stock_analysis(symbol_data)
                
        except Exception as e:
            self.logger.error(f"AI analysis failed for {symbol_data['symbol']}: {e}")
            return self._basic_stock_analysis(symbol_data)
    
    def _basic_stock_analysis(self, symbol_data):
        """Basic stock analysis without AI."""
        try:
            ticker = yf.Ticker(f"{symbol_data['symbol']}.NS")
            hist = ticker.history(period="5d")
            
            if len(hist) < 2:
                return {
                    'recommendation': 'HOLD',
                    'confidence': 0,
                    'reasons': ['Insufficient data'],
                    'risk_level': 'HIGH',
                    'target_price': symbol_data['current_price'],
                    'ai_powered': False
                }
            
            # Simple momentum analysis
            recent_change = (hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0] * 100
            avg_volume = hist['Volume'].mean()
            
            # Basic decision logic
            if recent_change > 2 and symbol_data['volume'] > avg_volume * 1.5:
                recommendation = 'BUY'
                confidence = min(70, 50 + abs(recent_change) * 2)
                reasons = [f"Positive momentum: {recent_change:.1f}%", "High volume"]
            elif recent_change < -2:
                recommendation = 'SELL'
                confidence = min(70, 50 + abs(recent_change) * 2)
                reasons = [f"Negative momentum: {recent_change:.1f}%"]
            else:
                recommendation = 'HOLD'
                confidence = 30
                reasons = ["Sideways movement", "No clear trend"]
            
            return {
                'recommendation': recommendation,
                'confidence': confidence,
                'reasons': reasons,
                'risk_level': 'MEDIUM',
                'target_price': symbol_data['current_price'],
                'ai_powered': False
            }
            
        except Exception as e:
            self.logger.error(f"Basic analysis failed: {e}")
            return {
                'recommendation': 'HOLD',
                'confidence': 0,
                'reasons': ['Analysis failed'],
                'risk_level': 'HIGH',
                'target_price': symbol_data['current_price'],
                'ai_powered': False
            }
    
    def check_existing_positions_for_selling(self, portfolio_id):
        """
        Check existing positions and decide which to sell based on:
        1. +/- 2 rupees change from buy price
        2. AI agent suggestion
        """
        try:
            portfolio = Portfolio.objects.get(id=portfolio_id)
            positions = portfolio.positions.filter(quantity__gt=0)
            
            sell_decisions = []
            
            for position in positions:
                try:
                    # Get current price
                    ticker = yf.Ticker(f"{position.symbol.symbol}.NS")
                    current_price = ticker.info.get('currentPrice', position.current_price)
                    
                    # Calculate change from buy price
                    price_change = current_price - position.average_buy_price
                    
                    # Rule 1: Sell if +/- 2 rupees change
                    if abs(price_change) >= 2:
                        sell_reason = f"Price change: ₹{price_change:.2f} (±2 rule)"
                        sell_decisions.append({
                            'position': position,
                            'action': 'SELL',
                            'reason': sell_reason,
                            'current_price': current_price,
                            'confidence': 90,
                            'rule_based': True
                        })
                        continue
                    
                    # Rule 2: Check AI agent suggestion
                    symbol_data = {
                        'symbol': position.symbol.symbol,
                        'current_price': current_price,
                        'market_cap': 0,  # Will be fetched in analysis
                        'volume': 0
                    }
                    
                    analysis = self.analyze_stock_with_ai_agent(symbol_data)
                    
                    if analysis['recommendation'] == 'SELL' and analysis['confidence'] > 60:
                        sell_decisions.append({
                            'position': position,
                            'action': 'SELL',
                            'reason': f"AI suggestion: {', '.join(analysis['reasons'])}",
                            'current_price': current_price,
                            'confidence': analysis['confidence'],
                            'rule_based': False
                        })
                    
                except Exception as e:
                    self.logger.error(f"Error analyzing position {position.id}: {e}")
                    continue
            
            return sell_decisions
            
        except Portfolio.DoesNotExist:
            self.logger.error(f"Portfolio {portfolio_id} not found")
            return []
    
    def execute_buy_decision(self, portfolio_id, symbol_data, analysis, max_investment=5000):
        """Execute buy decision based on analysis."""
        try:
            portfolio = Portfolio.objects.get(id=portfolio_id)
            balance_info = self.check_portfolio_balance(portfolio_id)
            
            if not balance_info['can_trade']:
                return {'success': False, 'message': 'Insufficient balance'}
            
            # Calculate investment amount (max 5000 or 10% of available balance)
            investment_amount = min(
                max_investment,
                balance_info['available_balance'] * 0.1,
                balance_info['available_balance'] - 1000  # Keep 1000 as buffer
            )
            
            if investment_amount < 1000:
                return {'success': False, 'message': 'Investment amount too small'}
            
            # Calculate quantity
            quantity = int(investment_amount / symbol_data['current_price'])
            actual_investment = quantity * symbol_data['current_price']
            
            if quantity == 0:
                return {'success': False, 'message': 'Cannot buy even 1 share'}
            
            # Create position or update existing
            position, created = Position.objects.get_or_create(
                portfolio=portfolio,
                symbol=symbol_data['symbol_obj'],
                defaults={
                    'quantity': 0,
                    'average_buy_price': 0,
                    'current_price': symbol_data['current_price']
                }
            )
            
            # Update position
            total_quantity = position.quantity + quantity
            total_investment = (position.quantity * position.average_buy_price) + actual_investment
            new_avg_price = total_investment / total_quantity
            
            position.quantity = total_quantity
            position.average_buy_price = new_avg_price
            position.current_price = symbol_data['current_price']
            position.save()
            
            # Create transaction record
            Transaction.objects.create(
                portfolio=portfolio,
                symbol=symbol_data['symbol_obj'],
                transaction_type='BUY',
                quantity=quantity,
                price=symbol_data['current_price'],
                total_amount=actual_investment,
                notes=f"AI Analysis: {analysis.get('recommendation', 'N/A')} (Confidence: {analysis.get('confidence', 0)}%)"
            )
            
            # Update portfolio balance
            portfolio.current_balance -= actual_investment
            portfolio.save()
            
            self.logger.info(f"Bought {quantity} shares of {symbol_data['symbol']} at ₹{symbol_data['current_price']}")
            
            return {
                'success': True,
                'message': f"Bought {quantity} shares of {symbol_data['symbol']}",
                'quantity': quantity,
                'price': symbol_data['current_price'],
                'total_amount': actual_investment
            }
            
        except Exception as e:
            self.logger.error(f"Error executing buy decision: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def execute_sell_decision(self, sell_decision):
        """Execute sell decision."""
        try:
            position = sell_decision['position']
            current_price = sell_decision['current_price']
            
            # Calculate total amount
            total_amount = position.quantity * current_price
            
            # Create transaction record
            Transaction.objects.create(
                portfolio=position.portfolio,
                symbol=position.symbol,
                transaction_type='SELL',
                quantity=position.quantity,
                price=current_price,
                total_amount=total_amount,
                notes=sell_decision['reason']
            )
            
            # Update portfolio balance
            position.portfolio.current_balance += total_amount
            position.portfolio.save()
            
            # Remove position
            symbol_name = position.symbol.symbol
            quantity_sold = position.quantity
            position.delete()
            
            self.logger.info(f"Sold {quantity_sold} shares of {symbol_name} at ₹{current_price}")
            
            return {
                'success': True,
                'message': f"Sold {quantity_sold} shares of {symbol_name} at ₹{current_price}",
                'quantity': quantity_sold,
                'price': current_price,
                'total_amount': total_amount
            }
            
        except Exception as e:
            self.logger.error(f"Error executing sell decision: {e}")
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def run_small_cap_trading_cycle(self, portfolio_id):
        """
        Main trading cycle that implements the complete logic:
        1. Check for sells first
        2. Find small cap opportunities
        3. Analyze and execute buys
        """
        try:
            self.logger.info("Starting small cap trading cycle")
            
            results = {
                'sells_executed': [],
                'buys_executed': [],
                'analysis_performed': [],
                'errors': []
            }
            
            # Step 1: Check existing positions for selling
            sell_decisions = self.check_existing_positions_for_selling(portfolio_id)
            
            for sell_decision in sell_decisions:
                result = self.execute_sell_decision(sell_decision)
                results['sells_executed'].append({
                    'symbol': sell_decision['position'].symbol.symbol,
                    'result': result,
                    'reason': sell_decision['reason']
                })
            
            # Step 2: Check balance for new purchases
            balance_info = self.check_portfolio_balance(portfolio_id)
            
            if not balance_info['can_trade']:
                self.logger.info("Insufficient balance for trading")
                return results
            
            # Step 3: Get small cap opportunities
            small_cap_symbols = self.get_small_cap_symbols_in_range(50, 100)
            
            # Step 4: Analyze top opportunities
            for symbol_data in small_cap_symbols[:10]:  # Check top 10
                try:
                    analysis = self.analyze_stock_with_ai_agent(symbol_data)
                    results['analysis_performed'].append({
                        'symbol': symbol_data['symbol'],
                        'analysis': analysis
                    })
                    
                    # Execute buy if AI recommends and confidence > 60%
                    if (analysis['recommendation'] == 'BUY' and 
                        analysis['confidence'] > 60):
                        
                        buy_result = self.execute_buy_decision(
                            portfolio_id, symbol_data, analysis
                        )
                        
                        results['buys_executed'].append({
                            'symbol': symbol_data['symbol'],
                            'result': buy_result,
                            'analysis': analysis
                        })
                        
                        # Limit to 1 buy per cycle
                        break
                        
                except Exception as e:
                    error_msg = f"Error processing {symbol_data['symbol']}: {e}"
                    self.logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            self.logger.info(f"Trading cycle completed. Sells: {len(results['sells_executed'])}, Buys: {len(results['buys_executed'])}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in trading cycle: {e}")
            return {'error': str(e)}
