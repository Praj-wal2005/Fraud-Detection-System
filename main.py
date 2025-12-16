from datetime import datetime, timedelta
import random
from rule_engine import RuleEngine
from graph_engine import GraphEngine
from ml_engine import MLEngine

# --- MOCK DATABASE ---
user_profiles = {
    "user_123": {
        "last_location": (12.9716, 77.5946), # Bangalore
        "last_timestamp": datetime.now() - timedelta(hours=2)
    }
}

# --- SYSTEM INITIALIZATION ---
rule_engine = RuleEngine()
graph_engine = GraphEngine()
ml_engine = MLEngine()

# Train ML Engine with dummy normal data
# [Amount, Hour]
dummy_history = [[100, 10], [50, 12], [200, 14], [20, 9], [150, 11]] 
ml_engine.train(dummy_history)

# Pre-populate graph with a known fraud ring
graph_engine.update_graph({'user_id': 'fraud_A', 'device_id': 'dev_X', 'ip_address': '1.1.1.1'})
graph_engine.mark_fraud('fraud_A')
# Connect a normal user to this device (Simulating account takeover)
graph_engine.update_graph({'user_id': 'user_compromised', 'device_id': 'dev_X', 'ip_address': '2.2.2.2'})


def process_transaction(tx_data):
    print(f"\n--- Processing Transaction for {tx_data['user_id']} ---")
    
    # 1. Update Graph with new data
    graph_engine.update_graph(tx_data)

    # 2. Check Rules
    user_profile = user_profiles.get(tx_data['user_id'])
    rule_violations = rule_engine.check_rules(tx_data, user_profile)
    
    if rule_violations:
        print(f"❌ BLOCKED (Rule Violation): {rule_violations}")
        return "BLOCK"

    # 3. Check Graph Risks
    graph_risk = graph_engine.check_network_risk(tx_data['user_id'])
    if graph_risk > 0.7:
        print(f"❌ BLOCKED (Graph Risk): Linked to known fraud ring.")
        return "BLOCK"

    # 4. Check ML Model
    # Features: [Amount, Hour of day]
    features = [tx_data['amount'], tx_data['timestamp'].hour]
    ml_risk = ml_engine.get_risk_score(features)
    
    if ml_risk > 0.5:
        print(f"⚠️ REVIEW (ML Anomaly): Unusual transaction pattern.")
        return "REVIEW"

    print("✅ APPROVED")
    # Update profile for next time
    user_profiles[tx_data['user_id']] = {
        "last_location": (tx_data['location_lat'], tx_data['location_lon']),
        "last_timestamp": tx_data['timestamp']
    }
    return "APPROVE"


# --- SIMULATION ---

# Scenario 1: Normal Transaction in Bangalore
tx_1 = {
    'user_id': 'user_123',
    'amount': 150,
    'timestamp': datetime.now(),
    'location_lat': 12.9716, 'location_lon': 77.5946, # Bangalore
    'ip_address': '192.168.0.1',
    'device_id': 'device_123'
}
process_transaction(tx_1)

# Scenario 2: Impossible Travel (London 1 hour later)
tx_2 = {
    'user_id': 'user_123',
    'amount': 200,
    'timestamp': datetime.now() + timedelta(hours=1),
    'location_lat': 51.5074, 'location_lon': -0.1278, # London
    'ip_address': '192.168.0.2',
    'device_id': 'device_123'
}
process_transaction(tx_2)

# Scenario 3: Graph Risk (User connected to fraud device)
tx_3 = {
    'user_id': 'user_compromised',
    'amount': 50,
    'timestamp': datetime.now(),
    'location_lat': 12.9716, 'location_lon': 77.5946,
    'ip_address': '2.2.2.2',
    'device_id': 'dev_X' # This device was used by 'fraud_A' earlier
}
process_transaction(tx_3)