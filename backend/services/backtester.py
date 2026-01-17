"""
Backtesting engine for evaluating LLM trading agents.
"""
import logging
from datetime import datetime, timedelta
import time
from typing import Dict, Any, List, Optional
import numpy as np

from models import db, Backtest, Trade, InsiderTrade, Agent
from services.stock_data import StockDataService
from services.llm_agents import create_agent

logger = logging.getLogger(__name__)


class BacktestEngine:
    """Engine for backtesting LLM trading agents on historical insider data."""
    
    def __init__(self):
        self.stock_service = StockDataService()
    

    def run_backtest(
        self,
        agent_id: int,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 100000.0,
        holding_period_days: int = 30,
        progress_callback=None,
        existing_backtest_id: int = None
    ) -> Backtest:
        """
        Run a backtest for an agent.
        
        Args:
            agent_id: ID of the agent to backtest
            start_date: Start of backtest period
            end_date: End of backtest period
            initial_capital: Starting capital
            holding_period_days: Default holding period for positions
            progress_callback: Optional callback function(message, type)
            existing_backtest_id: Optional ID of existing backtest record
            
        Returns:
            Backtest result object
        """
        # Get agent configuration
        if progress_callback:
            progress_callback(f"Starting backtest for agent {agent_id}", "info")
        
        agent_config = db.session.get(Agent, agent_id)
        if not agent_config:
            raise ValueError(f"Agent {agent_id} not found")
        
        # Create the LLM agent
        agent = create_agent(
            provider=agent_config.provider,
            model=agent_config.model,
            name=agent_config.name,
            temperature=agent_config.temperature,
            risk_tolerance=agent_config.risk_tolerance,
            max_position_size=agent_config.max_position_size,
            stop_loss_pct=agent_config.stop_loss_pct,
            take_profit_pct=agent_config.take_profit_pct,
            system_prompt=agent_config.system_prompt
        )
        
        if existing_backtest_id:
            backtest = db.session.get(Backtest, existing_backtest_id)
            if not backtest:
                raise ValueError(f"Backtest {existing_backtest_id} not found")
            # Update status if needed
            backtest.status = 'running'
        else:
            # Create backtest record
            backtest = Backtest(
                agent_id=agent_id,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                status='running'
            )
            db.session.add(backtest)
            
        db.session.commit()
        
        try:
            # Get insider trades in the period
            if progress_callback:
                progress_callback(f"Fetching insider trades from {start_date.date()} to {end_date.date()}", "info")
            
            insider_trades = InsiderTrade.query.filter(
                InsiderTrade.trade_date >= start_date,
                InsiderTrade.trade_date <= end_date
            ).order_by(InsiderTrade.trade_date).all()
            
            if progress_callback:
                progress_callback(f"Found {len(insider_trades)} insider trades to analyze", "info")
            
            if not insider_trades:
                backtest.status = 'completed'
                backtest.error_message = 'No insider trades found in period'
                backtest.final_value = initial_capital
                backtest.total_return = 0.0
                db.session.commit()
                return backtest
            
            # Run simulation
            portfolio = Portfolio(initial_capital)
            trades = []
            portfolio_history = []
            
            if progress_callback:
                progress_callback(f"Starting simulation with ${initial_capital:,.2f} initial capital", "info")
            
            # Aggregate trades by ticker, date, and type to avoid double work
            aggregated_map = {}
            for trade in insider_trades:
                # Key: Ticker + Date (YYYY-MM-DD) + Type
                key = (trade.ticker, trade.trade_date.date(), trade.trade_type)
                
                if key not in aggregated_map:
                    # Create base dict from first trade
                    base_dict = trade.to_dict()
                    base_dict['insider_names'] = [trade.insider_name]
                    base_dict['original_count'] = 1
                    aggregated_map[key] = base_dict
                else:
                    # Merge into existing
                    agg = aggregated_map[key]
                    agg['value'] = (agg.get('value') or 0) + (trade.value or 0)
                    agg['quantity'] = (agg.get('quantity') or 0) + (trade.quantity or 0)
                    if trade.insider_name not in agg['insider_names']:
                        agg['insider_names'].append(trade.insider_name)
                    agg['original_count'] += 1
            
            # Convert aggregated map back to list of objects (or dicts acting as objects)
            # We need to simulate the object access pattern or just use dicts. 
            # The current loop uses `insider_trade.ticker`. If we change `insider_trades` to be a list of dicts,
            # we must adjust the accessors in the loop below (e.g. `insider_trade['ticker']`).
            # BETTER STRATEGY: Create a simple class wrapper or just modify the loop to handle dicts if needed.
            # But simpler: Use `SimpleNamespace` or just rewrite the loop to use dict access?
            # The loop uses: .ticker, .trade_date, .to_dict().
            # Let's wrap the dicts in a helper class to maintain dot notation compatibility.
            
            class TradeWrapper:
                def __init__(self, data):
                    self.data = data
                    for k, v in data.items():
                        setattr(self, k, v)
                    # Special handling for aggregated fields
                    if len(data.get('insider_names', [])) > 1:
                        self.insider_name = f"{len(data['insider_names'])} Insiders ({', '.join(data['insider_names'][:2])}...)"
                    self.value = data.get('value')
                    self.quantity = data.get('quantity')
                    # Ensure price exists (fallback to original entry's price)
                    self.price = data.get('price')

                def to_dict(self):
                    return self.data

            processed_trades = [TradeWrapper(d) for d in aggregated_map.values()]
            # Sort by date
            processed_trades.sort(key=lambda x: x.trade_date)
            
            if progress_callback:
                 progress_callback(f"Aggregated {len(insider_trades)} raw trades into {len(processed_trades)} analyzed events.", "info")

            for idx, insider_trade in enumerate(processed_trades, 1):
                if progress_callback and idx % 10 == 0:
                    progress_callback(f"Analyzing trade {idx}/{len(insider_trades)}: {insider_trade.ticker}", "progress")
                # Get stock context for analysis
                stock_context = self.stock_service.get_analysis_context(
                    insider_trade.ticker,
                    insider_trade.trade_date
                )
                
                if 'error' in stock_context:
                    logger.warning(f"Stock context error for {insider_trade.ticker}: {stock_context['error']}. Proceeding with insider data only.")
                    # continue  <-- Don't skip, just proceed
                
                # Get LLM decision
                decision = agent.analyze_trade(insider_trade.to_dict(), stock_context)
                
                # Log detailed analysis
                reasoning = decision.get('reasoning', 'No reasoning provided')
                decision_type = decision.get('decision', 'HOLD')
                confidence = decision.get('confidence', 0)
                
                # Throttle for live feeling
                time.sleep(0.1)
                
                # Debug logging
                logger.info(f"Trade Analysis - Ticker: {insider_trade.ticker}, Type: {insider_trade.trade_type}, Value: {insider_trade.value}, Decision: {decision_type}")

                if progress_callback:
                    # Log the reasoning as a distinct step
                    progress_callback(f"🤖 Agent Analysis for {insider_trade.ticker}:", "analysis")
                    progress_callback(f"{reasoning}", "analysis_details")
                    
                    if decision_type == 'BUY':
                        progress_callback(f"  → BUY signal for {insider_trade.ticker} (confidence: {confidence:.2f})", "trade")
                    elif decision_type == 'SELL':
                            progress_callback(f"  → SELL signal for {insider_trade.ticker} (confidence: {confidence:.2f})", "trade")
                    else:
                        progress_callback(f"  → HOLD decision for {insider_trade.ticker}", "info")
                
                # Execute trade if decision is to buy
                if decision_type == 'BUY' and confidence > 0.5:
                    trade = self._execute_buy(
                        portfolio, insider_trade, decision, holding_period_days
                    )
                    if trade:
                        trades.append(trade)
                
                # Record portfolio value at each decision point
                portfolio_value = portfolio.get_total_value(
                    insider_trade.trade_date,
                    self.stock_service
                )
                portfolio_history.append({
                    'date': insider_trade.trade_date.isoformat(),
                    'value': portfolio_value
                })
            
            # Close all remaining positions at end date
            for position in portfolio.open_positions:
                close_result = self._close_position(
                    portfolio, position, end_date
                )
                if close_result:
                    trades.append(close_result)
            
            # Calculate final metrics
            if progress_callback:
                progress_callback(f"Backtest complete. Calculating final metrics...", "info")
            
            final_value = portfolio.get_total_value(end_date, self.stock_service)
            metrics = self._calculate_metrics(
                initial_capital, final_value, trades,
                start_date, end_date, portfolio_history
            )
            
            if progress_callback:
                progress_callback(f"Final value: ${final_value:,.2f} | Return: {metrics['total_return']:.2f}% | Trades: {len(trades)}", "success")
            
            # Get benchmark return
            benchmark_return = self._calculate_benchmark_return(start_date, end_date)
            
            # Update backtest record
            backtest.final_value = final_value
            backtest.total_return = metrics['total_return']
            backtest.annualized_return = metrics['annualized_return']
            backtest.sharpe_ratio = metrics['sharpe_ratio']
            backtest.max_drawdown = metrics['max_drawdown']
            backtest.win_rate = metrics['win_rate']
            backtest.total_trades = len(trades)
            backtest.benchmark_return = benchmark_return
            backtest.alpha = metrics['total_return'] - benchmark_return if benchmark_return else None
            backtest.portfolio_history = portfolio_history
            backtest.status = 'completed'
            backtest.completed_at = datetime.utcnow()
            
            # Save trades
            for trade_data in trades:
                trade = Trade(
                    backtest_id=backtest.id,
                    ticker=trade_data['ticker'],
                    trade_type=trade_data['trade_type'],
                    entry_date=trade_data['entry_date'],
                    entry_price=trade_data['entry_price'],
                    exit_date=trade_data.get('exit_date'),
                    exit_price=trade_data.get('exit_price'),
                    quantity=trade_data['quantity'],
                    pnl=trade_data.get('pnl'),
                    pnl_pct=trade_data.get('pnl_pct'),
                    reason=trade_data.get('reason'),
                    insider_trade_id=trade_data.get('insider_trade_id')
                )
                db.session.add(trade)
            
            db.session.commit()
            return backtest
            
        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            backtest.status = 'failed'
            backtest.error_message = str(e)
            db.session.commit()
            raise
    
    def _execute_buy(
        self,
        portfolio: 'Portfolio',
        insider_trade: InsiderTrade,
        decision: Dict,
        holding_period_days: int
    ) -> Optional[Dict]:
        """Execute a buy order."""
        ticker = insider_trade.ticker
        trade_date = insider_trade.trade_date
        
        # Get current price
        current_price = self.stock_service.get_price_at_date(ticker, trade_date)
        if current_price is None:
            # Fallback to insider transaction price if market data fails
            if insider_trade.price:
                current_price = insider_trade.price
                logger.warning(f"Using insider price ${current_price} as fallback for {insider_trade.ticker}")
            else:
                return None
        
        # Calculate position size
        position_size = decision.get('position_size', 0.05)
        max_value = portfolio.cash * position_size
        quantity = int(max_value / current_price)
        
        if quantity <= 0:
            return None
        
        # Execute buy
        cost = quantity * current_price
        if cost > portfolio.cash:
            return None
        
        portfolio.cash -= cost
        position = {
            'ticker': ticker,
            'quantity': quantity,
            'entry_price': current_price,
            'entry_date': trade_date,
            'target_exit_date': trade_date + timedelta(days=holding_period_days),
            'insider_trade_id': insider_trade.id
        }
        portfolio.open_positions.append(position)
        
        return {
            'ticker': ticker,
            'trade_type': 'buy',
            'entry_date': trade_date,
            'entry_price': current_price,
            'quantity': quantity,
            'reason': decision.get('reasoning'),
            'insider_trade_id': insider_trade.id
        }
    
    def _close_position(
        self,
        portfolio: 'Portfolio',
        position: Dict,
        exit_date: datetime
    ) -> Optional[Dict]:
        """Close an open position."""
        ticker = position['ticker']
        exit_price = self.stock_service.get_price_at_date(ticker, exit_date)
        
        if not exit_price:
            logger.warning(f"Using entry price {position['entry_price']} as fallback exit for {ticker}")
            exit_price = position['entry_price']
        
        quantity = position['quantity']
        entry_price = position['entry_price']
        pnl = (exit_price - entry_price) * quantity
        pnl_pct = ((exit_price - entry_price) / entry_price) * 100
        
        # Add proceeds back to cash
        portfolio.cash += exit_price * quantity
        portfolio.open_positions.remove(position)
        
        return {
            'ticker': ticker,
            'trade_type': 'sell',
            'entry_date': position['entry_date'],
            'entry_price': entry_price,
            'exit_date': exit_date,
            'exit_price': exit_price,
            'quantity': quantity,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'insider_trade_id': position.get('insider_trade_id')
        }
    
    def _calculate_metrics(
        self,
        initial_capital: float,
        final_value: float,
        trades: List[Dict],
        start_date: datetime,
        end_date: datetime,
        portfolio_history: List[Dict]
    ) -> Dict[str, float]:
        """Calculate performance metrics."""
        # Total return
        total_return = ((final_value - initial_capital) / initial_capital) * 100
        
        # Annualized return
        days = (end_date - start_date).days
        years = days / 365.25
        if years > 0:
            annualized_return = ((final_value / initial_capital) ** (1 / years) - 1) * 100
        else:
            annualized_return = total_return
        
        # Win rate
        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        win_rate = (len(winning_trades) / len(trades) * 100) if trades else 0
        
        # Max drawdown
        if portfolio_history:
            values = [h['value'] for h in portfolio_history]
            peak = values[0]
            max_dd = 0
            for value in values:
                if value > peak:
                    peak = value
                dd = (peak - value) / peak
                max_dd = max(max_dd, dd)
            max_drawdown = max_dd * 100
        else:
            max_drawdown = 0
        
        # Sharpe ratio (simplified, assuming 2% risk-free rate)
        if portfolio_history and len(portfolio_history) > 1:
            returns = []
            for i in range(1, len(portfolio_history)):
                prev_val = portfolio_history[i-1]['value']
                curr_val = portfolio_history[i]['value']
                if prev_val > 0:
                    returns.append((curr_val - prev_val) / prev_val)
            
            if returns:
                mean_return = np.mean(returns)
                std_return = np.std(returns)
                rf_rate = 0.02 / 252  # Daily risk-free rate
                sharpe_ratio = (mean_return - rf_rate) / std_return * np.sqrt(252) if std_return > 0 else 0
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        return {
            'total_return': round(total_return, 2),
            'annualized_return': round(annualized_return, 2),
            'win_rate': round(win_rate, 2),
            'max_drawdown': round(max_drawdown, 2),
            'sharpe_ratio': round(sharpe_ratio, 2)
        }
    
    def _calculate_benchmark_return(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[float]:
        """Calculate S&P 500 return for the period."""
        try:
            sp500_data = self.stock_service.get_sp500_data(start_date, end_date)
            if sp500_data is not None and not sp500_data.empty:
                start_price = sp500_data.iloc[0]['Close']
                end_price = sp500_data.iloc[-1]['Close']
                return round(((end_price - start_price) / start_price) * 100, 2)
        except Exception as e:
            logger.error(f"Error calculating benchmark: {e}")
        return None
    
    def run_simple_backtest(
        self,
        insider_trade: InsiderTrade,
        holding_period_days: int = 30,
        position_size: float = 1.0
    ) -> Dict[str, Any]:
        """
        Run a simple backtest for a single insider trade without LLM agents.
        
        Args:
            insider_trade: The insider trade to backtest
            holding_period_days: Number of days to hold the position
            position_size: Multiplier for position size (1.0 = 100% of available capital)
            
        Returns:
            Dictionary with backtest results including entry/exit prices and returns
        """
        try:
            ticker = insider_trade.ticker
            entry_date = insider_trade.trade_date
            exit_date = entry_date + timedelta(days=holding_period_days)
            
            # Get entry price (price at insider trade date)
            entry_price = self.stock_service.get_price_at_date(ticker, entry_date)
            if not entry_price:
                return {
                    'success': False,
                    'error': f'Could not fetch entry price for {ticker} on {entry_date.strftime("%Y-%m-%d")}'
                }
            
            # Get exit price (price after holding period)
            exit_price = self.stock_service.get_price_at_date(ticker, exit_date)
            if not exit_price:
                return {
                    'success': False,
                    'error': f'Could not fetch exit price for {ticker} on {exit_date.strftime("%Y-%m-%d")}'
                }
            
            # Calculate returns
            price_change = exit_price - entry_price
            return_pct = (price_change / entry_price) * 100
            
            # Calculate P&L assuming $10,000 position
            initial_investment = 10000 * position_size
            shares = initial_investment / entry_price
            pnl = shares * price_change
            final_value = initial_investment + pnl
            
            # Get stock info for context
            stock_context = self.stock_service.get_analysis_context(ticker, entry_date)
            
            return {
                'success': True,
                'ticker': ticker,
                'company_name': insider_trade.company_name,
                'insider_name': insider_trade.insider_name,
                'insider_title': insider_trade.insider_title,
                'trade_type': insider_trade.trade_type,
                'insider_trade_value': insider_trade.value,
                'entry_date': entry_date.isoformat(),
                'exit_date': exit_date.isoformat(),
                'holding_period_days': holding_period_days,
                'entry_price': round(entry_price, 2),
                'exit_price': round(exit_price, 2),
                'price_change': round(price_change, 2),
                'return_pct': round(return_pct, 2),
                'initial_investment': round(initial_investment, 2),
                'shares': round(shares, 4),
                'pnl': round(pnl, 2),
                'final_value': round(final_value, 2),
                'sector': stock_context.get('sector') if 'error' not in stock_context else None,
                'industry': stock_context.get('industry') if 'error' not in stock_context else None,
            }
            
        except Exception as e:
            logger.error(f"Simple backtest failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class Portfolio:
    """Simple portfolio management class."""
    
    def __init__(self, initial_cash: float):
        self.cash = initial_cash
        self.open_positions = []
    
    def get_total_value(self, date: datetime, stock_service: StockDataService) -> float:
        """Calculate total portfolio value."""
        total = self.cash
        
        for position in self.open_positions:
            price = stock_service.get_price_at_date(position['ticker'], date)
            if price:
                total += price * position['quantity']
            else:
                # Use entry price if current price not available
                total += position['entry_price'] * position['quantity']
        
        return total
