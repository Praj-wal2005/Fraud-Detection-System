import networkx as nx
import numpy as np
from sklearn.ensemble import IsolationForest
import math
from datetime import datetime

# --- HELPER: Geospatial Distance ---
def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    # Ensure inputs are floats to prevent errors
    lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return c * 6371 # km

# --- 1. RULE ENGINE ---
class RuleEngine:
    def __init__(self):
        self.BLACKLIST_IPS = {'192.168.1.50', '10.0.0.99'}
        self.MAX_VELOCITY_KMH = 800.0 

    def check_rules(self, current_tx, user_profile):
        violations = []
        # Check IP
        if current_tx.get('ip_address') in self.BLACKLIST_IPS:
            violations.append("Blacklisted IP detected")

        # Check Impossible Travel
        if user_profile and user_profile.get('last_location'):
            last_lat, last_lon = user_profile['last_location']
            curr_lat, curr_lon = current_tx['location_lat'], current_tx['location_lon']
            distance = calculate_haversine_distance(last_lat, last_lon, curr_lat, curr_lon)
            
            # Time diff in hours
            time_diff = (current_tx['timestamp'] - user_profile['last_timestamp']).total_seconds() / 3600
            
            # Avoid division by zero if transactions are instant
            if time_diff > 0.01:
                speed = distance / time_diff
                if speed > self.MAX_VELOCITY_KMH:
                     violations.append(f"Impossible Travel ({int(distance)}km in {time_diff:.2f}h)")
        return violations

# --- 2. GRAPH ENGINE ---
class GraphEngine:
    def __init__(self):
        self.graph = nx.Graph()
        self.known_fraud_nodes = set()

    def update_graph(self, tx):
        # Add nodes and edges safely
        u, d, ip = tx['user_id'], tx['device_id'], tx['ip_address']
        self.graph.add_edge(u, d)
        self.graph.add_edge(u, ip)

    def mark_fraud(self, node_id):
        self.known_fraud_nodes.add(node_id)

    def check_network_risk(self, user_id):
        if user_id not in self.graph: return 0.0
        try:
            # Check neighbors up to 2 hops away
            lengths = nx.single_source_shortest_path_length(self.graph, user_id, cutoff=2)
            for node in lengths:
                if node in self.known_fraud_nodes:
                    return 1.0 # Connected to fraud!
        except Exception as e:
            print(f"Graph Error: {e}")
            return 0.0
        return 0.0

# --- 3. ML ENGINE ---
class MLEngine:
    def __init__(self):
        self.model = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
        # Dummy training data
        dummy_data = [[100, 10], [50, 12], [200, 14], [20, 9], [150, 11]]
        self.model.fit(dummy_data)

    def get_risk_score(self, amount, hour):
        try:
            X = np.array([[float(amount), float(hour)]])
            score = self.model.decision_function(X)[0]
            # Negative score = Anomaly (High Risk)
            return 1.0 if score < 0 else 0.1
        except:
            return 0.0