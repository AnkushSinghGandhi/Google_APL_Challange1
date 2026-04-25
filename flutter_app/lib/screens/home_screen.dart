import 'dart:async';
import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../widgets/zone_card.dart';

const Map<String, String> _nodeEmojis = {
  'gate_a': '🚪', 'gate_b': '🚪', 'gate_c': '🚪',
  'main_stand': '🏟️', 'east_stand': '🏟️',
  'food_court': '🍔', 'merch_store': '🛍️', 'restrooms': '🚻',
};

const Map<String, String> _nodeNames = {
  'gate_a': 'Gate A', 'gate_b': 'Gate B', 'gate_c': 'Gate C',
  'main_stand': 'Main Stand', 'east_stand': 'East Stand',
  'food_court': 'Food Court', 'merch_store': 'Merch Store', 'restrooms': 'Restrooms',
};

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  Map<String, dynamic>? _state;
  String? _selectedNode;
  String _selectedUser = 'user_1';
  Map<String, dynamic>? _checkinResult;
  bool _loading = false;
  bool _emergency = false;
  bool _geminiLoading = false;
  String? _geminiReasoning;
  Timer? _pollTimer;

  final List<Map<String, String>> _users = [
    {'id': 'user_1', 'name': 'Ankush'},
    {'id': 'user_2', 'name': 'Priya'},
    {'id': 'user_3', 'name': 'Rahul'},
    {'id': 'user_4', 'name': 'Sneha'},
    {'id': 'user_5', 'name': 'Arjun'},
  ];

  @override
  void initState() {
    super.initState();
    _fetchState();
    _pollTimer = Timer.periodic(const Duration(seconds: 3), (_) => _fetchState());
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  Future<void> _fetchState() async {
    try {
      final state = await ApiService.getState();
      if (mounted) {
        setState(() {
          _state = state;
          // Check for emergency (phase == post_event with critical zones)
          final phase = state['phase'] ?? '';
          if (phase == 'post_event' && !_emergency) {
            // Could be normal post-event, only flash if triggered from button
          }
        });
      }
    } catch (e) {
      // Silently fail on poll errors
    }
  }

  Future<void> _doCheckIn() async {
    if (_selectedNode == null) {
      _showSnack('Select a zone first!', Colors.orange);
      return;
    }
    setState(() => _loading = true);
    try {
      final result = await ApiService.checkIn(_selectedUser, _selectedNode!);
      setState(() {
        _checkinResult = result;
        _loading = false;
      });
      final reward = result['suggestion']?['reward_type'] ?? 'none';
      if (reward != 'none') {
        _showSnack('🎁 Reward: ${reward.toString().replaceAll('_', ' ')}!', const Color(0xFF34A853));
      } else {
        _showSnack('✅ Checked in!', const Color(0xFF4285F4));
      }
      _fetchState();
    } catch (e) {
      setState(() => _loading = false);
      _showSnack('❌ Connection error', Colors.red);
    }
  }

  Future<void> _doSimulate() async {
    try {
      await ApiService.simulate();
      _fetchState();
    } catch (_) {}
  }

  Future<void> _doAskGemini() async {
    setState(() => _geminiLoading = true);
    try {
      final result = await ApiService.askGemini();
      setState(() {
        _geminiLoading = false;
        _geminiReasoning = result['reasoning'] ?? 'No reasoning returned';
      });
      final actions = (result['actions'] as List?)?.length ?? 0;
      _showSnack('🤖 Gemini took $actions action(s)', const Color(0xFFA855F7));
      _fetchState();
    } catch (e) {
      setState(() {
        _geminiLoading = false;
        _geminiReasoning = 'Error contacting Gemini API';
      });
      _showSnack('❌ Gemini API error', Colors.red);
    }
  }

  Future<void> _doEmergency() async {
    setState(() => _emergency = true);
    _showSnack('🚨 Emergency evacuation activated!', const Color(0xFFEA4335));
    try {
      await ApiService.triggerEmergency();
      _fetchState();
    } catch (_) {}
    // Auto-dismiss after 5s
    Future.delayed(const Duration(seconds: 5), () {
      if (mounted) setState(() => _emergency = false);
    });
  }

  void _showSnack(String text, Color color) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(text, style: const TextStyle(fontWeight: FontWeight.w600)),
        backgroundColor: color.withOpacity(0.9),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        duration: const Duration(seconds: 2),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          // Background gradient
          Container(
            decoration: const BoxDecoration(
              gradient: RadialGradient(
                center: Alignment(-0.8, -0.6),
                radius: 1.5,
                colors: [Color(0x194285F4), Color(0xFF060A14)],
              ),
            ),
          ),

          SafeArea(
            child: Column(
              children: [
                _buildHeader(),
                _buildStatsBar(),
                Expanded(
                  child: _state == null
                      ? const Center(child: CircularProgressIndicator())
                      : _buildBody(),
                ),
                _buildBottomBar(),
              ],
            ),
          ),

          // Emergency Overlay
          if (_emergency)
            _buildEmergencyOverlay(),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: BoxDecoration(
        color: _emergency ? const Color(0xFFEA4335).withOpacity(0.1) : Colors.transparent,
        border: Border(
          bottom: BorderSide(
            color: _emergency ? const Color(0xFFEA4335).withOpacity(0.4) : Colors.white.withOpacity(0.05),
          ),
        ),
      ),
      child: Row(
        children: [
          // Logo
          ShaderMask(
            shaderCallback: (bounds) => const LinearGradient(
              colors: [Color(0xFF4285F4), Color(0xFFA855F7), Color(0xFFEA4335)],
            ).createShader(bounds),
            child: const Text(
              'EventFlow AI',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: Colors.white),
            ),
          ),
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: const Color(0xFFEA4335).withOpacity(0.12),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: const Color(0xFFEA4335).withOpacity(0.25)),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 6, height: 6,
                  decoration: const BoxDecoration(shape: BoxShape.circle, color: Color(0xFFEA4335)),
                ),
                const SizedBox(width: 4),
                const Text('LIVE', style: TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: Color(0xFFEA4335), letterSpacing: 1)),
              ],
            ),
          ),
          const Spacer(),
          // Phase badge
          if (_state != null)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: const Color(0xFF6366F1).withOpacity(0.12),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                _formatPhase(_state!['phase'] ?? ''),
                style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Color(0xFF6366F1)),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildStatsBar() {
    final tick = _state?['tick'] ?? 0;
    final totalCrowd = _state?['total_crowd'] ?? 0;
    final density = ((_state?['overall_density'] ?? 0) * 100).round();

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      color: Colors.black.withOpacity(0.3),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
        children: [
          _statChip('⏱', 'Tick', '$tick'),
          _statChip('📊', 'Density', '$density%'),
          _statChip('👥', 'Crowd', '$totalCrowd'),
          _statChip('🔥', 'Hotspots', '${(_state?['hotspots'] as List?)?.length ?? 0}'),
        ],
      ),
    );
  }

  Widget _statChip(String icon, String label, String value) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(icon, style: const TextStyle(fontSize: 14)),
        const SizedBox(height: 2),
        Text(value, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700, fontFamily: 'monospace')),
        Text(label, style: TextStyle(fontSize: 9, color: Colors.white.withOpacity(0.4), letterSpacing: 0.5)),
      ],
    );
  }

  Widget _buildBody() {
    final nodes = _state!['nodes'] as Map<String, dynamic>? ?? {};

    return ListView(
      padding: const EdgeInsets.only(top: 8, bottom: 8),
      children: [
        // Section: Zones
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
          child: Row(
            children: [
              const Text('🗺️ Stadium Zones', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
              const Spacer(),
              GestureDetector(
                onTap: _doSimulate,
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                  decoration: BoxDecoration(
                    color: const Color(0xFF6366F1).withOpacity(0.12),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: const Color(0xFF6366F1).withOpacity(0.2)),
                  ),
                  child: const Text('▶ Step', style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Color(0xFF6366F1))),
                ),
              ),
            ],
          ),
        ),
        ...nodes.entries.map((e) {
          final nodeId = e.key;
          final node = e.value as Map<String, dynamic>;
          return ZoneCard(
            name: _nodeNames[nodeId] ?? nodeId,
            emoji: _nodeEmojis[nodeId] ?? '📍',
            crowd: node['crowd'] ?? 0,
            capacity: node['capacity'] ?? 100,
            congestion: node['congestion'] ?? 'low',
            waitTime: (node['wait_time'] ?? 0).round(),
            isSelected: _selectedNode == nodeId,
            onTap: () => setState(() => _selectedNode = nodeId),
          );
        }),

        const SizedBox(height: 12),

        // Gemini Section
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('✦ AI Reasoning', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
              const SizedBox(height: 8),
              if (_geminiReasoning != null)
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xFF6366F1).withOpacity(0.06),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0xFF6366F1).withOpacity(0.12)),
                  ),
                  child: Text(
                    _geminiReasoning!,
                    style: TextStyle(fontSize: 12, height: 1.5, color: Colors.white.withOpacity(0.7)),
                  ),
                ),
              if (_geminiReasoning == null)
                Container(
                  padding: const EdgeInsets.all(20),
                  alignment: Alignment.center,
                  child: Text(
                    'Tap "Ask Gemini" to analyze the stadium',
                    style: TextStyle(fontSize: 12, color: Colors.white.withOpacity(0.3)),
                  ),
                ),
            ],
          ),
        ),

        // Checkin result
        if (_checkinResult != null) ...[
          const SizedBox(height: 12),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: const Color(0xFF34A853).withOpacity(0.06),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFF34A853).withOpacity(0.12)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Text('👤', style: TextStyle(fontSize: 16)),
                      const SizedBox(width: 8),
                      Text(
                        _checkinResult!['user']?['name'] ?? 'Fan',
                        style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                      ),
                      const Spacer(),
                      Text(
                        'Lv.${_checkinResult!['user']?['level'] ?? 1} · ${_checkinResult!['user']?['points'] ?? 0} pts',
                        style: TextStyle(fontSize: 11, color: Colors.white.withOpacity(0.5)),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Text(
                    _checkinResult!['suggestion']?['suggestion'] ?? 'Enjoy the event!',
                    style: TextStyle(fontSize: 12, color: Colors.white.withOpacity(0.7), height: 1.4),
                  ),
                ],
              ),
            ),
          ),
        ],

        const SizedBox(height: 32),

        // Credits Section
        Center(
          child: Column(
            children: [
              Text(
                'Designed & Developed by Ankush Singh Gandhi',
                style: TextStyle(fontSize: 10, color: Colors.white.withOpacity(0.3), fontWeight: FontWeight.w500),
              ),
              const SizedBox(height: 2),
              Text(
                'warriorwhocodes.com',
                style: TextStyle(fontSize: 10, color: const Color(0xFF4285F4).withOpacity(0.4), fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 8),
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                   Text('Using ', style: TextStyle(fontSize: 9, color: Colors.white.withOpacity(0.2))),
                   Text('Gemini 3.1 Pro & Flash', style: TextStyle(fontSize: 9, color: Colors.white.withOpacity(0.4), fontWeight: FontWeight.w800)),
                ],
              ),
            ],
          ),
        ),

        const SizedBox(height: 100), // Padding for bottom bar
      ],
    );

  }

  Widget _buildBottomBar() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      decoration: BoxDecoration(
        color: const Color(0xFF0C1221).withOpacity(0.95),
        border: Border(top: BorderSide(color: Colors.white.withOpacity(0.05))),
      ),
      child: SafeArea(
        top: false,
        child: Row(
          children: [
            // User selector
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.04),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.white.withOpacity(0.06)),
              ),
              child: DropdownButtonHideUnderline(
                child: DropdownButton<String>(
                  value: _selectedUser,
                  isDense: true,
                  dropdownColor: const Color(0xFF111B2E),
                  style: const TextStyle(fontSize: 12, color: Colors.white),
                  items: _users.map((u) => DropdownMenuItem(
                    value: u['id'],
                    child: Text(u['name']!, style: const TextStyle(fontSize: 12)),
                  )).toList(),
                  onChanged: (v) => setState(() => _selectedUser = v!),
                ),
              ),
            ),

            const SizedBox(width: 8),

            // Check In
            Expanded(
              child: GestureDetector(
                onTap: _loading ? null : _doCheckIn,
                child: Container(
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  decoration: BoxDecoration(
                    color: const Color(0xFF6366F1).withOpacity(0.15),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: const Color(0xFF6366F1).withOpacity(0.3)),
                  ),
                  alignment: Alignment.center,
                  child: _loading
                      ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                      : const Text('📍 Check In', style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13, color: Color(0xFF6366F1))),
                ),
              ),
            ),

            const SizedBox(width: 8),

            // Ask Gemini
            GestureDetector(
              onTap: _geminiLoading ? null : _doAskGemini,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(colors: [Color(0xFF4285F4), Color(0xFFA855F7), Color(0xFFEA4335)]),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: _geminiLoading
                    ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                    : const Text('✨ Gemini', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13, color: Colors.white)),
              ),
            ),

            const SizedBox(width: 8),

            // Emergency
            GestureDetector(
              onTap: _doEmergency,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                decoration: BoxDecoration(
                  color: const Color(0xFFEA4335).withOpacity(0.12),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: const Color(0xFFEA4335).withOpacity(0.3)),
                ),
                child: const Text('🚨', style: TextStyle(fontSize: 16)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmergencyOverlay() {
    return AnimatedOpacity(
      opacity: _emergency ? 1.0 : 0.0,
      duration: const Duration(milliseconds: 300),
      child: Container(
        color: const Color(0xFFEA4335).withOpacity(0.15),
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text('🚨', style: TextStyle(fontSize: 64)),
              const SizedBox(height: 12),
              const Text('EMERGENCY', style: TextStyle(fontSize: 28, fontWeight: FontWeight.w900, color: Color(0xFFEA4335), letterSpacing: 4)),
              const Text('EVACUATION', style: TextStyle(fontSize: 28, fontWeight: FontWeight.w900, color: Color(0xFFEA4335), letterSpacing: 4)),
              const SizedBox(height: 12),
              Text('All fans directed to nearest exits', style: TextStyle(fontSize: 14, color: Colors.white.withOpacity(0.8))),
              const SizedBox(height: 24),
              GestureDetector(
                onTap: () => setState(() => _emergency = false),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Text('Dismiss', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatPhase(String phase) {
    switch (phase) {
      case 'pre_event': return '🎫 Pre-Event';
      case 'during_event': return '⚽ During';
      case 'halftime': return '☕ Halftime';
      case 'post_event': return '🚪 Post';
      default: return phase;
    }
  }
}
