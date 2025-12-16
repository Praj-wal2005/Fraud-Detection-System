# engines.py
import networkx as nx
import numpy as np
from sklearn.ensemble import IsolationForest
import math
from datetime import datetime

# --- HELPER: Geospatial Distance ---
def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
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
        if current_tx.get('ip_address') in self.BLACKLIST_IPS:
            violations.append("Blacklisted IP detected")

        if user_profile and user_profile.get('last_location'):
            last_lat, last_lon = user_profile['last_location']
            curr_lat, curr_lon = current_tx['location_lat'], current_tx['location_lon']
            distance = calculate_haversine_distance(last_lat, last_lon, curr_lat, curr_lon)
            
            # Time diff in hours
            time_diff = (current_tx['timestamp'] - user_profile['last_timestamp']).total_seconds() / 3600
            
            # Impossible Travel Check
            if time_diff > 0.1 and (distance / time_diff) > self.MAX_VELOCITY_KMH:
                 violations.append(f"Impossible Travel ({int(distance)}km in {time_diff:.1f}h)")
        return violations

# --- 2. GRAPH ENGINE ---
class GraphEngine:
    def __init__(self):
        self.graph = nx.Graph()
        self.known_fraud_nodes = set()

    def update_graph(self, tx):
        self.graph.add_edge(tx['user_id'], tx['device_id'])
        self.graph.add_edge(tx['user_id'], tx['ip_address'])

    def mark_fraud(self, node_id):
        self.known_fraud_nodes.add(node_id)

    def check_network_risk(self, user_id):
        if user_id not in self.graph: return 0.0
        try:
            # Check if connected to fraudster within 2 hops
            neighbors = nx.single_source_shortest_path_length(self.graph, user_id, cutoff=2)
            for node in neighbors:
                if node in self.known_fraud_nodes: return 1.0
        except: pass
        return 0.0

# --- 3. ML ENGINE ---
class MLEngine:
    def __init__(self):
        self.model = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
        # Train on dummy data immediately so the website works
        dummy_data = [[100, 10], [50, 12], [200, 14], [20, 9], [150, 11]]
        self.model.fit(dummy_data)

    def get_risk_score(self, amount, hour):
        X = np.array([[amount, hour]])
        score = self.model.decision_function(X)[0]
        # Normalizing score: Negative is bad. 
        return 1.0 if score < 0 else 0.1