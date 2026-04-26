"""
Digital Twin Simulator — Stadium Crowd Flow Engine
Simulates crowd movement across stadium nodes with event-phase-aware dynamics.
Includes first responder deployment and incident management.
"""
import random
import copy
import time
from config import STADIUM_NODES, CONGESTION_THRESHOLDS, RESPONDER_TYPES


class StadiumSimulator:
    def __init__(self):
        self.tick = 0
        self.phase = "pre_event"
        self.nodes = {}
        self._init_nodes()
        self.history = []  # list of past states for prediction replay

        # First Responder State
        self.responders = {nid: {rt: 0 for rt in RESPONDER_TYPES} for nid in STADIUM_NODES}
        self.available_responders = {rt: cfg["default_available"] for rt, cfg in RESPONDER_TYPES.items()}
        self.incidents = []  # list of active incidents
        self._incident_counter = 0

    def _init_nodes(self):
        """Initialize live node state from config."""
        for node_id, cfg in STADIUM_NODES.items():
            # Pre-event: gates have some people, rest mostly empty
            if cfg["type"] == "gate":
                initial = random.randint(20, 60)
            elif cfg["type"] == "seating":
                initial = random.randint(10, 40)
            elif cfg["type"] == "emergency":
                initial = random.randint(0, 5)
            else:
                initial = random.randint(5, 20)

            self.nodes[node_id] = {
                "id": node_id,
                "name": cfg["name"],
                "type": cfg["type"],
                "capacity": cfg["capacity"],
                "crowd": initial,
                "wait_time": round(initial / cfg["capacity"] * 8, 1),  # minutes
                "congestion": self._calc_congestion(initial, cfg["capacity"]),
                "connections": cfg["connections"],
            }

    def _calc_congestion(self, crowd, capacity):
        ratio = crowd / capacity
        if ratio < CONGESTION_THRESHOLDS["low"]:
            return "low"
        elif ratio < CONGESTION_THRESHOLDS["medium"]:
            return "medium"
        elif ratio < CONGESTION_THRESHOLDS["high"]:
            return "high"
        else:
            return "critical"

    def _update_derived(self, node_id):
        """Recalculate derived fields for a node."""
        n = self.nodes[node_id]
        cap = STADIUM_NODES[node_id]["capacity"]
        n["crowd"] = max(0, min(n["crowd"], cap + 30))  # slight overflow allowed
        n["wait_time"] = round(n["crowd"] / cap * 8, 1)
        n["congestion"] = self._calc_congestion(n["crowd"], cap)

    def set_phase(self, phase):
        """Change event phase: pre_event, during_event, halftime, post_event"""
        valid = ["pre_event", "during_event", "halftime", "post_event"]
        if phase in valid:
            self.phase = phase
            return True
        return False

    def simulate_step(self):
        """Advance one simulation tick — people flow between nodes."""
        self.tick += 1

        # Save snapshot for history
        self.history.append({
            "tick": self.tick,
            "phase": self.phase,
            "snapshot": {nid: {"crowd": n["crowd"], "congestion": n["congestion"]} for nid, n in self.nodes.items()}
        })
        if len(self.history) > 50:
            self.history = self.history[-50:]

        for node_id, cfg in STADIUM_NODES.items():
            node = self.nodes[node_id]
            attraction = cfg["attraction"][self.phase]

            for conn_id in cfg["connections"]:
                conn_cfg = STADIUM_NODES[conn_id]
                conn_node = self.nodes[conn_id]
                conn_attraction = conn_cfg["attraction"][self.phase]

                # Flow direction: people move toward higher attraction
                if conn_attraction > attraction and node["crowd"] > 5:
                    flow = random.randint(1, max(1, int(node["crowd"] * 0.08)))
                    flow = min(flow, node["crowd"])
                    node["crowd"] -= flow
                    conn_node["crowd"] += flow
                elif attraction > conn_attraction and conn_node["crowd"] > 5:
                    flow = random.randint(0, max(1, int(conn_node["crowd"] * 0.05)))
                    flow = min(flow, conn_node["crowd"])
                    conn_node["crowd"] -= flow
                    node["crowd"] += flow

            # Random walk noise
            node["crowd"] += random.randint(-3, 5)

        # Recalculate derived fields
        for nid in self.nodes:
            self._update_derived(nid)

        return self.get_state()

    def predict_future(self, steps=5):
        """Run simulation N steps ahead on a copy and return predicted state."""
        sim_copy = copy.deepcopy(self)
        predictions = []
        for _ in range(steps):
            state = sim_copy.simulate_step()
            predictions.append(state)
        return predictions

    def get_state(self):
        """Return current full state."""
        total_crowd = sum(n["crowd"] for n in self.nodes.values())
        total_capacity = sum(STADIUM_NODES[nid]["capacity"] for nid in self.nodes)
        hotspots = [nid for nid, n in self.nodes.items() if n["congestion"] in ("high", "critical")]

        # Count deployed responders
        total_deployed = {rt: 0 for rt in RESPONDER_TYPES}
        for nid_resp in self.responders.values():
            for rt, count in nid_resp.items():
                total_deployed[rt] += count

        active_incidents = [i for i in self.incidents if i["status"] == "active"]

        return {
            "tick": self.tick,
            "phase": self.phase,
            "total_crowd": total_crowd,
            "total_capacity": total_capacity,
            "overall_density": round(total_crowd / total_capacity, 2),
            "hotspots": hotspots,
            "nodes": {nid: {**n} for nid, n in self.nodes.items()},
            "responders": {nid: {**r} for nid, r in self.responders.items()},
            "responder_summary": {
                rt: {"deployed": total_deployed[rt], "available": self.available_responders[rt]}
                for rt in RESPONDER_TYPES
            },
            "active_incidents": active_incidents,
            "incident_count": len(active_incidents),
        }

    def get_node(self, node_id):
        """Get status of a single node."""
        if node_id in self.nodes:
            result = {**self.nodes[node_id]}
            result["responders"] = {**self.responders.get(node_id, {})}
            return result
        return None

    def get_hotspots(self):
        """Get all nodes with high/critical congestion."""
        return [
            {**self.nodes[nid]}
            for nid in self.nodes
            if self.nodes[nid]["congestion"] in ("high", "critical")
        ]

    def apply_redistribution(self, from_node, to_node, count):
        """Manually move people between nodes (called by Gemini agent)."""
        if from_node in self.nodes and to_node in self.nodes:
            actual = min(count, self.nodes[from_node]["crowd"])
            self.nodes[from_node]["crowd"] -= actual
            self.nodes[to_node]["crowd"] += actual
            self._update_derived(from_node)
            self._update_derived(to_node)
            return {"moved": actual, "from": from_node, "to": to_node}
        return {"error": "Invalid node IDs"}

    # --- First Responder Methods ---

    def deploy_responders(self, node_id, responder_type, count):
        """Deploy responders of a given type to a node."""
        if node_id not in self.nodes:
            return {"error": f"Unknown node: {node_id}"}
        if responder_type not in RESPONDER_TYPES:
            return {"error": f"Unknown responder type: {responder_type}"}

        count = max(1, min(count, 10))  # Cap per-deployment
        available = self.available_responders[responder_type]
        actual = min(count, available)

        if actual <= 0:
            return {"error": f"No {responder_type} units available", "available": 0}

        self.responders[node_id][responder_type] += actual
        self.available_responders[responder_type] -= actual

        return {
            "status": "deployed",
            "node_id": node_id,
            "node_name": self.nodes[node_id]["name"],
            "responder_type": responder_type,
            "deployed": actual,
            "remaining_available": self.available_responders[responder_type],
        }

    def recall_responders(self, node_id, responder_type):
        """Recall all responders of a type from a node."""
        if node_id not in self.nodes:
            return {"error": f"Unknown node: {node_id}"}
        if responder_type not in RESPONDER_TYPES:
            return {"error": f"Unknown responder type: {responder_type}"}

        recalled = self.responders[node_id][responder_type]
        self.responders[node_id][responder_type] = 0
        self.available_responders[responder_type] += recalled

        return {
            "status": "recalled",
            "node_id": node_id,
            "responder_type": responder_type,
            "recalled": recalled,
            "now_available": self.available_responders[responder_type],
        }

    def create_incident(self, node_id, incident_type, severity):
        """Create a new incident at a node."""
        if node_id not in self.nodes:
            return {"error": f"Unknown node: {node_id}"}

        self._incident_counter += 1
        incident = {
            "id": f"INC-{self._incident_counter:04d}",
            "node_id": node_id,
            "node_name": self.nodes[node_id]["name"],
            "type": incident_type,
            "severity": severity,
            "status": "active",
            "timestamp": time.time(),
            "assigned_responders": [],
        }
        self.incidents.append(incident)
        return incident

    def resolve_incident(self, incident_id):
        """Mark an incident as resolved."""
        for inc in self.incidents:
            if inc["id"] == incident_id and inc["status"] == "active":
                inc["status"] = "resolved"
                inc["resolved_at"] = time.time()
                # Recall responders assigned to this incident's node
                return {"status": "resolved", "incident": inc}
        return {"error": f"Incident {incident_id} not found or already resolved"}

    def get_responder_summary(self):
        """Return a summary of all responder deployments."""
        deployed_by_node = {}
        for nid, resp in self.responders.items():
            total = sum(resp.values())
            if total > 0:
                deployed_by_node[nid] = {
                    "node_name": self.nodes[nid]["name"],
                    **resp,
                    "total": total,
                }
        return {
            "deployed_by_node": deployed_by_node,
            "available": {**self.available_responders},
            "total_deployed": sum(sum(r.values()) for r in self.responders.values()),
        }

