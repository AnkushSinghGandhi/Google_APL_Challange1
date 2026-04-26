/**
 * EventFlow AI — Production Frontend
 * Stadium visualization, toasts, emergency mode, sparkline, sound effects.
 */

// ---- Node Layout ----
const NODE_LAYOUT = {
    gate_a: { x: 13, y: 13, emoji: '🚪', label: 'Gate A' },
    gate_b: { x: 87, y: 13, emoji: '🚪', label: 'Gate B' },
    gate_c: { x: 13, y: 87, emoji: '🚪', label: 'Gate C' },
    main_stand: { x: 42, y: 42, emoji: '🏟️', label: 'Main Stand' },
    east_stand: { x: 72, y: 42, emoji: '🏟️', label: 'East Stand' },
    food_court: { x: 38, y: 16, emoji: '🍔', label: 'Food Court' },
    merch_store: { x: 82, y: 72, emoji: '🛍️', label: 'Merch Store' },
    restrooms: { x: 28, y: 72, emoji: '🚻', label: 'Restrooms' },
    medical_tent: { x: 55, y: 90, emoji: '⛑️', label: 'Medical Tent' },
};

const CONNECTIONS = [
    ['gate_a', 'main_stand'], ['gate_a', 'food_court'],
    ['gate_b', 'east_stand'], ['gate_b', 'merch_store'],
    ['gate_c', 'main_stand'], ['gate_c', 'restrooms'], ['gate_c', 'medical_tent'],
    ['main_stand', 'food_court'], ['main_stand', 'restrooms'],
    ['east_stand', 'merch_store'], ['east_stand', 'restrooms'],
    ['food_court', 'merch_store'],
    ['restrooms', 'medical_tent'],
];

const CONGESTION_COLORS = {
    low: '#34a853', medium: '#fbbc04', high: '#f97316', critical: '#ea4335',
};

// ---- State ----
let currentState = null;
let autoInterval = null;
let isAutoRunning = false;
let totalAiActions = 0;
let totalRewards = 0;
let previousCrowds = {};
let densityHistory = [];
let lastCriticalAlert = 0;

// ---- Web Audio for alerts ----
const AudioCtx = window.AudioContext || window.webkitAudioContext;
let audioCtx = null;

function playAlertSound(type = 'warning') {
    try {
        if (!audioCtx) audioCtx = new AudioCtx();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        gain.gain.value = 0.08;

        if (type === 'critical') {
            osc.frequency.value = 880;
            osc.type = 'square';
            gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.4);
            osc.start();
            osc.stop(audioCtx.currentTime + 0.4);
        } else if (type === 'emergency') {
            osc.frequency.value = 600;
            osc.type = 'sawtooth';
            gain.gain.setValueAtTime(0.12, audioCtx.currentTime);
            gain.gain.linearRampToValueAtTime(0, audioCtx.currentTime + 1);
            osc.frequency.setValueAtTime(600, audioCtx.currentTime);
            osc.frequency.linearRampToValueAtTime(1200, audioCtx.currentTime + 0.5);
            osc.frequency.linearRampToValueAtTime(600, audioCtx.currentTime + 1);
            osc.start();
            osc.stop(audioCtx.currentTime + 1);
        } else if (type === 'success') {
            osc.frequency.value = 523;
            osc.type = 'sine';
            gain.gain.value = 0.06;
            gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.2);
            osc.start();
            osc.stop(audioCtx.currentTime + 0.2);
            // Second note
            setTimeout(() => {
                const o2 = audioCtx.createOscillator();
                const g2 = audioCtx.createGain();
                o2.connect(g2); g2.connect(audioCtx.destination);
                o2.frequency.value = 659; o2.type = 'sine';
                g2.gain.value = 0.06;
                g2.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.3);
                o2.start(); o2.stop(audioCtx.currentTime + 0.3);
            }, 120);
        } else {
            osc.frequency.value = 440;
            osc.type = 'triangle';
            gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.25);
            osc.start();
            osc.stop(audioCtx.currentTime + 0.25);
        }
    } catch (e) { /* Audio not available */ }
}

// ---- Toast Notifications ----
function showToast(title, message, type = 'info') {
    const container = document.getElementById('toast-container');
    const icons = { success: '✅', warning: '⚠️', danger: '🚨', info: 'ℹ️' };
    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.innerHTML = `
        <span class="toast-icon">${icons[type] || 'ℹ️'}</span>
        <div class="toast-body">
            <span class="toast-title">${title}</span>
            <span class="toast-message">${message}</span>
        </div>
    `;
    container.appendChild(el);

    // Auto remove after 4s
    setTimeout(() => {
        el.classList.add('toast-exit');
        setTimeout(() => el.remove(), 300);
    }, 4000);

    // Keep max 4 toasts
    while (container.children.length > 4) {
        container.removeChild(container.firstChild);
    }
}

// ---- API Helpers ----
async function apiGet(url) { return (await fetch(url)).json(); }
async function apiPost(url, body = {}) {
    return (await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    })).json();
}

// ---- Sparkline ----
function drawSparkline(data) {
    const canvas = document.getElementById('density-sparkline');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;

    ctx.clearRect(0, 0, w, h);

    if (data.length < 2) return;

    const recent = data.slice(-30); // Last 30 ticks
    const max = Math.max(...recent.map(d => d.density), 0.5);
    const step = w / (recent.length - 1);

    // Fill gradient
    const grad = ctx.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, 'rgba(99, 102, 241, 0.3)');
    grad.addColorStop(1, 'rgba(99, 102, 241, 0)');

    ctx.beginPath();
    ctx.moveTo(0, h);
    recent.forEach((d, i) => {
        const x = i * step;
        const y = h - (d.density / max) * (h - 4);
        if (i === 0) ctx.lineTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.lineTo(w, h);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    // Line
    ctx.beginPath();
    recent.forEach((d, i) => {
        const x = i * step;
        const y = h - (d.density / max) * (h - 4);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = '#6366f1';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Dot at end
    const lastX = (recent.length - 1) * step;
    const lastY = h - (recent[recent.length - 1].density / max) * (h - 4);
    ctx.beginPath();
    ctx.arc(lastX, lastY, 2.5, 0, Math.PI * 2);
    ctx.fillStyle = '#6366f1';
    ctx.fill();
}

// ---- SVG Capacity Ring ----
function createCapacityRingSVG(crowd, capacity, color) {
    const ratio = Math.min(crowd / capacity, 1.2);
    const circumference = 2 * Math.PI * 33;
    const dashoffset = circumference * (1 - Math.min(ratio, 1));
    return `
        <svg width="76" height="76" viewBox="0 0 76 76" class="capacity-ring-svg">
            <circle cx="38" cy="38" r="33" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="3"/>
            <circle cx="38" cy="38" r="33" fill="none" stroke="${color}" stroke-width="3"
                stroke-dasharray="${circumference}" stroke-dashoffset="${dashoffset}"
                stroke-linecap="round" transform="rotate(-90 38 38)"
                style="transition: stroke-dashoffset 0.6s ease, stroke 0.4s ease;"/>
        </svg>
    `;
}

// ---- Stadium Map ----
function renderStadiumMap(state) {
    const container = document.getElementById('stadium-map');
    const rect = container.getBoundingClientRect();
    const w = rect.width || 700;
    const h = rect.height || 450;
    container.innerHTML = '';

    // Connection lines
    CONNECTIONS.forEach(([fromId, toId]) => {
        const from = NODE_LAYOUT[fromId], to = NODE_LAYOUT[toId];
        if (!from || !to) return;
        const x1 = (from.x / 100) * w, y1 = (from.y / 100) * h;
        const x2 = (to.x / 100) * w, y2 = (to.y / 100) * h;
        const length = Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2);
        const angle = Math.atan2(y2 - y1, x2 - x1) * (180 / Math.PI);

        const line = document.createElement('div');
        line.className = 'connection-line';
        line.style.left = `${x1}px`;
        line.style.top = `${y1}px`;
        line.style.width = `${length}px`;
        line.style.transform = `rotate(${angle}deg)`;
        line.innerHTML = `
            <div class="connection-line-bg"></div>
            <div class="connection-particle" style="--duration: ${2.5 + Math.random() * 2}s; animation-delay: ${Math.random() * 3}s"></div>
        `;
        container.appendChild(line);
    });

    // Nodes
    if (!state || !state.nodes) return;
    Object.entries(state.nodes).forEach(([nodeId, node]) => {
        const layout = NODE_LAYOUT[nodeId];
        if (!layout) return;
        const x = (layout.x / 100) * w, y = (layout.y / 100) * h;
        const congestion = node.congestion || 'low';
        const color = CONGESTION_COLORS[congestion];
        const percent = Math.round((node.crowd / node.capacity) * 100);

        const el = document.createElement('div');
        el.className = 'stadium-node';
        el.style.left = `${x - 38}px`;
        el.style.top = `${y - 50}px`;
        el.innerHTML = `
            <div class="node-ring">
                <div class="node-ring-bg"></div>
                <div class="node-ring-progress">${createCapacityRingSVG(node.crowd, node.capacity, color)}</div>
                <div class="node-inner congestion-${congestion}">
                    <span class="node-emoji">${layout.emoji}</span>
                    <span class="node-count">${node.crowd}</span>
                </div>
            </div>
            <span class="node-label">${layout.label}</span>
            <span class="node-meta"><span>${percent}%</span><span>·</span><span>⏱${node.wait_time}m</span></span>
        `;
        el.addEventListener('click', () => {
            document.getElementById('node-select').value = nodeId;
            document.getElementById('deploy-zone').value = nodeId;
        });
        container.appendChild(el);
    });

    // Render responder markers on nodes
    if (state.responders) {
        renderResponderMarkers(state, container, w, h);
    }

    // Save for delta
    Object.entries(state.nodes).forEach(([nid, n]) => { previousCrowds[nid] = n.crowd; });
}

// ---- Stats ----
function updateStats(state) {
    if (!state) return;
    document.getElementById('tick-counter').textContent = state.tick || 0;
    document.getElementById('crowd-count').textContent = state.total_crowd || 0;
    const density = Math.round((state.overall_density || 0) * 100);
    document.getElementById('density-value').textContent = `${density}%`;

    const chip = document.getElementById('density-chip');
    chip.style.borderColor =
        density > 85 ? 'var(--congestion-critical)' :
            density > 70 ? 'var(--congestion-high)' :
                density > 50 ? 'var(--congestion-medium)' : 'var(--congestion-low)';

    let counts = { low: 0, medium: 0, high: 0, critical: 0 };
    if (state.nodes) {
        Object.values(state.nodes).forEach(n => {
            counts[n.congestion] = (counts[n.congestion] || 0) + 1;
        });
    }
    document.getElementById('count-low').textContent = counts.low;
    document.getElementById('count-medium').textContent = counts.medium;
    document.getElementById('count-high').textContent = counts.high;
    document.getElementById('count-critical').textContent = counts.critical;
    document.getElementById('hotspot-count').textContent = (state.hotspots || []).length;
    document.getElementById('ai-action-count').textContent = totalAiActions;
    document.getElementById('reward-count').textContent = totalRewards;

    // Sound alert for critical zones
    if (counts.critical > 0) {
        const now = Date.now();
        if (now - lastCriticalAlert > 8000) {
            lastCriticalAlert = now;
            playAlertSound('critical');
            showToast('Critical Congestion', `${counts.critical} zone(s) at critical capacity!`, 'danger');
        }
    }

    // Update responder stats
    if (state.responder_summary) {
        const rs = state.responder_summary;
        if (rs.firefighter) {
            document.getElementById('fire-deployed').textContent = rs.firefighter.deployed;
            document.getElementById('fire-available').textContent = rs.firefighter.available;
        }
        if (rs.police) {
            document.getElementById('police-deployed').textContent = rs.police.deployed;
            document.getElementById('police-available').textContent = rs.police.available;
        }
        if (rs.medic) {
            document.getElementById('medic-deployed').textContent = rs.medic.deployed;
            document.getElementById('medic-available').textContent = rs.medic.available;
        }
    }

    // Update incident banner & list
    updateIncidents(state);

    // Track density history
    densityHistory.push({ tick: state.tick, density: state.overall_density || 0 });
    if (densityHistory.length > 50) densityHistory.shift();
    drawSparkline(densityHistory);
}

// ---- Leaderboard ----
function updateLeaderboard(state) {
    const container = document.getElementById('leaderboard');
    const lb = state.leaderboard || [];
    if (lb.length === 0) {
        container.innerHTML = '<div class="user-result-placeholder"><p>No data</p></div>';
        return;
    }
    container.innerHTML = lb.map((u, i) => `
        <div class="lb-row">
            <div class="lb-rank rank-${i + 1}">${i + 1}</div>
            <span class="lb-name">${u.name}</span>
            <span class="lb-badges">${(u.badges || []).join('')}</span>
            <span class="lb-points">${u.points}</span>
        </div>
    `).join('');
}

// ---- Activity Feed ----
function addActivity(text, type = 'info') {
    const feed = document.getElementById('activity-feed');
    const el = document.createElement('div');
    el.className = 'activity-item';
    const now = new Date();
    const time = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
    const icons = { info: '📋', sim: '⏩', ai: '🤖', reward: '🎁', phase: '🔄', user: '👤', alert: '🚨' };
    el.innerHTML = `<span class="activity-time">${time}</span><span class="activity-text">${icons[type] || '📋'} ${text}</span>`;
    feed.prepend(el);
    while (feed.children.length > 15) feed.removeChild(feed.lastChild);
}

// ---- AI Feed ----
function appendDecision(decision) {
    const feed = document.getElementById('ai-feed');
    const placeholder = feed.querySelector('.ai-placeholder');
    if (placeholder) placeholder.remove();

    const actionsHtml = (decision.actions || []).map(a => `
        <div class="ai-action">
            <span class="action-icon">⚡</span>
            <span class="action-name">${a.function}</span>
            <span style="color:var(--text-muted);font-size:0.58rem">${formatArgs(a.args)}</span>
        </div>
    `).join('');

    totalAiActions += (decision.actions || []).length;

    const el = document.createElement('div');
    el.className = 'ai-decision';
    el.innerHTML = `
        <div class="ai-decision-header">
            <span class="tick-badge">T${decision.tick || '?'}</span>
            <span class="phase-tag">${formatPhase(decision.phase)}</span>
        </div>
        <div class="ai-reasoning">${formatReasoning(decision.reasoning || 'No reasoning.')}</div>
        ${actionsHtml ? `<div class="ai-actions">${actionsHtml}</div>` : ''}
    `;
    feed.prepend(el);
    while (feed.children.length > 8) feed.removeChild(feed.lastChild);
}

function formatReasoning(text) {
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>')
        .replace(/`(.*?)`/g, '<code style="background:rgba(255,255,255,0.08);padding:1px 4px;border-radius:3px;font-family:var(--font-mono);font-size:0.65rem;">$1</code>');
}

function formatArgs(args) {
    if (!args) return '';
    return Object.entries(args).filter(([, v]) => typeof v === 'string' || typeof v === 'number').map(([, v]) => v).slice(0, 3).join(' → ');
}

function formatPhase(phase) {
    return { pre_event: '🎫 Pre', during_event: '⚽ During', halftime: '☕ Half', post_event: '🚪 Post' }[phase] || phase;
}

// ---- User Suggestion ----
function showSuggestion(data) {
    const container = document.getElementById('user-result');
    const user = data.user || {};
    const suggestion = data.suggestion || {};
    container.innerHTML = `
        <div class="suggestion-card">
            <div class="suggestion-user">
                <div class="suggestion-avatar">${(user.name || 'G')[0]}</div>
                <div class="suggestion-user-info">
                    <span class="suggestion-user-name">${user.name || 'Guest'}</span>
                    <span class="suggestion-user-meta">Lv.${user.level || 1} · ${user.points || 0} pts${(user.badges || []).length ? ' · ' + user.badges.join('') : ''}</span>
                </div>
            </div>
            <p class="suggestion-text">${suggestion.suggestion || 'Enjoy the event! 🎉'}</p>
            ${suggestion.reward_type && suggestion.reward_type !== 'none' ? `<span class="suggestion-reward">🎁 ${suggestion.reward_type.replace('_', ' ')}</span>` : ''}
        </div>
    `;
    if (suggestion.reward_type && suggestion.reward_type !== 'none') totalRewards++;
}

// ---- Refresh ----
async function refreshState() {
    try {
        const state = await apiGet('/api/state');
        currentState = state;
        renderStadiumMap(state);
        updateStats(state);
        updateLeaderboard(state);
        totalRewards = (state.recent_rewards || []).length;
    } catch (e) { console.error('Failed to fetch:', e); }
}

// ---- Event Handlers ----
document.addEventListener('DOMContentLoaded', () => {
    refreshState();
    checkKeyStatus();  // Check API key on load
    // Simulate Step
    document.getElementById('btn-simulate').addEventListener('click', async () => {
        const btn = document.getElementById('btn-simulate');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span>';
        try {
            const result = await apiPost('/api/simulate');
            addActivity(`Tick ${result.tick} — ${(result.hotspots || []).length} hotspot(s)`, 'sim');
            await refreshState();
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"/></svg> Step';
        }
    });

    // Auto-run
    document.getElementById('btn-auto').addEventListener('click', () => {
        const btn = document.getElementById('btn-auto');
        if (isAutoRunning) {
            clearInterval(autoInterval);
            isAutoRunning = false;
            btn.classList.remove('active');
            btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"/><line x1="19" y1="3" x2="19" y2="21"/></svg> Auto';
            addActivity('Auto-simulation paused', 'info');
        } else {
            isAutoRunning = true;
            btn.classList.add('active');
            btn.innerHTML = '⏸ Pause';
            addActivity('Auto-simulation started', 'info');
            autoInterval = setInterval(async () => {
                const result = await apiPost('/api/simulate');
                addActivity(`Tick ${result.tick} — density ${Math.round(result.overall_density * 100)}%`, 'sim');
                await refreshState();
            }, 2000);
        }
    });

    // Ask Gemini
    document.getElementById('btn-agent').addEventListener('click', async () => {
        const btn = document.getElementById('btn-agent');
        btn.classList.add('loading');
        btn.innerHTML = '<span class="spinner"></span> Thinking...';
        addActivity('Gemini agent activated...', 'ai');
        playAlertSound('success');
        try {
            const decision = await apiPost('/api/agent/decide');
            appendDecision(decision);
            const actionCount = (decision.actions || []).length;
            addActivity(`Gemini took ${actionCount} action(s)`, 'ai');
            if (actionCount > 0) {
                showToast('Gemini AI', `Took ${actionCount} action(s) to optimize crowd flow`, 'success');
            } else {
                showToast('Gemini AI', 'Stadium is flowing smoothly ✅', 'info');
            }
            await refreshState();
        } catch (e) {
            appendDecision({ reasoning: '❌ API error', actions: [], tick: currentState?.tick, phase: currentState?.phase });
            showToast('Error', 'Failed to reach Gemini API', 'danger');
        } finally {
            btn.classList.remove('loading');
            btn.innerHTML = '<span class="gemini-sparkle">✨</span> Ask Gemini';
        }
    });

    // Phase controls
    document.querySelectorAll('.phase-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const phase = btn.dataset.phase;
            document.querySelectorAll('.phase-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            await apiPost('/api/event/phase', { phase });
            addActivity(`Phase → ${formatPhase(phase)}`, 'phase');
            showToast('Phase Changed', `Event is now in ${formatPhase(phase)} mode`, 'info');
            playAlertSound('warning');
            await refreshState();
        });
    });

    // Emergency Mode — Code Yellow
    document.getElementById('btn-code-yellow').addEventListener('click', async () => {
        handleEmergency('code_yellow');
    });

    // Emergency Mode — Code Red
    document.getElementById('btn-code-red').addEventListener('click', async () => {
        handleEmergency('code_red');
    });

    // Deploy Responders
    document.getElementById('btn-deploy').addEventListener('click', async () => {
        const zone = document.getElementById('deploy-zone').value;
        const type = document.getElementById('deploy-type').value;
        const count = parseInt(document.getElementById('deploy-count').value);
        const btn = document.getElementById('btn-deploy');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span>';
        try {
            const result = await apiPost('/api/responders/deploy', { node_id: zone, type, count });
            if (result.error) {
                showToast('Deploy Failed', result.error, 'warning');
            } else {
                const typeEmoji = { firefighter: '🚒', police: '🚔', medic: '🚑' }[type] || '🚨';
                showToast('Deployed', `${typeEmoji} ${result.deployed} ${type}(s) → ${result.node_name}`, 'success');
                addActivity(`${typeEmoji} ${result.deployed} ${type}(s) deployed to ${result.node_name}`, 'alert');
                playAlertSound('success');
            }
            await refreshState();
        } finally {
            btn.disabled = false;
            btn.innerHTML = '🚀 Deploy';
        }
    });

    // Create Incident
    document.getElementById('btn-create-incident').addEventListener('click', async () => {
        const zone = document.getElementById('incident-zone').value;
        const type = document.getElementById('incident-type').value;
        const severity = document.getElementById('incident-severity').value;
        try {
            const result = await apiPost('/api/incident/create', { node_id: zone, type, severity });
            if (result.error) {
                showToast('Error', result.error, 'warning');
            } else {
                showToast('Incident Reported', `${result.id}: ${result.type} at ${result.node_name}`, 'danger');
                addActivity(`📋 Incident ${result.id}: ${result.type} (${result.severity}) at ${result.node_name}`, 'alert');
                playAlertSound('warning');
            }
            await refreshState();
        } catch (e) {
            showToast('Error', 'Failed to create incident', 'danger');
        }
    });

    // User check-in
    document.getElementById('btn-checkin').addEventListener('click', async () => {
        const userId = document.getElementById('user-select').value;
        const nodeId = document.getElementById('node-select').value;
        const btn = document.getElementById('btn-checkin');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span>';
        try {
            const data = await apiPost('/api/user/checkin', { user_id: userId, node_id: nodeId });
            showSuggestion(data);
            addActivity(`${data.user?.name || userId} checked in at ${NODE_LAYOUT[nodeId]?.label || nodeId}`, 'user');
            playAlertSound('success');
            if (data.suggestion?.reward_type && data.suggestion.reward_type !== 'none') {
                showToast('Reward Issued', `${data.user?.name} earned ${data.suggestion.reward_type.replace('_', ' ')}!`, 'success');
            }
            await refreshState();
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg> Check In';
        }
    });

    // Resize
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            if (currentState) renderStadiumMap(currentState);
        }, 200);
    });

    // Dismiss emergency overlay on click
    document.getElementById('emergency-overlay').addEventListener('click', () => {
        document.getElementById('emergency-overlay').classList.remove('active');
        document.getElementById('emergency-overlay').classList.remove('code-yellow');
    });

    // --- API Key Modal ---
    document.getElementById('btn-key-settings').addEventListener('click', () => {
        document.getElementById('key-modal-overlay').classList.add('active');
        checkKeyStatus();
    });

    document.getElementById('key-modal-close').addEventListener('click', () => {
        document.getElementById('key-modal-overlay').classList.remove('active');
    });

    document.getElementById('key-modal-overlay').addEventListener('click', (e) => {
        if (e.target === e.currentTarget) {
            e.currentTarget.classList.remove('active');
        }
    });

    document.getElementById('btn-set-key').addEventListener('click', async () => {
        const input = document.getElementById('key-input');
        const key = input.value.trim();
        if (!key) { showToast('Error', 'Please enter an API key', 'warning'); return; }
        const btn = document.getElementById('btn-set-key');
        btn.disabled = true;
        btn.textContent = 'Setting...';
        try {
            const result = await apiPost('/api/key/set', { key });
            if (result.error) {
                showToast('Error', result.error, 'danger');
            } else {
                showToast('API Key Set', 'Gemini is now active! \uD83D\uDE80', 'success');
                playAlertSound('success');
                input.value = '';
                checkKeyStatus();
            }
        } finally {
            btn.disabled = false;
            btn.textContent = 'Set Key';
        }
    });

    document.getElementById('key-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') document.getElementById('btn-set-key').click();
    });

    document.getElementById('btn-clear-key').addEventListener('click', async () => {
        await apiPost('/api/key/clear');
        showToast('Key Cleared', 'Reverted to environment key or fallback mode', 'info');
        checkKeyStatus();
    });
});

// ---- Emergency Handler ----
async function handleEmergency(severity) {
    const overlay = document.getElementById('emergency-overlay');
    const header = document.getElementById('main-header');
    const title = document.getElementById('emergency-overlay-title');
    const msg = document.getElementById('emergency-overlay-msg');

    playAlertSound('emergency');

    if (severity === 'code_yellow') {
        overlay.classList.add('code-yellow');
        title.textContent = 'CODE YELLOW — ALERT';
        msg.textContent = 'Police deployed to congestion hotspots';
        addActivity('⚠️ CODE YELLOW ACTIVATED — Police deploying to hotspots', 'alert');
    } else {
        overlay.classList.remove('code-yellow');
        title.textContent = 'CODE RED — EMERGENCY EVACUATION';
        msg.textContent = 'All fans directed to nearest exits';
        addActivity('🚨 CODE RED — FULL EMERGENCY EVACUATION', 'alert');
    }

    overlay.classList.add('active');
    header.classList.add('emergency-active');

    document.querySelectorAll('.phase-btn').forEach(b => b.classList.remove('active'));
    document.querySelector('[data-phase="post_event"]').classList.add('active');

    try {
        const result = await apiPost('/api/emergency', { severity });
        showToast('EMERGENCY', result.message, 'danger');

        setTimeout(() => {
            overlay.classList.remove('active');
            overlay.classList.remove('code-yellow');
        }, 3000);

        setTimeout(() => {
            header.classList.remove('emergency-active');
        }, 10000);

        await refreshState();
    } catch (e) {
        showToast('Error', 'Emergency activation failed', 'danger');
        overlay.classList.remove('active');
        overlay.classList.remove('code-yellow');
    }
}

// ---- Responder Markers on Stadium Map ----
function renderResponderMarkers(state, container, w, h) {
    const responders = state.responders || {};
    const RESP_EMOJIS = { firefighter: '🚒', police: '🚔', medic: '🚑' };

    Object.entries(responders).forEach(([nodeId, resp]) => {
        const layout = NODE_LAYOUT[nodeId];
        if (!layout) return;

        const totalResp = (resp.firefighter || 0) + (resp.police || 0) + (resp.medic || 0);
        if (totalResp === 0) return;

        const x = (layout.x / 100) * w;
        const y = (layout.y / 100) * h;

        const markersDiv = document.createElement('div');
        markersDiv.className = 'responder-markers';
        markersDiv.style.left = `${x}px`;
        markersDiv.style.top = `${y + 32}px`;
        markersDiv.style.position = 'absolute';

        Object.entries(resp).forEach(([type, count]) => {
            if (count > 0) {
                const marker = document.createElement('span');
                marker.className = 'responder-marker';
                marker.innerHTML = `${RESP_EMOJIS[type] || '🚨'}<span class="responder-marker-count">${count}</span>`;
                markersDiv.appendChild(marker);
            }
        });

        container.appendChild(markersDiv);
    });
}

// ---- Incident Management ----
function updateIncidents(state) {
    const incidents = state.active_incidents || [];
    const count = incidents.length;

    // Update banner
    const banner = document.getElementById('incident-banner');
    const bannerCount = document.getElementById('incident-banner-count');
    if (count > 0) {
        banner.classList.add('active');
        bannerCount.textContent = count;
    } else {
        banner.classList.remove('active');
    }

    // Update count badge
    document.getElementById('incident-count').textContent = count;

    // Render incident list
    const list = document.getElementById('incident-list');
    if (count === 0) {
        list.innerHTML = '<div class="no-incidents">No active incidents ✅</div>';
        return;
    }

    const INCIDENT_EMOJIS = {
        fire: '🔥', medical: '🏥', security: '🔒', stampede: '🏃',
        structural: '🏗️', weather: '⛈️', other: '📋'
    };

    list.innerHTML = incidents.map(inc => `
        <div class="incident-item">
            <span class="severity-badge severity-${inc.severity}">${inc.severity.replace('_', ' ')}</span>
            <div class="incident-info">
                <span class="incident-type">${INCIDENT_EMOJIS[inc.type] || '📋'} ${inc.type}</span>
                <span class="incident-location">${inc.node_name} · ${inc.id}</span>
            </div>
            <button class="btn-resolve" onclick="resolveIncident('${inc.id}')">
                ✓ Resolve
            </button>
        </div>
    `).join('');
}

async function resolveIncident(incidentId) {
    try {
        const result = await apiPost('/api/incident/resolve', { incident_id: incidentId });
        if (result.error) {
            showToast('Error', result.error, 'warning');
        } else {
            showToast('Resolved', `Incident ${incidentId} resolved`, 'success');
            addActivity(`✅ Incident ${incidentId} resolved`, 'info');
            playAlertSound('success');
        }
        await refreshState();
    } catch (e) {
        showToast('Error', 'Failed to resolve incident', 'danger');
    }
}

// ---- API Key Management ----
async function checkKeyStatus() {
    try {
        const res = await fetch('/api/key/status');
        const data = await res.json();
        updateKeyUI(data);
    } catch {
        updateKeyUI({ has_key: false });
    }
}

function updateKeyUI(status) {
    const btn = document.getElementById('btn-key-settings');
    const dot = document.getElementById('key-status-dot');
    const text = document.getElementById('key-status-text');
    const clearBtn = document.getElementById('btn-clear-key');

    if (status.has_key) {
        btn.classList.add('key-active');
        btn.classList.remove('key-missing');
        dot.classList.add('status-active');
        dot.classList.remove('status-missing');
        const source = status.source === 'user' ? 'User-provided' : 'Environment';
        text.textContent = `✅ Active (${source}) — ${status.masked_key}`;
        clearBtn.style.display = status.source === 'user' ? 'block' : 'none';
    } else {
        btn.classList.remove('key-active');
        btn.classList.add('key-missing');
        dot.classList.remove('status-active');
        dot.classList.add('status-missing');
        text.textContent = '⚠️ No API key — running in fallback mode';
        clearBtn.style.display = 'none';

        // Auto-open modal on first load if no key
        setTimeout(() => {
            document.getElementById('key-modal-overlay').classList.add('active');
        }, 1500);
    }
}
