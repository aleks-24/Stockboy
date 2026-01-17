"""
Test script with better error handling.
"""
import requests
import json

url = "http://localhost:5000/api/backtest/simple"

# Test 1: Check server is alive
print("=== Checking server health ===")
health_response = requests.get("http://localhost:5000/api/health")
print(f"Health check: {health_response.status_code}")
print(f"Response: {health_response.json()}\n")

# Test 2: Get a valid trade ID
print("=== Getting valid trade ID ===")
trades_response = requests.get("http://localhost:5000/api/insider-trades?limit=1")
print(f"Trades status: {trades_response.status_code}")
trades_data = trades_response.json()
if trades_data['trades']:
    trade_id = trades_data['trades'][0]['id']
    print(f"Found trade ID: {trade_id}")
    print(f"Ticker: {trades_data['trades'][0]['ticker']}")
    print(f"Date: {trades_data['trades'][0]['trade_date']}\n")
    
    # Test 3: Run simple backtest
    print("=== Running simple backtest ===")
    payload = {
        "insider_trade_id": trade_id,
        "holding_period_days": 30,
        "position_size": 1.0
    }
    
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"URL: {url}\n")
    
    response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    print(f"\nResponse text: {response.text[:500]}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Success!")
        print(json.dumps(result, indent=2))
    else:
        print(f"\n❌ Error: {response.status_code}")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print(response.text)
else:
    print("No trades found!")
