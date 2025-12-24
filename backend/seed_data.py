"""
Sample data generator for Stockboy development and testing.
"""
import random
from datetime import datetime, timedelta
from app import app, db
from models import InsiderTrade, Agent


def generate_sample_insider_trades(count: int = 100):
    """Generate sample insider trades for testing."""
    
    tickers = [
        ('AAPL', 'Apple Inc.'),
        ('MSFT', 'Microsoft Corporation'),
        ('GOOGL', 'Alphabet Inc.'),
        ('AMZN', 'Amazon.com Inc.'),
        ('NVDA', 'NVIDIA Corporation'),
        ('META', 'Meta Platforms Inc.'),
        ('TSLA', 'Tesla Inc.'),
        ('JPM', 'JPMorgan Chase & Co.'),
        ('V', 'Visa Inc.'),
        ('WMT', 'Walmart Inc.'),
        ('UNH', 'UnitedHealth Group Inc.'),
        ('JNJ', 'Johnson & Johnson'),
        ('COST', 'Costco Wholesale Corporation'),
        ('HD', 'Home Depot Inc.'),
        ('CRM', 'Salesforce Inc.'),
    ]
    
    insider_names = [
        ('John Smith', 'CEO'),
        ('Jane Doe', 'CFO'),
        ('Robert Johnson', 'Director'),
        ('Emily Williams', 'COO'),
        ('Michael Brown', '10% Owner'),
        ('Sarah Davis', 'VP'),
        ('David Wilson', 'General Counsel'),
        ('Lisa Anderson', 'Director'),
        ('James Taylor', 'President'),
        ('Jennifer Martinez', 'CTO'),
    ]
    
    trades = []
    base_date = datetime.now() - timedelta(days=365 * 5)  # 5 years ago
    
    for i in range(count):
        ticker, company = random.choice(tickers)
        insider_name, title = random.choice(insider_names)
        
        # Random date in the past 5 years
        days_offset = random.randint(0, 365 * 5)
        trade_date = base_date + timedelta(days=days_offset)
        filing_date = trade_date + timedelta(days=random.randint(1, 3))
        
        # 70% buys, 30% sells
        is_purchase = random.random() < 0.7
        trade_type = 'P - Purchase' if is_purchase else 'S - Sale'
        
        # Random price between $50 and $500
        price = round(random.uniform(50, 500), 2)
        
        # Random quantity
        quantity = random.randint(100, 50000)
        value = price * quantity
        
        # Random ownership change
        delta_owned = round(random.uniform(0.1, 25), 2)
        
        trade = InsiderTrade(
            filing_date=filing_date,
            trade_date=trade_date,
            ticker=ticker,
            company_name=company,
            insider_name=insider_name,
            insider_title=title,
            trade_type=trade_type,
            price=price,
            quantity=quantity,
            value=value,
            delta_owned=delta_owned,
            industry='Technology'
        )
        trades.append(trade)
    
    return trades


def generate_sample_agents():
    """Generate sample agents for testing."""
    agents = [
        Agent(
            name='Conservative GPT-4',
            provider='openai',
            model='gpt-4',
            temperature=0.3,
            risk_tolerance='conservative',
            max_position_size=0.05,
            stop_loss_pct=0.05,
            take_profit_pct=0.15
        ),
        Agent(
            name='Aggressive Claude',
            provider='anthropic',
            model='claude-3-sonnet-20240229',
            temperature=0.8,
            risk_tolerance='aggressive',
            max_position_size=0.15,
            stop_loss_pct=0.15,
            take_profit_pct=0.30
        ),
        Agent(
            name='Balanced Gemini',
            provider='google',
            model='gemini-pro',
            temperature=0.5,
            risk_tolerance='moderate',
            max_position_size=0.10,
            stop_loss_pct=0.10,
            take_profit_pct=0.20
        ),
        Agent(
            name='Mock Tester',
            provider='mock',
            model='mock',
            temperature=0.7,
            risk_tolerance='moderate',
            max_position_size=0.10,
            stop_loss_pct=0.10,
            take_profit_pct=0.20
        ),
    ]
    return agents


def seed_database():
    """Seed database with sample data."""
    with app.app_context():
        # Check if already seeded
        if InsiderTrade.query.count() > 0:
            print("Database already has data. Skipping seed.")
            return
        
        print("Seeding database with sample data...")
        
        # Generate and add trades
        trades = generate_sample_insider_trades(500)
        db.session.add_all(trades)
        print(f"Added {len(trades)} insider trades")
        
        # Generate and add agents
        agents = generate_sample_agents()
        db.session.add_all(agents)
        print(f"Added {len(agents)} sample agents")
        
        db.session.commit()
        print("Database seeded successfully!")


if __name__ == '__main__':
    seed_database()
