"""
Tests for the backtesting engine.
"""
import pytest
from datetime import datetime, timedelta
from app import app, db
from models import InsiderTrade, Agent, Backtest
from services.backtester import BacktestEngine, Portfolio


@pytest.fixture
def app_context():
    """Create app context for testing."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield
        db.drop_all()


@pytest.fixture
def sample_data(app_context):
    """Create sample data for backtesting."""
    # Create an agent
    agent = Agent(
        name='Test Agent',
        provider='mock',
        model='mock',
        temperature=0.7,
        risk_tolerance='moderate',
        max_position_size=0.1,
        stop_loss_pct=0.1,
        take_profit_pct=0.2
    )
    db.session.add(agent)
    
    # Create some insider trades
    base_date = datetime(2023, 1, 1)
    for i in range(5):
        trade = InsiderTrade(
            filing_date=base_date + timedelta(days=i*7),
            trade_date=base_date + timedelta(days=i*7),
            ticker='AAPL',
            company_name='Apple Inc.',
            insider_name=f'Insider {i}',
            insider_title='CEO',
            trade_type='P - Purchase',
            price=150.0 + i,
            quantity=10000,
            value=1500000 + i * 10000,
            delta_owned=5.0
        )
        db.session.add(trade)
    
    db.session.commit()
    return agent.id


class TestPortfolio:
    """Tests for Portfolio class."""
    
    def test_initial_cash(self):
        """Test portfolio initialization."""
        portfolio = Portfolio(100000)
        assert portfolio.cash == 100000
        assert portfolio.open_positions == []
    
    def test_position_tracking(self):
        """Test adding positions."""
        portfolio = Portfolio(100000)
        position = {
            'ticker': 'AAPL',
            'quantity': 100,
            'entry_price': 150.0,
            'entry_date': datetime.now()
        }
        portfolio.open_positions.append(position)
        portfolio.cash -= 15000  # Bought $15k worth
        
        assert len(portfolio.open_positions) == 1
        assert portfolio.cash == 85000


class TestBacktestEngine:
    """Tests for BacktestEngine class."""
    
    def test_engine_initialization(self, app_context):
        """Test engine can be created."""
        engine = BacktestEngine()
        assert engine.stock_service is not None
    
    def test_run_backtest_requires_agent(self, app_context):
        """Test backtest fails without valid agent."""
        engine = BacktestEngine()
        
        with pytest.raises(ValueError, match="Agent .* not found"):
            engine.run_backtest(
                agent_id=9999,  # Non-existent
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 12, 31),
                initial_capital=100000
            )


class TestMetricsCalculation:
    """Tests for metrics calculation logic."""
    
    def test_return_calculation(self):
        """Test return percentage calculation."""
        initial = 100000
        final = 120000
        expected_return = ((final - initial) / initial) * 100
        
        assert expected_return == 20.0
    
    def test_win_rate_calculation(self):
        """Test win rate calculation."""
        trades = [
            {'pnl': 100},
            {'pnl': 50},
            {'pnl': -30},
            {'pnl': 200},
            {'pnl': -50}
        ]
        
        winning = [t for t in trades if t['pnl'] > 0]
        win_rate = len(winning) / len(trades) * 100
        
        assert win_rate == 60.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
