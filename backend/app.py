"""
Stockboy - LLM Trading Bot Benchmark Platform
Flask API Backend
"""
import os
import logging
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

from models import db, InsiderTrade, Agent, Backtest, Trade
from services.scraper import OpenInsiderScraper
from services.stock_data import StockDataService
from services.backtester import BacktestEngine

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///stockboy.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions - Configure CORS with proper settings
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})
db.init_app(app)

# Initialize services
stock_service = StockDataService()
backtest_engine = BacktestEngine()


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })


# ==================== INSIDER TRADES ====================

@app.route('/api/insider-trades', methods=['GET'])
def get_insider_trades():
    """Get insider trades with optional filtering."""
    ticker = request.args.get('ticker')
    trade_type = request.args.get('trade_type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    query = InsiderTrade.query
    
    if ticker:
        query = query.filter(InsiderTrade.ticker == ticker.upper())
    if trade_type:
        query = query.filter(InsiderTrade.trade_type.like(f'%{trade_type}%'))
    if start_date:
        query = query.filter(InsiderTrade.trade_date >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(InsiderTrade.trade_date <= datetime.fromisoformat(end_date))
    
    query = query.order_by(InsiderTrade.trade_date.desc())
    total = query.count()
    trades = query.offset(offset).limit(limit).all()
    
    return jsonify({
        'trades': [t.to_dict() for t in trades],
        'total': total,
        'limit': limit,
        'offset': offset
    })


@app.route('/api/insider-trades/scrape', methods=['POST'])
def scrape_insider_trades():
    """Trigger scraping of insider trades."""
    data = request.get_json() or {}
    
    start_date = datetime.fromisoformat(data.get('start_date')) if data.get('start_date') else None
    end_date = datetime.fromisoformat(data.get('end_date')) if data.get('end_date') else None
    max_pages = data.get('max_pages', 10)
    
    try:
        scraper = OpenInsiderScraper()
        trades = scraper.scrape_trades(
            start_date=start_date,
            end_date=end_date,
            max_pages=max_pages
        )
        saved = scraper.save_trades_to_db(trades)
        
        return jsonify({
            'status': 'success',
            'scraped': len(trades),
            'saved': saved
        })
    except Exception as e:
        logger.error(f"Scraping error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/insider-trades/clusters', methods=['GET'])
def get_cluster_buys():
    """Get cluster buy opportunities."""
    days = request.args.get('days', 30, type=int)
    min_insiders = request.args.get('min_insiders', 2, type=int)
    
    scraper = OpenInsiderScraper()
    clusters = scraper.get_cluster_buys(days=days, min_insiders=min_insiders)
    
    return jsonify({'clusters': clusters})


# ==================== STOCK DATA ====================

@app.route('/api/stock/<ticker>', methods=['GET'])
def get_stock_data(ticker):
    """Get stock data with indicators."""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    start = datetime.fromisoformat(start_date) if start_date else None
    end = datetime.fromisoformat(end_date) if end_date else None
    
    data = stock_service.get_stock_data(ticker.upper(), start, end)
    return jsonify(data)


@app.route('/api/stock/<ticker>/analysis', methods=['GET'])
def get_stock_analysis(ticker):
    """Get analysis context for a stock."""
    date_str = request.args.get('date')
    trade_date = datetime.fromisoformat(date_str) if date_str else datetime.now()
    
    analysis = stock_service.get_analysis_context(ticker.upper(), trade_date)
    return jsonify(analysis)


# ==================== AGENTS ====================

@app.route('/api/agents', methods=['GET'])
def get_agents():
    """Get all configured agents."""
    agents = Agent.query.order_by(Agent.created_at.desc()).all()
    return jsonify({'agents': [a.to_dict() for a in agents]})


@app.route('/api/agents/<int:agent_id>', methods=['GET'])
def get_agent(agent_id):
    """Get a specific agent."""
    agent = Agent.query.get_or_404(agent_id)
    return jsonify(agent.to_dict())


@app.route('/api/agents', methods=['POST'])
def create_agent():
    """Create a new agent."""
    data = request.get_json()
    
    agent = Agent(
        name=data['name'],
        provider=data['provider'],
        model=data['model'],
        temperature=data.get('temperature', 0.7),
        risk_tolerance=data.get('risk_tolerance', 'moderate'),
        max_position_size=data.get('max_position_size', 0.1),
        stop_loss_pct=data.get('stop_loss_pct', 0.1),
        take_profit_pct=data.get('take_profit_pct', 0.2),
        system_prompt=data.get('system_prompt')
    )
    
    db.session.add(agent)
    db.session.commit()
    
    return jsonify(agent.to_dict()), 201


@app.route('/api/agents/<int:agent_id>', methods=['PUT'])
def update_agent(agent_id):
    """Update an agent."""
    agent = Agent.query.get_or_404(agent_id)
    data = request.get_json()
    
    for key in ['name', 'provider', 'model', 'temperature', 'risk_tolerance',
                'max_position_size', 'stop_loss_pct', 'take_profit_pct', 'system_prompt']:
        if key in data:
            setattr(agent, key, data[key])
    
    db.session.commit()
    return jsonify(agent.to_dict())


@app.route('/api/agents/<int:agent_id>', methods=['DELETE'])
def delete_agent(agent_id):
    """Delete an agent."""
    agent = Agent.query.get_or_404(agent_id)
    db.session.delete(agent)
    db.session.commit()
    return jsonify({'status': 'deleted'})


# ==================== BACKTESTS ====================

@app.route('/api/backtests', methods=['GET'])
def get_backtests():
    """Get all backtests."""
    agent_id = request.args.get('agent_id', type=int)
    status = request.args.get('status')
    limit = request.args.get('limit', 50, type=int)
    
    query = Backtest.query
    if agent_id:
        query = query.filter(Backtest.agent_id == agent_id)
    if status:
        query = query.filter(Backtest.status == status)
    
    backtests = query.order_by(Backtest.created_at.desc()).limit(limit).all()
    return jsonify({'backtests': [b.to_dict() for b in backtests]})


@app.route('/api/backtests/<int:backtest_id>', methods=['GET'])
def get_backtest(backtest_id):
    """Get a specific backtest with trades."""
    backtest = Backtest.query.get_or_404(backtest_id)
    result = backtest.to_dict()
    result['trades'] = [t.to_dict() for t in backtest.trades]
    return jsonify(result)


@app.route('/api/backtests', methods=['POST'])
def run_backtest():
    """Run a new backtest."""
    data = request.get_json()
    
    agent_id = data['agent_id']
    start_date = datetime.fromisoformat(data['start_date'])
    end_date = datetime.fromisoformat(data['end_date'])
    initial_capital = data.get('initial_capital', 100000)
    holding_period = data.get('holding_period_days', 30)
    
    try:
        backtest = backtest_engine.run_backtest(
            agent_id=agent_id,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            holding_period_days=holding_period
        )
        return jsonify(backtest.to_dict()), 201
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/backtests/<int:backtest_id>/trades', methods=['GET'])
def get_backtest_trades(backtest_id):
    """Get trades for a backtest."""
    trades = Trade.query.filter_by(backtest_id=backtest_id).all()
    return jsonify({'trades': [t.to_dict() for t in trades]})


# ==================== STATS ====================

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get overall platform statistics."""
    total_trades = InsiderTrade.query.count()
    total_agents = Agent.query.count()
    total_backtests = Backtest.query.count()
    completed_backtests = Backtest.query.filter_by(status='completed').count()
    
    # Get best performing backtest
    best_backtest = Backtest.query.filter_by(status='completed').order_by(
        Backtest.total_return.desc()
    ).first()
    
    # Get recent insider trades count by type
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_buys = InsiderTrade.query.filter(
        InsiderTrade.trade_date >= thirty_days_ago,
        InsiderTrade.trade_type.like('%P%')
    ).count()
    recent_sales = InsiderTrade.query.filter(
        InsiderTrade.trade_date >= thirty_days_ago,
        InsiderTrade.trade_type.like('%S%')
    ).count()
    
    return jsonify({
        'total_insider_trades': total_trades,
        'total_agents': total_agents,
        'total_backtests': total_backtests,
        'completed_backtests': completed_backtests,
        'recent_insider_buys': recent_buys,
        'recent_insider_sales': recent_sales,
        'best_backtest': best_backtest.to_dict() if best_backtest else None
    })


# Create database tables
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
