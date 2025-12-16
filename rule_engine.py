from datetime import datetime
from utils import calculate_haversine_distance

class RuleEngine:
    def __init__(self):
        self.BLACKLIST_IPS = {'192.168.1.50', '10.0.0.99'}
        self.MAX_VELOCITY_KMH = 800.0  # Max commercial flight speed approx

    def check_rules(self, current_tx, user_profile):
        """
        Returns a list of rule violations.
        """
        violations = []

        # 1. Blacklist Check
        if current_tx.get('ip_address') in self.BLACKLIST_IPS:
            violations.append("Blacklisted IP detected")

        # 2. Impossible Travel Check
        if user_profile and user_profile.get('last_location'):
            last_lat, last_lon = user_profile['last_location']
            curr_lat, curr_lon = current_tx['location_lat'], current_tx['location_lon']
            
            distance = calculate_haversine_distance(last_lat, last_lon, curr_lat, curr_lon)
            
            # Time difference in hours
            time_diff = (current_tx['timestamp'] - user_profile['last_timestamp']).total_seconds() / 3600
            
            if time_diff > 0:
                speed = distance / time_diff
                if speed > self.MAX_VELOCITY_KMH:
                    violations.append(f"Impossible Travel: Speed {speed:.2f} km/h > Limit")

        return violations