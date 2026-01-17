"""
Test agent prompt editing functionality.
"""
import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_agent_editing():
    print("=" * 60)
    print("TESTING AGENT PROMPT EDITING")
    print("=" * 60)
    
    # Get list of agents
    print("\n1. Getting list of agents...")
    response = requests.get(f"{BASE_URL}/agents")
    agents = response.json()['agents']
    
    if not agents:
        print("   No agents found. Creating a test agent...")
        # Create a test agent
        create_response = requests.post(f"{BASE_URL}/agents", json={
            "name": "Test Agent",
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.7,
            "risk_tolerance": "moderate",
            "system_prompt": "You are a trading assistant."
        })
        agent = create_response.json()
    else:
        agent = agents[0]
    
    print(f"   Using agent ID: {agent['id']} - {agent['name']}")
    print(f"   Current prompt: {agent.get('system_prompt', 'None')[:50]}...")
    
    # Update the system prompt
    print("\n2. Updating system prompt...")
    new_prompt = "You are a conservative trader focused on long-term value investing. Analyze insider trades carefully and only recommend trades with strong fundamentals."
    
    update_response = requests.put(
        f"{BASE_URL}/agents/{agent['id']}",
        json={"system_prompt": new_prompt},
        headers={"Content-Type": "application/json"}
    )
    
    if update_response.status_code == 200:
        print("   ✅ Update successful!")
        updated_agent = update_response.json()
        print(f"   New prompt: {updated_agent['system_prompt'][:80]}...")
    else:
        print(f"   ❌ Update failed: {update_response.status_code}")
        print(f"   {update_response.text}")
        return
    
    # Verify the update persisted
    print("\n3. Verifying update persisted...")
    verify_response = requests.get(f"{BASE_URL}/agents/{agent['id']}")
    verified_agent = verify_response.json()
    
    if verified_agent['system_prompt'] == new_prompt:
        print("   ✅ System prompt successfully updated and persisted!")
    else:
        print("   ❌ System prompt did not persist correctly")
    
    print("\n" + "=" * 60)
    print("AGENT EDITING TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_agent_editing()
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to API. Make sure Flask server is running.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
