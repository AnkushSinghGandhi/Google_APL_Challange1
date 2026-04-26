import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# --- Stadium Layout ---
# Each node: id, name, type, capacity, connections (adjacent nodes), attraction scores per phase
STADIUM_NODES = {
    "gate_a": {
        "name": "Gate A (Main Entrance)",
        "type": "gate",
        "capacity": 200,
        "connections": ["main_stand", "food_court"],
        "attraction": {"pre_event": 0.9, "during_event": 0.1, "halftime": 0.1, "post_event": 0.8},
    },
    "gate_b": {
        "name": "Gate B (North Entrance)",
        "type": "gate",
        "capacity": 150,
        "connections": ["east_stand", "merch_store"],
        "attraction": {"pre_event": 0.6, "during_event": 0.1, "halftime": 0.1, "post_event": 0.6},
    },
    "gate_c": {
        "name": "Gate C (South Exit)",
        "type": "gate",
        "capacity": 180,
        "connections": ["main_stand", "restrooms", "medical_tent"],
        "attraction": {"pre_event": 0.4, "during_event": 0.05, "halftime": 0.05, "post_event": 0.9},
    },
    "main_stand": {
        "name": "Main Stand",
        "type": "seating",
        "capacity": 500,
        "connections": ["gate_a", "gate_c", "food_court", "restrooms"],
        "attraction": {"pre_event": 0.7, "during_event": 0.95, "halftime": 0.3, "post_event": 0.1},
    },
    "east_stand": {
        "name": "East Stand",
        "type": "seating",
        "capacity": 400,
        "connections": ["gate_b", "merch_store", "restrooms"],
        "attraction": {"pre_event": 0.5, "during_event": 0.9, "halftime": 0.3, "post_event": 0.1},
    },
    "food_court": {
        "name": "Food Court",
        "type": "amenity",
        "capacity": 120,
        "connections": ["gate_a", "main_stand", "merch_store"],
        "attraction": {"pre_event": 0.3, "during_event": 0.2, "halftime": 0.95, "post_event": 0.3},
    },
    "merch_store": {
        "name": "Merchandise Store",
        "type": "amenity",
        "capacity": 80,
        "connections": ["gate_b", "east_stand", "food_court"],
        "attraction": {"pre_event": 0.4, "during_event": 0.15, "halftime": 0.6, "post_event": 0.5},
    },
    "restrooms": {
        "name": "Restrooms",
        "type": "amenity",
        "capacity": 60,
        "connections": ["main_stand", "east_stand", "gate_c", "medical_tent"],
        "attraction": {"pre_event": 0.2, "during_event": 0.25, "halftime": 0.8, "post_event": 0.2},
    },
    "medical_tent": {
        "name": "Medical Tent",
        "type": "emergency",
        "capacity": 40,
        "connections": ["gate_c", "restrooms"],
        "attraction": {"pre_event": 0.0, "during_event": 0.05, "halftime": 0.05, "post_event": 0.1},
    },
}

# --- Simulation Parameters ---
SIM_TICK_SECONDS = 60  # each step = 1 minute of real time
CONGESTION_THRESHOLDS = {
    "low": 0.5,
    "medium": 0.7,
    "high": 0.85,
    "critical": 1.0,
}

# --- Reward Types ---
REWARD_TYPES = {
    "discount": {"label": "🏷️ 20% Discount", "points": 30},
    "bonus_points": {"label": "⭐ 100 Bonus Points", "points": 100},
    "priority_exit": {"label": "🚪 Priority Exit Pass", "points": 50},
    "free_item": {"label": "🎁 Free Snack Voucher", "points": 75},
}

# --- First Responder Types ---
RESPONDER_TYPES = {
    "firefighter": {"label": "🚒 Firefighter", "emoji": "🚒", "color": "#f97316", "default_available": 12},
    "police": {"label": "🚔 Police", "emoji": "🚔", "color": "#6366f1", "default_available": 15},
    "medic": {"label": "🚑 Medic", "emoji": "🚑", "color": "#22d3ee", "default_available": 10},
}

# --- Incident Severity Levels ---
INCIDENT_SEVERITIES = {
    "code_green": {"label": "✅ Code Green", "level": 0, "color": "#34a853", "description": "Normal — Monitoring"},
    "code_yellow": {"label": "⚠️ Code Yellow", "level": 1, "color": "#fbbc04", "description": "Alert — Deploy police to hotspots"},
    "code_red": {"label": "🚨 Code Red", "level": 2, "color": "#ea4335", "description": "Full Emergency — Deploy all, evacuate"},
}

# --- Incident Types ---
INCIDENT_TYPES = ["fire", "medical", "security", "stampede", "structural", "weather", "other"]
