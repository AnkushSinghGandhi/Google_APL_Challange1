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
    """Activate emergency evacuation mode."""
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

    return jsonify({
        "status": "emergency_activated",
        "phase": "post_event",
        "evacuations": evac_actions,
        "message": "🚨 Emergency evacuation initiated. All fans directed to nearest exits with priority passes.",
    })


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
    app.run(debug=True, port=5000)
