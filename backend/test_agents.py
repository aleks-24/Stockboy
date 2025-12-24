"""
Test script for LLM Agents.
Run this standalone to test LLM agent functionality.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.llm_agents import create_agent, MockAgent
from datetime import datetime

def test_llm_agents():
    """Test LLM agents."""
    print("=" * 60)
    print("Testing LLM Agents")
    print("=" * 60)
    
    # Test 1: Create Mock Agent (no API key needed)
    print("\n[TEST 1] Creating Mock Agent...")
    try:
        agent = create_agent(
            provider='mock',
            model='mock',
            name='Test Agent',
            temperature=0.7,
            risk_tolerance='moderate'
        )
        print(f"✓ Successfully created mock agent: {agent.name}")
    except Exception as e:
        print(f"✗ Error creating mock agent: {e}")
        return False
    
    # Test 2: Analyze a sample trade
    print("\n[TEST 2] Analyzing sample trade...")
    sample_trade = {
        'ticker': 'AAPL',
        'company_name': 'Apple Inc.',
        'insider_name': 'Tim Cook',
        'insider_title': 'CEO',
        'trade_type': 'P-Purchase',
        'trade_date': '2024-12-01',
        'price': 190.50,
        'quantity': 10000,
        'value': 1905000,
        'delta_owned': 0.5
    }
    
    sample_context = {
        'sector': 'Technology',
        'industry': 'Consumer Electronics',
        'market_cap': 3000000000000,
        'fundamentals': {
            'pe_ratio': 30.5,
            'dividend_yield': 0.5
        },
        'technicals': {
            'rsi': 55.0,
            'macd': 2.5,
            'sma_50': 185.0
        },
        'signals': {
            'trend': 'bullish'
        }
    }
    
    try:
        decision = agent.analyze_trade(sample_trade, sample_context)
        
        print(f"✓ Agent decision:")
        print(f"  Decision: {decision.get('decision')}")
        print(f"  Confidence: {decision.get('confidence')}")
        print(f"  Reasoning: {decision.get('reasoning')[:100]}...")
        
    except Exception as e:
        print(f"✗ Error analyzing trade: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Test system prompt generation with backtest date
    print("\n[TEST 3] Testing temporal system prompt...")
    try:
        backtest_date = datetime(2023, 1, 1)
        prompt = agent.get_system_prompt(backtest_date)
        
        if '2023-01-01' in prompt and 'TEMPORAL CONSTRAINT' in prompt:
            print("✓ System prompt includes temporal constraints")
        else:
            print("⚠ Warning: Temporal constraints may not be properly set")
            
    except Exception as e:
        print(f"✗ Error generating system prompt: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("LLM agent test completed!")
    print("=" * 60)
    return True

if __name__ == '__main__':
    success = test_llm_agents()
    sys.exit(0 if success else 1)
