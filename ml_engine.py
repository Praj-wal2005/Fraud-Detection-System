import numpy as np
from sklearn.ensemble import IsolationForest

class MLEngine:
    def __init__(self):
        # Unsupervised model for anomaly detection
        self.model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
        self.is_trained = False

    def train(self, historical_features):
        """
        Expects a list of lists: [[amount, hour_of_day], ...]
        """
        X = np.array(historical_features)
        self.model.fit(X)
        self.is_trained = True

    def get_risk_score(self, feature_vector):
        if not self.is_trained:
            return 0.5 # Default uncertainty

        # Reshape for single prediction
        X = np.array(feature_vector).reshape(1, -1)
        
        # decision_function returns negative for outliers, positive for inliers
        score = self.model.decision_function(X)[0]
        
        # Normalize score to 0-1 range (approximate) for risk
        # Lower score = Higher Anomaly
        risk = 1.0 if score < 0 else 0.0
        return risk