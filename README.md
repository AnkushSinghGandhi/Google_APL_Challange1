# 🏟️ EventFlow AI — Agentic Crowd Orchestrator

> **Google Agentic Premier League 2026 Hackathon Project**

EventFlow AI is a high-impact crowd management system that combines a **Digital Twin** stadium simulation with **Gemini's Agentic Reasoning** and **Gamification** to dynamically redistribute crowds and prevent dangerous congestion in real-time.

![Dashboard Preview](dashboard_preview.png)

## 🌟 Standout Features

### 1. 🤖 True Agentic Reasoning (Not just a chatbot)
Most AI projects just chat. EventFlow AI uses the new `google-genai` SDK for **Function Calling**. Gemini gets full context of the stadium capacity and can autonomously execute tools like `redistribute_crowd`, `broadcast_message`, and `issue_discount_reward` to proactively solve congestion hotspots.

### 2. 🗺️ Robust Digital Twin Simulator
A fully modeled stadium with 8 interconnected nodes (Gates, Stands, Food Court, Restrooms, Merch). The crowd dynamically flows between them based on the **Event Phase** (Pre-Event, During, Halftime, Post-Event). 

### 3. 🚨 Emergency Evacuation Mode
A single-click emergency mode that instantly triggers visual/audio alarms, shifts the simulation into "Post Event" phase, and forces aggressive redistribution parameters to guide fans to the nearest exits.

### 4. 🎮 Gamification & Rewards
You can't physically move fans, so we nudge their behavior using rewards. Gemini dynamically issues targeted incentives (e.g., "15% off Merch Store") to fans in congested areas, steering them to lower-density zones.

### 5. 💎 Premium Dashboard
A production-grade, dark-mode UI featuring:
* Glassmorphism and modern gradient styling
* Real-time SVG capacity rings and animated particle flows
* Live Activity Feed & Density Trend Sparklines
* Sound effects for alarms and success states (Web Audio API)
* Native toast notifications

## 🛠️ Tech & AI Development Stack

**Core Technology:**
* **AI:** Google Gemini (`google-genai` SDK) for runtime function calling
* **Backend:** Python / Flask
* **Frontend:** Vanilla JS / HTML5 / Advanced CSS3
* **No external DB required** (In-memory simulation state for easy demo)

**AI Development Tools Used:**
This project was built using state-of-the-art AI coding assistants:
* **Antigravity:** Google DeepMind's agentic coding assistant
* **Gemini 3.1 Pro model:** Primary reasoning engine for code generation
* **Gemini 3 Flash model:** Optimized model for rapid iterations and micro-tasks
* **Claude Opus 4.6:** Advanced reasoning for architecture and design planning

**Developed By:**
* **Ankush Singh Gandhi** — [warriorwhocodes.com](https://warriorwhocodes.com)
* **Deployed Using:** Google Cloud Platform (GCP)

## 🚀 How to Run

1. **Clone & Setup:**
```bash
git clone https://github.com/your-username/eventflow-ai.git
cd eventflow-ai
pip install -r requirements.txt
```

2. **Add API Key:**
Create a `.env` file in the root directory:
```
GEMINI_API_KEY=your_gemini_api_key_here
```
*(Note: The app will run in "Fallback Mode" using rule-based logic if no key is provided, ensuring your demo never crashes!)*

3. **Start the Server:**
```bash
python app.py
```

4. **Navigate:** Open `http://localhost:5000` in your browser.

## 💡 Demo Script

1. **Start** in the *Pre-Event* phase. Show crowds flowing into the gates.
2. Switch to **Halftime** and hit *Step* a few times. Watch the Food Court and Restrooms hit critical mass (red rings, audio alarm sounds).
3. Hit the **Ask Gemini** button. Watch the AI reason about the congestion and take action to clear the bottleneck.
4. Click the **🚨 Emergency** button to show the full evacuation overlay and alarm.
5. Check in as a Fan to show the personalized rewards system.

---

## 🧠 The Journey: Ideation & Vision

### The Original Idea
When thinking about the Google Agentic Premier League, I wanted to solve a real-world, high-stakes problem. Crowd crushes and stadium bottlenecks are incredibly dangerous and notoriously hard to manage. My idea was: **What if an AI didn't just *monitor* a crowd, but actively *managed* it?** 

By combining a Digital Twin simulator with an Agentic AI, the system could foresee bottlenecks. Since we can't physically move people, I introduced **gamification**—using targeted discounts and rewards to nudge crowd behavior naturally and safely.

### What I Could Have Done More (Future Scope)
Given more time, I would expand EventFlow AI with:
1. **Computer Vision Integration:** Instead of a simulator, hook the backend up to live stadium CCTV feeds using a vision model to calculate real-time density.
2. **Mobile App Push Notifications:** Deep integration with a stadium's ticketing app to send live, personalized routing instructions directly to fans' phones.
3. **Predictive Weather & Transport Factors:** Feed Gemini live weather data and transit schedules so it can preemptively manage crowds (e.g., holding fans inside if a sudden thunderstorm hits the exits).
4. **Dynamic Pricing Integration:** Automatically adjust food and merch prices on digital menus based on AI congestion data.

### Behind the Scenes: Prompts I Used to Build This
I collaborated extensively with AI to bring this vision to life. Here are some of the core prompts I gave my AI assistants to build the system:

* *"I'm participating in the Google Agentic Premier League hackathon. I want to build a Python Flask app that acts as an Agentic Crowd Orchestrator for a stadium. First, build a 'Digital Twin' simulator with 8 connected nodes (Gates, Stands, Food Court) where people flow based on event phases."*
* *"Now, integrate the new `google-genai` SDK. I want to give Gemini 'tools' (function calling) like `redistribute_crowd` and `issue_discount_reward`. Feed Gemini the simulator's state and let it autonomously decide how to solve congestion."*
* *"Design a premium, production-grade frontend dashboard. It must be dark mode, use glassmorphism, and have a real-time SVG map of the stadium that changes color from green to red based on density. Add an 'Activity Feed' so judges can see exactly what Gemini is reasoning and doing."*
* *"Add standout features to impress the judges: An emergency evacuation mode that turns the screen red and blares a Web Audio siren, and a density history sparkline chart to show trends."*

---
*Built with ❤️ for the Google Agentic Premier League.*
