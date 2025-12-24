"""
Pytest tests for Stockboy backend.
"""
import pytest
import json
from datetime import datetime, timedelta
from app import app, db
from models import InsiderTrade, Agent, Backtest, Trade


@pytest.fixture
def client():
    """Create test client."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


@pytest.fixture
def sample_agent(client):
    """Create a sample agent."""
    with app.app_context():
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
        db.session.commit()
        return agent.id


@pytest.fixture
def sample_trades(client):
    """Create sample insider trades."""
    with app.app_context():
        trades = []
        for i in range(5):
            trade = InsiderTrade(
                filing_date=datetime.now() - timedelta(days=i),
                trade_date=datetime.now() - timedelta(days=i+1),
                ticker=f'TEST{i}',
                company_name=f'Test Company {i}',
                insider_name=f'Insider {i}',
                insider_title='CEO',
                trade_type='P - Purchase',
                price=100.0 + i * 10,
                quantity=1000 * (i + 1),
                value=100000 * (i + 1),
                delta_owned=5.0 + i
            )
            db.session.add(trade)
            trades.append(trade)
        db.session.commit()
        return [t.id for t in trades]


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check returns 200."""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'


class TestAgentsEndpoints:
    """Tests for agent CRUD endpoints."""
    
    def test_get_agents_empty(self, client):
        """Test getting agents when none exist."""
        response = client.get('/api/agents')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['agents'] == []
    
    def test_create_agent(self, client):
        """Test creating a new agent."""
        agent_data = {
            'name': 'GPT-4 Trader',
            'provider': 'openai',
            'model': 'gpt-4',
            'temperature': 0.5,
            'risk_tolerance': 'aggressive'
        }
        response = client.post(
            '/api/agents',
            data=json.dumps(agent_data),
            content_type='application/json'
        )
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['name'] == 'GPT-4 Trader'
        assert data['provider'] == 'openai'
    
    def test_get_agent(self, client, sample_agent):
        """Test getting a specific agent."""
        response = client.get(f'/api/agents/{sample_agent}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'Test Agent'
    
    def test_update_agent(self, client, sample_agent):
        """Test updating an agent."""
        update_data = {'name': 'Updated Agent', 'temperature': 0.9}
        response = client.put(
            f'/api/agents/{sample_agent}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'Updated Agent'
        assert data['temperature'] == 0.9
    
    def test_delete_agent(self, client, sample_agent):
        """Test deleting an agent."""
        response = client.delete(f'/api/agents/{sample_agent}')
        assert response.status_code == 200
        
        # Verify deleted
        response = client.get(f'/api/agents/{sample_agent}')
        assert response.status_code == 404


class TestInsiderTradesEndpoints:
    """Tests for insider trades endpoints."""
    
    def test_get_insider_trades_empty(self, client):
        """Test getting trades when none exist."""
        response = client.get('/api/insider-trades')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['trades'] == []
        assert data['total'] == 0
    
    def test_get_insider_trades(self, client, sample_trades):
        """Test getting insider trades."""
        response = client.get('/api/insider-trades')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['trades']) == 5
        assert data['total'] == 5
    
    def test_filter_by_ticker(self, client, sample_trades):
        """Test filtering trades by ticker."""
        response = client.get('/api/insider-trades?ticker=TEST0')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['trades']) == 1
        assert data['trades'][0]['ticker'] == 'TEST0'
    
    def test_pagination(self, client, sample_trades):
        """Test trade pagination."""
        response = client.get('/api/insider-trades?limit=2&offset=0')
        data = json.loads(response.data)
        assert len(data['trades']) == 2
        assert data['total'] == 5


class TestBacktestsEndpoints:
    """Tests for backtest endpoints."""
    
    def test_get_backtests_empty(self, client):
        """Test getting backtests when none exist."""
        response = client.get('/api/backtests')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['backtests'] == []


class TestStatsEndpoint:
    """Tests for stats endpoint."""
    
    def test_get_stats(self, client, sample_trades, sample_agent):
        """Test getting platform stats."""
        response = client.get('/api/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total_insider_trades'] == 5
        assert data['total_agents'] == 1


class TestStockDataEndpoint:
    """Tests for stock data endpoints."""
    
    def test_get_stock_data(self, client):
        """Test getting stock data (may fail if yfinance rate limited)."""
        response = client.get('/api/stock/AAPL')
        # Response depends on external API, just check it doesn't crash
        assert response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
