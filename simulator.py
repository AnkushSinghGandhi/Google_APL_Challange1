"""
Digital Twin Simulator — Stadium Crowd Flow Engine
Simulates crowd movement across stadium nodes with event-phase-aware dynamics.
"""
import random
import copy
from config import STADIUM_NODES, CONGESTION_THRESHOLDS


class StadiumSimulator:
    def __init__(self):
        self.tick = 0
        self.phase = "pre_event"
        self.nodes = {}
        self._init_nodes()
        self.history = []  # list of past states for prediction replay

    def _init_nodes(self):
        """Initialize live node state from config."""
        for node_id, cfg in STADIUM_NODES.items():
            # Pre-event: gates have some people, rest mostly empty
            if cfg["type"] == "gate":
                initial = random.randint(20, 60)
            elif cfg["type"] == "seating":
                initial = random.randint(10, 40)
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

        return {
            "tick": self.tick,
            "phase": self.phase,
            "total_crowd": total_crowd,
            "total_capacity": total_capacity,
            "overall_density": round(total_crowd / total_capacity, 2),
            "hotspots": hotspots,
            "nodes": {nid: {**n} for nid, n in self.nodes.items()},
        }

    def get_node(self, node_id):
        """Get status of a single node."""
        if node_id in self.nodes:
            return {**self.nodes[node_id]}
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
