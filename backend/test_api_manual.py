"""
Test script to verify the simple backtest API endpoint.
"""
import requests
import json
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:5000/api"

def test_health():
    """Test health endpoint."""
    print("\n=== Testing Health Endpoint ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def get_insider_trades():
    """Get list of insider trades."""
    print("\n=== Fetching Insider Trades ===")
    response = requests.get(f"{BASE_URL}/insider-trades?limit=5")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {data['total']} total trades")
        if data['trades']:
            print(f"First trade: {data['trades'][0]['ticker']} - {data['trades'][0]['company_name']}")
            return data['trades'][0]['id']
    else:
        print(f"Error: {response.status_code}")
    return None

def test_simple_backtest(trade_id, holding_period=30):
    """Test the simple backtest endpoint."""
    print(f"\n=== Testing Simple Backtest for Trade ID {trade_id} ===")
    
    payload = {
        "insider_trade_id": trade_id,
        "holding_period_days": holding_period,
        "position_size": 1.0
    }
    
    response = requests.post(
        f"{BASE_URL}/backtest/simple",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print(f"\n✅ Backtest Successful!")
            print(f"Ticker: {result['ticker']}")
            print(f"Company: {result['company_name']}")
            print(f"Insider: {result['insider_name']} ({result['insider_title']})")
            print(f"Entry Date: {result['entry_date']}")
            print(f"Exit Date: {result['exit_date']}")
            print(f"Entry Price: ${result['entry_price']}")
            print(f"Exit Price: ${result['exit_price']}")
            print(f"Return: {result['return_pct']:.2f}%")
            print(f"P&L: ${result['pnl']:.2f}")
            print(f"Final Value: ${result['final_value']:.2f}")
            return True
        else:
            print(f"❌ Backtest failed: {result.get('error')}")
    else:
        print(f"❌ HTTP Error: {response.text}")
    
    return False

def test_invalid_trade_id():
    """Test with invalid trade ID."""
    print("\n=== Testing Invalid Trade ID ===")
    
    payload = {
        "insider_trade_id": 9999999,
        "holding_period_days": 30
    }
    
    response = requests.post(
        f"{BASE_URL}/backtest/simple",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 404:
        print("✅ Correctly returned 404 for invalid trade ID")
        return True
    else:
        print(f"❌ Expected 404, got {response.status_code}")
        return False

def test_missing_parameters():
    """Test with missing required parameters."""
    print("\n=== Testing Missing Parameters ===")
    
    payload = {}
    
    response = requests.post(
        f"{BASE_URL}/backtest/simple",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 400:
        print("✅ Correctly returned 400 for missing parameters")
        return True
    else:
        print(f"❌ Expected 400, got {response.status_code}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("STOCKBOY API TEST SUITE")
    print("=" * 60)
    
    # Test health endpoint
    if not test_health():
        print("\n❌ Server is not running!")
        return
    
    # Test invalid inputs first
    test_missing_parameters()
    test_invalid_trade_id()
    
    # Get a real trade and test
    trade_id = get_insider_trades()
    if trade_id:
        # Test with 30 days
        test_simple_backtest(trade_id, holding_period=30)
        
        # Test with 90 days
        test_simple_backtest(trade_id, holding_period=90)
    else:
        print("\n⚠️  No insider trades found in database.")
        print("   Run seed_data.py or scrape some data first!")
    
    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to the API server.")
        print("   Make sure the Flask server is running on http://localhost:5000")
    except Exception as e:
        print(f"\n❌ Error: {e}")
