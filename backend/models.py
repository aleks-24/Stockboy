"""
SQLAlchemy models for Stockboy trading bot benchmark platform.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class InsiderTrade(db.Model):
    """Represents an insider trade from OpenInsider.com"""
    __tablename__ = 'insider_trades'
    
    id = db.Column(db.Integer, primary_key=True)
    filing_date = db.Column(db.DateTime, nullable=False, index=True)
    trade_date = db.Column(db.DateTime, nullable=False)
    ticker = db.Column(db.String(10), nullable=False, index=True)
    company_name = db.Column(db.String(200), nullable=False)
    insider_name = db.Column(db.String(200), nullable=False)
    insider_title = db.Column(db.String(100))
    trade_type = db.Column(db.String(20), nullable=False)  # 'P' for Purchase, 'S' for Sale
    price = db.Column(db.Float)
    quantity = db.Column(db.Integer)
    value = db.Column(db.Float)
    shares_owned_after = db.Column(db.Integer)
    delta_owned = db.Column(db.Float)  # Percentage change in ownership
    industry = db.Column(db.String(100))
    sec_filing_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filing_date': self.filing_date.isoformat() if self.filing_date else None,
            'trade_date': self.trade_date.isoformat() if self.trade_date else None,
            'ticker': self.ticker,
            'company_name': self.company_name,
            'insider_name': self.insider_name,
            'insider_title': self.insider_title,
            'trade_type': self.trade_type,
            'price': self.price,
            'quantity': self.quantity,
            'value': self.value,
            'shares_owned_after': self.shares_owned_after,
            'delta_owned': self.delta_owned,
            'industry': self.industry,
            'sec_filing_url': self.sec_filing_url,
        }


class Agent(db.Model):
    """LLM agent configuration"""
    __tablename__ = 'agents'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    provider = db.Column(db.String(50), nullable=False)  # openai, anthropic, google
    model = db.Column(db.String(100), nullable=False)  # gpt-4, claude-3, gemini-pro
    temperature = db.Column(db.Float, default=0.7)
    risk_tolerance = db.Column(db.String(20), default='moderate')  # conservative, moderate, aggressive
    max_position_size = db.Column(db.Float, default=0.1)  # Max % of portfolio per position
    stop_loss_pct = db.Column(db.Float, default=0.1)  # Stop loss percentage
    take_profit_pct = db.Column(db.Float, default=0.2)  # Take profit percentage
    system_prompt = db.Column(db.Text)  # Custom system prompt
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    backtests = db.relationship('Backtest', backref='agent', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'provider': self.provider,
            'model': self.model,
            'temperature': self.temperature,
            'risk_tolerance': self.risk_tolerance,
            'max_position_size': self.max_position_size,
            'stop_loss_pct': self.stop_loss_pct,
            'take_profit_pct': self.take_profit_pct,
            'system_prompt': self.system_prompt,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Backtest(db.Model):
    """Backtest run results"""
    __tablename__ = 'backtests'
    
    id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    initial_capital = db.Column(db.Float, nullable=False)
    final_value = db.Column(db.Float)
    total_return = db.Column(db.Float)  # Percentage
    annualized_return = db.Column(db.Float)
    sharpe_ratio = db.Column(db.Float)
    max_drawdown = db.Column(db.Float)
    win_rate = db.Column(db.Float)
    total_trades = db.Column(db.Integer, default=0)
    benchmark_return = db.Column(db.Float)  # S&P 500 return for comparison
    alpha = db.Column(db.Float)  # Excess return over benchmark
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    error_message = db.Column(db.Text)
    portfolio_history = db.Column(db.JSON)  # List of {date, value} for charting
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    trades = db.relationship('Trade', backref='backtest', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'agent_name': self.agent.name if self.agent else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'initial_capital': self.initial_capital,
            'final_value': self.final_value,
            'total_return': self.total_return,
            'annualized_return': self.annualized_return,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'win_rate': self.win_rate,
            'total_trades': self.total_trades,
            'benchmark_return': self.benchmark_return,
            'alpha': self.alpha,
            'status': self.status,
            'error_message': self.error_message,
            'portfolio_history': self.portfolio_history,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }


class Trade(db.Model):
    """Individual trades made during a backtest"""
    __tablename__ = 'trades'
    
    id = db.Column(db.Integer, primary_key=True)
    backtest_id = db.Column(db.Integer, db.ForeignKey('backtests.id'), nullable=False)
    ticker = db.Column(db.String(10), nullable=False)
    trade_type = db.Column(db.String(10), nullable=False)  # buy, sell
    entry_date = db.Column(db.DateTime, nullable=False)
    entry_price = db.Column(db.Float, nullable=False)
    exit_date = db.Column(db.DateTime)
    exit_price = db.Column(db.Float)
    quantity = db.Column(db.Integer, nullable=False)
    pnl = db.Column(db.Float)  # Profit/Loss
    pnl_pct = db.Column(db.Float)  # Profit/Loss percentage
    reason = db.Column(db.Text)  # LLM's reasoning for the trade
    insider_trade_id = db.Column(db.Integer, db.ForeignKey('insider_trades.id'))
    
    insider_trade = db.relationship('InsiderTrade', backref='triggered_trades')
    
    def to_dict(self):
        return {
            'id': self.id,
            'backtest_id': self.backtest_id,
            'ticker': self.ticker,
            'trade_type': self.trade_type,
            'entry_date': self.entry_date.isoformat() if self.entry_date else None,
            'entry_price': self.entry_price,
            'exit_date': self.exit_date.isoformat() if self.exit_date else None,
            'exit_price': self.exit_price,
            'quantity': self.quantity,
            'pnl': self.pnl,
            'pnl_pct': self.pnl_pct,
            'reason': self.reason,
        }
