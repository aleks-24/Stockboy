"""
Test live backtest streaming.
"""
import requests
import json
import time

BASE_URL = "http://localhost:5000/api"

def test_stream():
    print("=" * 60)
    print("TESTING LIVE BACKTEST STREAMING")
    print("=" * 60)
    
    # Get a completed backtest to test streaming
    print("\n1. Getting backtest list...")
    response = requests.get(f"{BASE_URL}/backtests?limit=1")
    backtests = response.json()['backtests']
    
    if not backtests:
        print("   No backtests found. Need to create one first.")
        return
    
    backtest_id = backtests[0]['id']
    status = backtests[0]['status']
    
    print(f"   Testing with backtest ID: {backtest_id}")
    print(f"   Status: {status}")
    
    # Stream the backtest
    print(f"\n2. Streaming backtest progress...")
    print("   " + "-" * 56)
    
    url = f"{BASE_URL}/backtests/stream/{backtest_id}"
    
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            for line in r.iter_lines():
                if line:
                    # Decode and parse SSE data
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            msg = data.get('message', '')
                            msg_type = data.get('type', 'info')
                            
                            icon = {
                                'info': 'ℹ️',
                                'heartbeat': '💓',
                                'complete': '✅',
                                'error': '❌'
                            }.get(msg_type, '📝')
                            
                            print(f"   {icon} [{msg_type.upper():10s}] {msg}")
                            
                            # Exit on completion or error
                            if msg_type in ['complete', 'error']:
                                break
                                
                        except json.JSONDecodeError:
                            print(f"   Could not parse: {line_str}")
    except requests.exceptions.Timeout:
        print("   ⏱️  Stream timeout")
    except KeyboardInterrupt:
        print("\n   User interrupted")
    
    print("   " + "-" * 56)
    print("\n3. Stream test complete!")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_stream()
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to API. Make sure Flask server is running.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
