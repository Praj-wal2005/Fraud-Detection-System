import networkx as nx

class GraphEngine:
    def __init__(self):
        # In production, this would connect to Neo4j
        self.graph = nx.Graph()
        self.known_fraud_nodes = set()

    def update_graph(self, transaction):
        """Add transaction entities to the graph"""
        user_id = transaction['user_id']
        device_id = transaction['device_id']
        ip = transaction['ip_address']

        # Add nodes
        self.graph.add_node(user_id, type='user')
        self.graph.add_node(device_id, type='device')
        self.graph.add_node(ip, type='ip')

        # Add edges (Relationships)
        self.graph.add_edge(user_id, device_id)
        self.graph.add_edge(user_id, ip)

    def mark_fraud(self, user_id):
        self.known_fraud_nodes.add(user_id)

    def check_network_risk(self, user_id):
        """
        Check if user is connected to known fraud within 2 hops.
        """
        if user_id not in self.graph:
            return 0.0

        try:
            # Get neighbors within 2 hops
            subgraph_nodes = nx.single_source_shortest_path_length(self.graph, user_id, cutoff=2)
            
            for node in subgraph_nodes:
                if node in self.known_fraud_nodes:
                    return 1.0  # High Risk: Connected to fraudster
        except:
            pass
            
        # Check for Synthetic Identity (One Device, Many Users)
        device_neighbors = [n for n in self.graph.neighbors(user_id) if self.graph.nodes[n].get('type') == 'device']
        for dev in device_neighbors:
            users_on_device = [n for n in self.graph.neighbors(dev) if self.graph.nodes[n].get('type') == 'user']
            if len(users_on_device) > 3:
                return 0.8 # Risk: Device used by too many people

        return 0.0