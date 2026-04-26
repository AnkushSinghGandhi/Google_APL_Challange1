"""
Gemini Agentic Decision Engine
Uses the new google-genai SDK with function calling for true agentic behavior.
"""
import json
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, STADIUM_NODES, RESPONDER_TYPES, INCIDENT_TYPES

# Will be set by app.py after initialization
_simulator = None
_rewards = None
_decision_log = []

# Capacity lookup for prompt building
STADIUM_NODES_CAPS = {nid: cfg["capacity"] for nid, cfg in STADIUM_NODES.items()}


def init_engine(simulator, rewards):
    """Initialize with references to simulator and reward engine."""
    global _simulator, _rewards
    _simulator = simulator
    _rewards = rewards


# --- Tool function implementations ---
def get_node_status(node_id: str) -> dict:
    """Get the current crowd status of a specific stadium zone."""
    result = _simulator.get_node(node_id)
    return result if result else {"error": "Node not found"}


def get_congestion_hotspots() -> list:
    """Get all stadium zones with HIGH or CRITICAL congestion."""
    return _simulator.get_hotspots()


def predict_crowd_flow(minutes_ahead: int) -> list:
    """Run simulation forward to predict future crowd distribution."""
    minutes = min(10, max(1, minutes_ahead))
    predictions = _simulator.predict_future(minutes)
    return [
        {"tick": p["tick"], "hotspots": p["hotspots"], "overall_density": p["overall_density"]}
        for p in predictions
    ]


def issue_reward_to_users(from_node: str, to_node: str, reward_type: str, reason: str) -> dict:
    """Issue a gamification reward to users at a specific node."""
    users_at_node = _rewards.get_users_at_node(from_node)
    results = []
    for user in users_at_node[:5]:
        r = _rewards.issue_reward(user["id"], reward_type, reason)
        results.append(r)
    return {
        "users_rewarded": len(results),
        "from_node": from_node,
        "to_node": to_node,
        "reward_type": reward_type,
        "details": results,
    }


def redistribute_crowd(from_node: str, to_node: str, count: int) -> dict:
    """Move people from one node to another to ease congestion."""
    count = min(50, max(5, count))
    return _simulator.apply_redistribution(from_node, to_node, count)


def broadcast_announcement(message: str, target_nodes: list) -> dict:
    """Send a public announcement to specific stadium zones."""
    return {"status": "broadcasted", "message": message, "target_nodes": target_nodes}


def deploy_emergency_responders(node_id: str, responder_type: str, count: int) -> dict:
    """Deploy first responders to a stadium zone."""
    return _simulator.deploy_responders(node_id, responder_type, count)


def create_incident_report(node_id: str, incident_type: str, severity: str) -> dict:
    """Create an incident report for a zone."""
    return _simulator.create_incident(node_id, incident_type, severity)


def request_backup(node_id: str, reason: str) -> dict:
    """Request additional responder units to a critical zone — deploys all types."""
    results = []
    for rt in RESPONDER_TYPES:
        r = _simulator.deploy_responders(node_id, rt, 3)
        results.append(r)
    return {"status": "backup_deployed", "node_id": node_id, "reason": reason, "deployments": results}


# Map of callable tool functions
TOOL_FUNCTIONS = {
    "get_node_status": get_node_status,
    "get_congestion_hotspots": get_congestion_hotspots,
    "predict_crowd_flow": predict_crowd_flow,
    "issue_reward_to_users": issue_reward_to_users,
    "redistribute_crowd": redistribute_crowd,
    "broadcast_announcement": broadcast_announcement,
    "deploy_emergency_responders": deploy_emergency_responders,
    "create_incident_report": create_incident_report,
    "request_backup": request_backup,
}

# --- Tool declarations for Gemini ---
TOOL_DECLARATIONS = [
    types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="get_node_status",
            description="Get the current crowd status of a specific stadium zone/node including crowd count, capacity, wait time, and congestion level.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "node_id": types.Schema(type="STRING", description="The ID of the stadium node (e.g., 'gate_a', 'food_court', 'main_stand')"),
                },
                required=["node_id"],
            ),
        ),
        types.FunctionDeclaration(
            name="get_congestion_hotspots",
            description="Get all stadium zones that currently have HIGH or CRITICAL congestion levels.",
            parameters=types.Schema(type="OBJECT", properties={}),
        ),
        types.FunctionDeclaration(
            name="predict_crowd_flow",
            description="Run the simulation forward by a specified number of minutes to predict future crowd distribution.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "minutes_ahead": types.Schema(type="INTEGER", description="Number of minutes to simulate ahead (1-10)"),
                },
                required=["minutes_ahead"],
            ),
        ),
        types.FunctionDeclaration(
            name="issue_reward_to_users",
            description="Issue a gamification reward to users at a congested node to incentivize them to move. Types: 'discount', 'bonus_points', 'priority_exit', 'free_item'.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "from_node": types.Schema(type="STRING", description="Node where users currently are (congested zone)"),
                    "to_node": types.Schema(type="STRING", description="Target node to redirect users to (less crowded zone)"),
                    "reward_type": types.Schema(type="STRING", description="Type of reward: 'discount', 'bonus_points', 'priority_exit', 'free_item'"),
                    "reason": types.Schema(type="STRING", description="Human-readable reason for this reward"),
                },
                required=["from_node", "to_node", "reward_type", "reason"],
            ),
        ),
        types.FunctionDeclaration(
            name="redistribute_crowd",
            description="Actively move a number of people from one node to another. Simulates successful crowd guidance.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "from_node": types.Schema(type="STRING", description="Source node to move people from"),
                    "to_node": types.Schema(type="STRING", description="Destination node"),
                    "count": types.Schema(type="INTEGER", description="Number of people to redirect (10-50)"),
                },
                required=["from_node", "to_node", "count"],
            ),
        ),
        types.FunctionDeclaration(
            name="broadcast_announcement",
            description="Send a public announcement to specific stadium zones to guide crowd behavior.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "message": types.Schema(type="STRING", description="The announcement message"),
                    "target_nodes": types.Schema(
                        type="ARRAY",
                        items=types.Schema(type="STRING"),
                        description="List of node IDs to broadcast to",
                    ),
                },
                required=["message", "target_nodes"],
            ),
        ),
        types.FunctionDeclaration(
            name="deploy_emergency_responders",
            description="Deploy first responders (firefighter, police, or medic) to a stadium zone for emergency management. Use when congestion is critical or an incident is reported.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "node_id": types.Schema(type="STRING", description="Node ID to deploy responders to"),
                    "responder_type": types.Schema(type="STRING", description="Type of responder: 'firefighter', 'police', or 'medic'"),
                    "count": types.Schema(type="INTEGER", description="Number of units to deploy (1-10)"),
                },
                required=["node_id", "responder_type", "count"],
            ),
        ),
        types.FunctionDeclaration(
            name="create_incident_report",
            description="Create an incident report for a stadium zone. Types: fire, medical, security, stampede, structural, weather, other. Severities: code_green, code_yellow, code_red.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "node_id": types.Schema(type="STRING", description="Node where the incident is occurring"),
                    "incident_type": types.Schema(type="STRING", description="Type of incident: fire, medical, security, stampede, structural, weather, other"),
                    "severity": types.Schema(type="STRING", description="Severity level: code_green, code_yellow, or code_red"),
                },
                required=["node_id", "incident_type", "severity"],
            ),
        ),
        types.FunctionDeclaration(
            name="request_backup",
            description="Request backup by deploying all responder types (firefighter, police, medic) to a critical zone simultaneously.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "node_id": types.Schema(type="STRING", description="Node ID that needs backup"),
                    "reason": types.Schema(type="STRING", description="Reason for backup request"),
                },
                required=["node_id", "reason"],
            ),
        ),
    ])
]


def agent_decide():
    """Main agentic loop: Send state to Gemini, let it reason and call tools."""
    if not GEMINI_API_KEY:
        return _fallback_decide()

    state = _simulator.get_state()

    system_instruction = """You are EventFlow AI, an intelligent crowd management agent for a live stadium event.
You coordinate both crowd flow AND first responder emergency teams.

Your job is to:
1. Analyze the current stadium crowd state
2. Identify congestion hotspots and potential safety risks
3. Take proactive actions to redistribute crowds using rewards, announcements, and direct guidance
4. Deploy first responders (firefighter, police, medic) when situations are dangerous
5. Create incident reports for emergencies
6. Explain your reasoning clearly

IMPORTANT RULES:
- Always check hotspots first
- If congestion is critical (>85% capacity), take immediate action
- When congestion is CRITICAL and density >90%, deploy police for crowd control
- If multiple zones are critical simultaneously, create an incident report and deploy medics
- During emergency/post_event phase, prioritize responder deployment before reward-based redistribution
- Deploy firefighters proactively if there's a fire-related incident or structural concern
- Deploy medics to medical_tent and any zone with potential injuries from overcrowding
- Prefer giving rewards over broadcasting announcements for non-emergency situations
- Be specific about which nodes to redirect to
- Consider the event phase when making decisions
- Always explain WHY you're taking each action
- Keep your reasoning concise (3-5 sentences max per action)"""

    node_summary = "\n".join([
        f"  - {n['name']} ({nid}): {n['crowd']}/{STADIUM_NODES_CAPS[nid]} people, "
        f"wait: {n['wait_time']}min, congestion: {n['congestion']}"
        for nid, n in state["nodes"].items()
    ])

    # Responder summary
    resp_summary = state.get("responder_summary", {})
    resp_lines = []
    for rt, info in resp_summary.items():
        resp_lines.append(f"  - {rt}: {info['deployed']} deployed, {info['available']} available")
    resp_text = "\n".join(resp_lines) if resp_lines else "  No responder data"

    # Active incidents
    active_inc = state.get("active_incidents", [])
    inc_text = ", ".join([f"{i['id']} ({i['type']}/{i['severity']} at {i['node_name']})" for i in active_inc]) if active_inc else "None"

    user_message = f"""Current stadium state at tick {state['tick']}, phase: {state['phase']}
Overall density: {int(state['overall_density'] * 100)}% ({state['total_crowd']}/{state['total_capacity']})
Hotspots: {', '.join(state['hotspots']) if state['hotspots'] else 'None'}

ZONE STATUS:
{node_summary}

FIRST RESPONDERS:
{resp_text}

ACTIVE INCIDENTS: {inc_text}

Analyze the situation and take actions to manage the crowd. Use your tools to check hotspots, predict flow, issue rewards, redistribute crowd, and deploy first responders as needed. If zones are critical, consider deploying police or medics. Explain your reasoning."""

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        # Start the agentic loop with automatic function calling
        actions_taken = []
        reasoning = ""

        # Use chat-based approach with manual function calling for control
        contents = [types.Content(parts=[types.Part.from_text(text=user_message)], role="user")]

        max_turns = 6
        for turn in range(max_turns):
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=TOOL_DECLARATIONS,
                    temperature=0.7,
                ),
            )

            # Process response parts
            model_parts = []
            function_calls_in_response = []

            for part in response.candidates[0].content.parts:
                model_parts.append(part)
                if part.text:
                    reasoning += part.text + "\n"
                if part.function_call:
                    function_calls_in_response.append(part)

            # Add model response to conversation
            contents.append(types.Content(parts=model_parts, role="model"))

            if not function_calls_in_response:
                break  # No more function calls, done

            # Execute each function call and collect responses
            function_response_parts = []
            for fc_part in function_calls_in_response:
                func_name = fc_part.function_call.name
                func_args = dict(fc_part.function_call.args) if fc_part.function_call.args else {}

                # Execute the function
                if func_name in TOOL_FUNCTIONS:
                    try:
                        result = TOOL_FUNCTIONS[func_name](**func_args)
                    except Exception as e:
                        result = {"error": str(e)}
                else:
                    result = {"error": f"Unknown function: {func_name}"}

                actions_taken.append({
                    "function": func_name,
                    "args": func_args,
                    "result": result,
                })

                function_response_parts.append(
                    types.Part.from_function_response(
                        name=func_name,
                        response={"result": json.dumps(result, default=str)},
                    )
                )

            # Send function results back
            contents.append(types.Content(parts=function_response_parts, role="user"))

        decision = {
            "tick": state["tick"],
            "phase": state["phase"],
            "reasoning": reasoning.strip(),
            "actions": actions_taken,
            "hotspots_before": state["hotspots"],
        }

        _decision_log.append(decision)
        if len(_decision_log) > 20:
            _decision_log.pop(0)

        return decision

    except Exception as e:
        fallback = _fallback_decide()
        fallback["error"] = str(e)
        fallback["reasoning"] = f"⚠️ Gemini API error: {str(e)}\n\n" + fallback.get("reasoning", "")
        return fallback


def _fallback_decide():
    """Rule-based fallback when Gemini is unavailable."""
    state = _simulator.get_state()
    actions = []
    reasoning_parts = ["⚠️ Running in fallback mode (no Gemini API key or API error).\n"]

    hotspots = _simulator.get_hotspots()

    if not hotspots:
        reasoning_parts.append("✅ No congestion hotspots detected. Stadium is flowing smoothly.")
    else:
        critical_count = sum(1 for h in hotspots if h["congestion"] == "critical")

        for hot in hotspots:
            nid = hot["id"]
            connections = hot["connections"]
            best_target = None
            best_crowd = float("inf")
            for conn in connections:
                conn_node = _simulator.get_node(conn)
                if conn_node and conn_node["crowd"] < best_crowd:
                    best_crowd = conn_node["crowd"]
                    best_target = conn

            if best_target:
                reasoning_parts.append(
                    f"🔴 {hot['name']} is {hot['congestion']} ({hot['crowd']} people). "
                    f"Redirecting to {_simulator.get_node(best_target)['name']}."
                )
                users = _rewards.get_users_at_node(nid)
                for u in users[:3]:
                    _rewards.issue_reward(u["id"], "bonus_points", f"Move to {best_target}")
                result = _simulator.apply_redistribution(nid, best_target, 15)
                actions.append({
                    "function": "redistribute_crowd",
                    "args": {"from_node": nid, "to_node": best_target, "count": 15},
                    "result": result,
                })

            # Deploy responders for critical zones
            if hot["congestion"] == "critical":
                reasoning_parts.append(f"🚔 Deploying police to {hot['name']} for crowd control.")
                deploy_result = _simulator.deploy_responders(nid, "police", 2)
                actions.append({
                    "function": "deploy_emergency_responders",
                    "args": {"node_id": nid, "responder_type": "police", "count": 2},
                    "result": deploy_result,
                })

        # If multiple critical zones, create incident
        if critical_count >= 2:
            reasoning_parts.append(f"🚨 Multiple critical zones ({critical_count}) — creating security incident.")
            inc = _simulator.create_incident(hotspots[0]["id"], "security", "code_yellow")
            actions.append({
                "function": "create_incident_report",
                "args": {"node_id": hotspots[0]["id"], "incident_type": "security", "severity": "code_yellow"},
                "result": inc,
            })

    decision = {
        "tick": state["tick"],
        "phase": state["phase"],
        "reasoning": "\n".join(reasoning_parts),
        "actions": actions,
        "hotspots_before": state["hotspots"],
    }
    _decision_log.append(decision)
    return decision


def get_user_suggestion(user_id, node_id):
    """Get a personalized suggestion for a specific user at a node."""
    if not GEMINI_API_KEY:
        return _fallback_user_suggestion(user_id, node_id)

    state = _simulator.get_state()
    node = _simulator.get_node(node_id)
    user = _rewards.get_user(user_id) or {"name": "Guest", "points": 0}

    if not node:
        return {"error": "Invalid node"}

    connected_info = []
    for c in node["connections"]:
        cn = _simulator.get_node(c)
        if cn:
            connected_info.append(f"  - {cn['name']}: {cn['congestion']} ({cn['crowd']} people)")

    prompt = f"""You are EventFlow AI, a friendly stadium assistant. A fan needs your help.

Fan: {user.get('name', 'Guest')} (Level {user.get('level', 1)}, {user.get('points', 0)} points)
Current location: {node['name']} ({node_id})
Zone congestion: {node['congestion']} ({node['crowd']}/{node['capacity']} people, {node['wait_time']}min wait)
Event phase: {state['phase']}

Connected zones:
{chr(10).join(connected_info)}

Give a SHORT, friendly, personalized suggestion (2-3 sentences max). If their zone is congested, suggest a less crowded alternative and mention a reward. If not congested, give a positive message. Be conversational, use emojis.

RESPOND ONLY with valid JSON:
{{"suggestion": "your message here", "reward_type": "discount|bonus_points|priority_exit|free_item|none", "target_node": "node_id or null"}}"""

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.8),
        )
        text = response.text.strip()

        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        result = json.loads(text)

        if result.get("reward_type") and result["reward_type"] != "none":
            _rewards.issue_reward(user_id, result["reward_type"], result.get("suggestion", ""))

        return result

    except Exception as e:
        return _fallback_user_suggestion(user_id, node_id)


def _fallback_user_suggestion(user_id, node_id):
    """Fallback user suggestion without Gemini."""
    node = _simulator.get_node(node_id)
    if not node:
        return {"suggestion": "Welcome! Enjoy the event! 🎉", "reward_type": "none", "target_node": None}

    if node["congestion"] in ("high", "critical"):
        for conn in node["connections"]:
            alt = _simulator.get_node(conn)
            if alt and alt["congestion"] in ("low", "medium"):
                _rewards.issue_reward(user_id, "bonus_points", f"Move to {conn}")
                return {
                    "suggestion": f"⚠️ It's getting crowded here! Head to {alt['name']} for a smoother experience. You'll earn 100 bonus points! ⭐",
                    "reward_type": "bonus_points",
                    "target_node": conn,
                }
        return {"suggestion": "It's busy here but hang tight — we're managing the flow! 💪", "reward_type": "none", "target_node": None}
    else:
        return {"suggestion": f"You're in a great spot! {node['name']} is looking comfortable right now. Enjoy! 🎉", "reward_type": "none", "target_node": None}


def get_decision_history():
    """Return past decisions."""
    return list(_decision_log)
