# app.py
from flask import Flask, render_template, request
from datetime import datetime, timedelta
from engines import RuleEngine, GraphEngine, MLEngine

app = Flask(__name__)

# --- INITIALIZE SYSTEM ---
rule_engine = RuleEngine()
graph_engine = GraphEngine()
ml_engine = MLEngine()

# Mock Database for User Profiles
user_db = {
    "user_bangalore": {
        "last_location": (12.9716, 77.5946), # Bangalore
        "last_timestamp": datetime.now() - timedelta(hours=1)
    }
}

# Pre-load a fraud ring for testing
graph_engine.update_graph({'user_id': 'bad_guy', 'device_id': 'dev_666', 'ip_address': '0.0.0.0'})
graph_engine.mark_fraud('bad_guy')
# Connect dev_666 to the graph so if anyone else uses it, they get flagged
graph_engine.update_graph({'user_id': 'bad_guy_2', 'device_id': 'dev_666', 'ip_address': '1.1.1.1'})


@app.route('/', methods=['GET', 'POST'])
def dashboard():
    result = None
    
    if request.method == 'POST':
        # 1. Extract Data from Form
        user_id = request.form.get('user_id')
        amount = float(request.form.get('amount'))
        lat = float(request.form.get('lat'))
        lon = float(request.form.get('lon'))
        device_id = request.form.get('device_id')
        
        # Build Transaction Object
        tx_data = {
            'user_id': user_id, 'amount': amount,
            'location_lat': lat, 'location_lon': lon,
            'timestamp': datetime.now(),
            'ip_address': request.remote_addr, # Gets your actual IP
            'device_id': device_id
        }

        # 2. Run Analysis
        reasons = []
        status = "APPROVE"
        risk_score = 0
        
        # A. Rule Check
        user_profile = user_db.get(user_id)
        rule_violations = rule_engine.check_rules(tx_data, user_profile)
        if rule_violations:
            status = "BLOCK"
            reasons.extend(rule_violations)
            risk_score += 50

        # B. Graph Check (Link Analysis)
        graph_engine.update_graph(tx_data) # Add current tx to graph
        net_risk = graph_engine.check_network_risk(user_id)
        if net_risk > 0.5:
            status = "BLOCK"
            reasons.append("Linked to known fraud device/ring")
            risk_score += 40

        # C. ML Check
        ml_risk = ml_engine.get_risk_score(amount, datetime.now().hour)
        if ml_risk > 0.5 and status != "BLOCK":
            status = "REVIEW"
            reasons.append(f"AI Anomaly Detected (Score: {ml_risk})")
            risk_score += 20

        # Final Result Package
        result = {
            "status": status,
            "reasons": reasons if reasons else ["Transaction looks safe."],
            "risk_score": min(risk_score, 100),
            "tx_data": tx_data
        }

        # Update Mock DB
        user_db[user_id] = {
            "last_location": (lat, lon),
            "last_timestamp": datetime.now()
        }

    return render_template('index.html', result=result)

if __name__ == '__main__':
    app.run(debug=True, port=5000)