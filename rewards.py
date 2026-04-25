"""
Gamification & Reward Engine
Manages user points, rewards, compliance tracking, and leaderboard.
"""
import random
import time
from config import REWARD_TYPES


class RewardEngine:
    def __init__(self):
        self.users = {}
        self.reward_log = []
        self._seed_users()

    def _seed_users(self):
        """Create some simulated users spread across the stadium."""
        names = [
            "Ankush", "Priya", "Rahul", "Sneha", "Arjun",
            "Meera", "Karan", "Divya", "Rohit", "Ananya",
            "Vikram", "Neha", "Aditya", "Pooja", "Saurabh"
        ]
        locations = ["gate_a", "gate_b", "gate_c", "main_stand", "east_stand", "food_court", "merch_store", "restrooms"]

        for i, name in enumerate(names):
            uid = f"user_{i+1}"
            self.users[uid] = {
                "id": uid,
                "name": name,
                "location": random.choice(locations),
                "points": random.randint(0, 200),
                "level": 1,
                "badges": [],
                "suggestions_followed": 0,
                "suggestions_total": 0,
            }

    def get_user(self, user_id):
        if user_id in self.users:
            return {**self.users[user_id]}
        return None

    def checkin_user(self, user_id, node_id):
        """Update a user's location."""
        if user_id not in self.users:
            # Create new user on the fly
            self.users[user_id] = {
                "id": user_id,
                "name": f"Fan-{user_id[-3:]}",
                "location": node_id,
                "points": 0,
                "level": 1,
                "badges": [],
                "suggestions_followed": 0,
                "suggestions_total": 0,
            }
        else:
            self.users[user_id]["location"] = node_id
        return self.users[user_id]

    def issue_reward(self, user_id, reward_type, reason=""):
        """Issue a reward to a user."""
        if reward_type not in REWARD_TYPES:
            return {"error": f"Unknown reward type: {reward_type}"}

        reward = REWARD_TYPES[reward_type]

        if user_id not in self.users:
            return {"error": f"Unknown user: {user_id}"}

        self.users[user_id]["points"] += reward["points"]
        self._check_level_up(user_id)

        entry = {
            "user_id": user_id,
            "user_name": self.users[user_id]["name"],
            "reward_type": reward_type,
            "reward_label": reward["label"],
            "points_earned": reward["points"],
            "reason": reason,
            "timestamp": time.time(),
        }
        self.reward_log.append(entry)
        if len(self.reward_log) > 100:
            self.reward_log = self.reward_log[-100:]

        return entry

    def record_suggestion(self, user_id, followed=True):
        """Track if user followed a suggestion."""
        if user_id in self.users:
            self.users[user_id]["suggestions_total"] += 1
            if followed:
                self.users[user_id]["suggestions_followed"] += 1

    def _check_level_up(self, user_id):
        u = self.users[user_id]
        new_level = 1 + u["points"] // 150
        if new_level > u["level"]:
            u["level"] = new_level
            badge_map = {2: "🥉 Bronze Fan", 3: "🥈 Silver Fan", 4: "🥇 Gold Fan", 5: "💎 Diamond Fan"}
            if new_level in badge_map and badge_map[new_level] not in u["badges"]:
                u["badges"].append(badge_map[new_level])

    def get_leaderboard(self, top_n=10):
        """Return top N users by points."""
        sorted_users = sorted(self.users.values(), key=lambda u: u["points"], reverse=True)
        return [
            {
                "rank": i + 1,
                "id": u["id"],
                "name": u["name"],
                "points": u["points"],
                "level": u["level"],
                "badges": u["badges"],
                "compliance": round(u["suggestions_followed"] / max(1, u["suggestions_total"]) * 100),
            }
            for i, u in enumerate(sorted_users[:top_n])
        ]

    def get_users_at_node(self, node_id):
        """Get all users currently at a specific node."""
        return [u for u in self.users.values() if u["location"] == node_id]

    def get_recent_rewards(self, n=10):
        return self.reward_log[-n:]
