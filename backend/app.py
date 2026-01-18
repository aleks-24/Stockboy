"""
Stockboy - LLM Trading Bot Benchmark Platform
Flask API Backend
"""
import os
import logging
from datetime import datetime, timedelta
import queue
import threading
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
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})
db.init_app(app)

# Initialize services
stock_service = StockDataService()
backtest_engine = BacktestEngine()

# Global dictionary to store message queues for active backtests
# Key: backtest_id, Value: queue.Queue
BACKTEST_QUEUES = {}



def update_env_file(key, value):
    """Update or add a key-value pair in the .env file."""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    # Read existing lines
    lines = []
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
            
    # Process lines
    new_lines = []
    found = False
    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            found = True
        else:
            new_lines.append(line)
            
    # Add if not found
    if not found:
        if new_lines and not new_lines[-1].endswith('\n'):
            new_lines[-1] += '\n'
        new_lines.append(f"{key}={value}\n")
        
    # Write back
    with open(env_path, 'w') as f:
        f.writelines(new_lines)
        
    # Update current process env
    os.environ[key] = value


@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get current settings (masked)."""
    keys = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY']
    settings = {}
    
    for key in keys:
        val = os.getenv(key)
        if val:
            # Mask the key: show first 3 and last 4 chars
            if len(val) > 10:
                settings[key.lower()] = f"{val[:3]}...{val[-4:]}"
            else:
                settings[key.lower()] = "Set (hidden)"
        else:
            settings[key.lower()] = ""
            
    return jsonify(settings)


@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Update settings."""
    data = request.get_json()
    
    mapping = {
        'openai': 'OPENAI_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY',
        'google': 'GOOGLE_API_KEY'
    }
    
    updated = []
    for ui_key, env_key in mapping.items():
        if ui_key in data and data[ui_key]:
            # Only update if value is provided (not empty)
            # If masked value is sent back, ignore it
            if '...' not in data[ui_key] and 'Set (hidden)' not in data[ui_key]:
                update_env_file(env_key, data[ui_key])
                updated.append(ui_key)
                
    return jsonify({
        'status': 'success',
        'updated': updated,
        'message': 'Settings saved successfully. Changes apply immediately.'
    })


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


def run_backtest_wrapper(backtest_id, kwargs):
    """Wrapper to run backtest in a thread and push logs to queue."""
    logger.info(f"Starting background backtest {backtest_id}")
    
    # Create a new queue for this backtest
    if backtest_id not in BACKTEST_QUEUES:
        BACKTEST_QUEUES[backtest_id] = queue.Queue()
        
    log_queue = BACKTEST_QUEUES[backtest_id]
    
    def progress_callback(message, msg_type="info"):
        """Callback to push messages to queue."""
        try:
            log_queue.put({
                "message": message,
                "type": msg_type,
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Error pushing to queue: {e}")
            
    with app.app_context():
        try:
            # Add existing_backtest_id to kwargs
            kwargs['existing_backtest_id'] = backtest_id
            kwargs['progress_callback'] = progress_callback
            
            backtest_engine.run_backtest(**kwargs)
            
            # Send completion message
            log_queue.put({
                "message": "Backtest completed successfully",
                "type": "complete",
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Background backtest failed: {e}")
            log_queue.put({
                "message": f"Backtest failed: {str(e)}",
                "type": "error",
                "timestamp": datetime.utcnow().isoformat()
            })
        finally:
            pass


@app.route('/api/backtests/stream/<int:backtest_id>', methods=['GET'])
def stream_backtest_logs(backtest_id):
    """Stream backtest logs in real-time using Server-Sent Events."""
    from flask import Response, stream_with_context
    import json
    import time
    
    def generate():
        """Generator function for SSE stream."""
        try:
            # Send initial message
            yield f"data: {json.dumps({'message': f'Connected to backtest {backtest_id} stream', 'type': 'info'})}\n\n"
            
            # Get the queue
            log_queue = BACKTEST_QUEUES.get(backtest_id)
            
            # If no queue (maybe restarted server or completed long ago), check DB
            if not log_queue:
                with app.app_context():
                    backtest = Backtest.query.get(backtest_id)
                    if backtest and backtest.status == 'completed':
                        yield f"data: {json.dumps({'message': 'Backtest already completed', 'type': 'complete', 'return': backtest.total_return})}\n\n"
                        return
                    elif backtest and backtest.status == 'failed':
                        yield f"data: {json.dumps({'message': f'Backtest failed: {backtest.error_message}', 'type': 'error'})}\n\n"
                        return
                    else:
                        yield f"data: {json.dumps({'message': 'Waiting for backtest to start...', 'type': 'info'})}\n\n"
            
            # Stream from queue
            timeout_seconds = 600  # 10 minute timeout
            start_time = datetime.utcnow()
            last_activity = start_time
            
            while (datetime.utcnow() - start_time).total_seconds() < timeout_seconds:
                # Check for messages in queue
                if log_queue and not log_queue.empty():
                    try:
                        msg_data = log_queue.get_nowait()
                        yield f"data: {json.dumps(msg_data)}\n\n"
                        last_activity = datetime.utcnow()
                        
                        if msg_data.get('type') in ['complete', 'error']:
                            break
                    except queue.Empty:
                        pass
                
                # If queue is empty, verify backtest implementation hasn't crashed/finished without queue update
                # (or if we are just waiting for it to be created)
                if not log_queue and backtest_id in BACKTEST_QUEUES:
                    log_queue = BACKTEST_QUEUES[backtest_id]
                
                # Send heartbeat
                if (datetime.utcnow() - last_activity).total_seconds() > 5:
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                    last_activity = datetime.utcnow()
                
                time.sleep(0.1)
                    
        except GeneratorExit:
            logger.info(f"Client disconnected from backtest {backtest_id} stream")
            # Optional: cleanup queue if no one else is listening?
            # For simplicity, we leave it since it's just strings
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


@app.route('/api/backtests', methods=['POST'])
def run_backtest():
    """Run a new backtest in the background."""
    data = request.get_json()
    
    agent_id = data['agent_id']
    start_date = datetime.fromisoformat(data['start_date'])
    end_date = datetime.fromisoformat(data['end_date'])
    initial_capital = data.get('initial_capital', 100000)
    holding_period = data.get('holding_period_days', 30)
    
    try:
        # Create backtest record immediately to get an ID
        backtest = Backtest(
            agent_id=agent_id,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            status='pending'
        )
        db.session.add(backtest)
        db.session.commit()
        
        # Prepare arguments for backtest engine
        kwargs = {
            'agent_id': agent_id,
            'start_date': start_date,
            'end_date': end_date,
            'initial_capital': initial_capital,
            'holding_period_days': holding_period
        }
        
        # Start background thread
        thread = threading.Thread(
            target=run_backtest_wrapper,
            args=(backtest.id, kwargs)
        )
        thread.daemon = True
        thread.start()
        
        # Return accepted status with backtest details
        return jsonify(backtest.to_dict()), 202
        
    except Exception as e:
        logger.error(f"Backtest startup error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/backtests/<int:backtest_id>/trades', methods=['GET'])
def get_backtest_trades(backtest_id):
    """Get trades for a backtest."""
    trades = Trade.query.filter_by(backtest_id=backtest_id).all()
    return jsonify({'trades': [t.to_dict() for t in trades]})


@app.route('/api/backtest/simple', methods=['POST'])
def run_simple_backtest():
    """Run a simple backtest for a single insider trade without requiring agents."""
    data = request.get_json()
    
    # Validate required parameters
    if 'insider_trade_id' not in data:
        return jsonify({'error': 'insider_trade_id is required'}), 400
    
    insider_trade_id = data['insider_trade_id']
    holding_period_days = data.get('holding_period_days', 30)
    position_size = data.get('position_size', 1.0)
    
    # Validate holding period
    if holding_period_days <= 0 or holding_period_days > 365:
        return jsonify({'error': 'holding_period_days must be between 1 and 365'}), 400
    
    # Validate position size
    if position_size <= 0 or position_size > 1.0:
        return jsonify({'error': 'position_size must be between 0 and 1.0'}), 400
    
    # Get the insider trade
    insider_trade = InsiderTrade.query.get(insider_trade_id)
    if not insider_trade:
        return jsonify({'error': f'Insider trade {insider_trade_id} not found'}), 404
    
    try:
        # Run the simple backtest
        result = backtest_engine.run_simple_backtest(
            insider_trade=insider_trade,
            holding_period_days=holding_period_days,
            position_size=position_size
        )
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify({'error': result.get('error', 'Unknown error')}), 500
            
    except Exception as e:
        logger.error(f"Simple backtest error: {e}")
        return jsonify({'error': str(e)}), 500


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
    
    # Seed default "Robust Trader" agent if not exists
    try:
        if Agent.query.filter_by(name="Robust Trader").first() is None:
            logger.info("Seeding 'Robust Trader' agent...")
            
            # Determine provider based on available keys
            provider = "mock"
            model = "mock-v1"
            if os.getenv("OPENAI_API_KEY"):
                provider = "openai"
                model = "gpt-4o"
            elif os.getenv("ANTHROPIC_API_KEY"):
                provider = "anthropic"
                model = "claude-3-5-sonnet-20240620"
                
            robust_agent = Agent(
                name="Robust Trader",
                provider=provider,
                model=model,
                temperature=0.7,
                risk_tolerance="high",
                max_position_size=0.15,
                stop_loss_pct=0.15,
                take_profit_pct=0.30,
                system_prompt="""You are a highly analytical and decisive trading algorithm specializing in insider trading signals.
Your goal is to maximize alpha by identifying high-conviction insider moves.

METHODOLOGY:
1. **Analyze the Insider**: Is this a C-level exec (CEO/CFO)? They know the most. Is it a cluster of buys? 
2. **Analyze the Trade**: Is the value > $100k? Is it a Purchase? (Grants/Options are less signal).
3. **Analyze the Value**: Is the stock beaten down? (Value play) or Momentum? 
4. **Decision**: Be decisive. If the signal is strong, BUY. If bad, SELL. If noise, HOLD.

Your output reasoning MUST be a step-by-step breakdown using bullet points.
"""
            )
            db.session.add(robust_agent)
            db.session.commit()
            logger.info(f"Seeded 'Robust Trader' using {provider}")
    except Exception as e:
        logger.error(f"Failed to seed agents: {e}")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
