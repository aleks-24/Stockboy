"""
Test the simple backtest API endpoint.
"""
import pytest
import json
from datetime import datetime, timedelta
from app import app, db
from models import InsiderTrade

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
def sample_trade(client):
    """Create a sample insider trade for testing."""
    with app.app_context():
        trade = InsiderTrade(
            filing_date=datetime(2023, 6, 1),
            trade_date=datetime(2023, 6, 1),
            ticker='AAPL',
            company_name='Apple Inc.',
            insider_name='Tim Cook',
            insider_title='CEO',
            trade_type='P - Purchase',
            price=180.0,
            quantity=10000,
            value=1800000,
            delta_owned=2.5
        )
        db.session.add(trade)
        db.session.commit()
        return trade.id


class TestSimpleBacktestEndpoint:
    """Tests for the simple backtest endpoint."""
    
    def test_simple_backtest_requires_trade_id(self, client):
        """Test that insider_trade_id is required."""
        response = client.post(
            '/api/backtest/simple',
            data=json.dumps({}),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'insider_trade_id is required' in data['error']
    
    def test_simple_backtest_invalid_trade_id(self, client):
        """Test with non-existent trade ID."""
        response = client.post(
            '/api/backtest/simple',
            data=json.dumps({'insider_trade_id': 99999}),
            content_type='application/json'
        )
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'not found' in data['error']
    
    def test_simple_backtest_invalid_holding_period(self, client, sample_trade):
        """Test with invalid holding period."""
        # Test negative holding period
        response = client.post(
            '/api/backtest/simple',
            data=json.dumps({
                'insider_trade_id': sample_trade,
                'holding_period_days': -10
            }),
            content_type='application/json'
        )
        assert response.status_code == 400
        
        # Test holding period too long
        response = client.post(
            '/api/backtest/simple',
            data=json.dumps({
                'insider_trade_id': sample_trade,
                'holding_period_days': 400
            }),
            content_type='application/json'
        )
        assert response.status_code == 400
    
    def test_simple_backtest_invalid_position_size(self, client, sample_trade):
        """Test with invalid position size."""
        # Test negative position size
        response = client.post(
            '/api/backtest/simple',
            data=json.dumps({
                'insider_trade_id': sample_trade,
                'position_size': -0.5
            }),
            content_type='application/json'
        )
        assert response.status_code == 400
        
        # Test position size > 1.0
        response = client.post(
            '/api/backtest/simple',
            data=json.dumps({
                'insider_trade_id': sample_trade,
                'position_size': 1.5
            }),
            content_type='application/json'
        )
        assert response.status_code == 400
    
    def test_simple_backtest_with_valid_trade(self, client, sample_trade):
        """Test backtest with valid trade (may fail if yfinance unavailable)."""
        response = client.post(
            '/api/backtest/simple',
            data=json.dumps({
                'insider_trade_id': sample_trade,
                'holding_period_days': 30,
                'position_size': 1.0
            }),
            content_type='application/json'
        )
        
        # Could be 200 (success) or 500 (if stock data unavailable)
        assert response.status_code in [200, 500]
        
        data = json.loads(response.data)
        if response.status_code == 200:
            # Verify response structure
            assert data['success'] is True
            assert data['ticker'] == 'AAPL'
            assert data['company_name'] == 'Apple Inc.'
            assert 'entry_price' in data
            assert 'exit_price' in data
            assert 'return_pct' in data
            assert 'pnl' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
