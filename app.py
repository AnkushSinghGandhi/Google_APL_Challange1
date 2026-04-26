"""
EventFlow AI — Agentic Crowd Orchestrator
Main Flask application with REST API endpoints.
"""
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from simulator import StadiumSimulator
from rewards import RewardEngine
from config import STADIUM_NODES
import gemini_engine

app = Flask(__name__)
CORS(app)

# --- Initialize engines ---
simulator = StadiumSimulator()
rewards = RewardEngine()
gemini_engine.init_engine(simulator, rewards)


# --- Page Routes ---
@app.route("/")
def index():
    return render_template("index.html")


# --- API Key Management ---

@app.route("/api/key/status", methods=["GET"])
def key_status():
    """Check if a Gemini API key is configured."""
    return jsonify(gemini_engine.get_api_key_status())


@app.route("/api/key/set", methods=["POST"])
def set_key():
    """Allow users to set their own Gemini API key."""
    data = request.get_json() or {}
    key = data.get("key", "").strip()
    if not key:
        return jsonify({"error": "No key provided"}), 400
    gemini_engine.set_api_key(key)
    return jsonify({"status": "ok", **gemini_engine.get_api_key_status()})


@app.route("/api/key/clear", methods=["POST"])
def clear_key():
    """Clear user-set API key, revert to env var."""
    gemini_engine.set_api_key(None)
    return jsonify({"status": "cleared", **gemini_engine.get_api_key_status()})


# --- API Routes ---

@app.route("/api/state", methods=["GET"])
def get_state():
    """Get full stadium state."""
    state = simulator.get_state()
    state["leaderboard"] = rewards.get_leaderboard(5)
    state["recent_rewards"] = rewards.get_recent_rewards(5)
    return jsonify(state)


@app.route("/api/simulate", methods=["POST"])
def simulate_step():
    """Advance simulation by 1 tick."""
    state = simulator.simulate_step()
    return jsonify(state)


@app.route("/api/event/phase", methods=["POST"])
def set_phase():
    """Change event phase."""
    data = request.get_json() or {}
    phase = data.get("phase", "")
    if simulator.set_phase(phase):
        return jsonify({"status": "ok", "phase": phase})
    return jsonify({"error": "Invalid phase. Use: pre_event, during_event, halftime, post_event"}), 400


@app.route("/api/predict/<int:minutes>", methods=["GET"])
def predict(minutes):
    """Predict crowd state N minutes ahead."""
    minutes = min(10, max(1, minutes))
    predictions = simulator.predict_future(minutes)
    return jsonify({"predictions": predictions})


@app.route("/api/agent/decide", methods=["POST"])
def agent_decide():
    """Trigger Gemini agent to analyze and act."""
    decision = gemini_engine.agent_decide()
    return jsonify(decision)


@app.route("/api/agent/history", methods=["GET"])
def agent_history():
    """Get past agent decisions."""
    return jsonify({"decisions": gemini_engine.get_decision_history()})


@app.route("/api/user/checkin", methods=["POST"])
def user_checkin():
    """User checks in at a node — gets personalized suggestion."""
    data = request.get_json() or {}
    user_id = data.get("user_id", "user_1")
    node_id = data.get("node_id", "gate_a")

    # Update user location
    rewards.checkin_user(user_id, node_id)

    # Get AI suggestion
    suggestion = gemini_engine.get_user_suggestion(user_id, node_id)

    return jsonify({
        "user": rewards.get_user(user_id),
        "suggestion": suggestion,
    })


@app.route("/api/leaderboard", methods=["GET"])
def leaderboard():
    """Get gamification leaderboard."""
    return jsonify({"leaderboard": rewards.get_leaderboard(10)})


@app.route("/api/emergency", methods=["POST"])
def emergency():
    """Activate emergency evacuation mode with optional severity."""
    data = request.get_json() or {}
    severity = data.get("severity", "code_red")

    simulator.set_phase("post_event")

    # Force redistribute from all non-gate nodes to gates
    evac_actions = []
    gate_nodes = ["gate_a", "gate_b", "gate_c"]
    for nid, node in simulator.nodes.items():
        if nid not in gate_nodes and node["crowd"] > 10:
            target_gate = min(gate_nodes, key=lambda g: simulator.nodes[g]["crowd"])
            moved = min(30, node["crowd"] - 5)
            result = simulator.apply_redistribution(nid, target_gate, moved)
            evac_actions.append(result)

    # Issue priority exit to all users
    for uid in list(rewards.users.keys())[:10]:
        rewards.issue_reward(uid, "priority_exit", "Emergency evacuation")

    # Auto-deploy responders based on severity
    deploy_results = []
    if severity == "code_red":
        # Full deployment: all types to all gates and hotspots
        hotspots = simulator.get_hotspots()
        deploy_zones = list(set(gate_nodes + [h["id"] for h in hotspots]))
        for zone in deploy_zones:
            for rtype in ["police", "medic", "firefighter"]:
                r = simulator.deploy_responders(zone, rtype, 2)
                deploy_results.append(r)
        # Create incident
        inc = simulator.create_incident(
            deploy_zones[0] if deploy_zones else "gate_a",
            "security", "code_red"
        )
    elif severity == "code_yellow":
        # Targeted deployment: police to hotspots
        hotspots = simulator.get_hotspots()
        for h in hotspots:
            r = simulator.deploy_responders(h["id"], "police", 3)
            deploy_results.append(r)
        inc = simulator.create_incident(
            hotspots[0]["id"] if hotspots else "gate_a",
            "security", "code_yellow"
        )
    else:
        inc = None

    return jsonify({
        "status": "emergency_activated",
        "severity": severity,
        "phase": "post_event",
        "evacuations": evac_actions,
        "responder_deployments": deploy_results,
        "incident": inc,
        "message": f"🚨 Emergency ({severity.replace('_', ' ').upper()}) activated. All fans directed to nearest exits with priority passes.",
    })


# --- First Responder API Routes ---

@app.route("/api/responders/deploy", methods=["POST"])
def deploy_responders():
    """Deploy responders to a zone."""
    data = request.get_json() or {}
    node_id = data.get("node_id", "")
    rtype = data.get("type", "")
    count = data.get("count", 1)
    result = simulator.deploy_responders(node_id, rtype, count)
    return jsonify(result)


@app.route("/api/responders/recall", methods=["POST"])
def recall_responders():
    """Recall responders from a zone."""
    data = request.get_json() or {}
    node_id = data.get("node_id", "")
    rtype = data.get("type", "")
    result = simulator.recall_responders(node_id, rtype)
    return jsonify(result)


@app.route("/api/responders/status", methods=["GET"])
def responder_status():
    """Get all responder deployments."""
    return jsonify(simulator.get_responder_summary())


@app.route("/api/incident/create", methods=["POST"])
def create_incident():
    """Create an incident report."""
    data = request.get_json() or {}
    node_id = data.get("node_id", "")
    inc_type = data.get("type", "other")
    severity = data.get("severity", "code_yellow")
    result = simulator.create_incident(node_id, inc_type, severity)
    return jsonify(result)


@app.route("/api/incident/resolve", methods=["POST"])
def resolve_incident():
    """Resolve an active incident."""
    data = request.get_json() or {}
    incident_id = data.get("incident_id", "")
    result = simulator.resolve_incident(incident_id)
    return jsonify(result)


@app.route("/api/incidents", methods=["GET"])
def list_incidents():
    """List active incidents."""
    active = [i for i in simulator.incidents if i["status"] == "active"]
    return jsonify({"incidents": active, "count": len(active)})


@app.route("/api/density-history", methods=["GET"])
def density_history():
    """Return density history for sparkline chart."""
    history = []
    for h in simulator.history:
        total = sum(s["crowd"] for s in h["snapshot"].values())
        total_cap = sum(STADIUM_NODES[nid]["capacity"] for nid in h["snapshot"])
        history.append({
            "tick": h["tick"],
            "density": round(total / total_cap, 3) if total_cap else 0,
            "phase": h["phase"],
        })
    return jsonify({"history": history})


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
