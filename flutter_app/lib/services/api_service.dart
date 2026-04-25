import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

class ApiService {
  // Use 10.0.2.2 for Android emulator, 127.0.0.1 for iOS simulator
  static String get baseUrl {
    if (Platform.isAndroid) {
      return 'http://10.0.2.2:5000';
    }
    return 'http://127.0.0.1:5000';
  }

  /// Fetch full stadium state
  static Future<Map<String, dynamic>> getState() async {
    final response = await http.get(Uri.parse('$baseUrl/api/state'));
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    throw Exception('Failed to load state');
  }

  /// Advance simulation by 1 tick
  static Future<Map<String, dynamic>> simulate() async {
    final response = await http.post(Uri.parse('$baseUrl/api/simulate'));
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    throw Exception('Failed to simulate');
  }

  /// Check in a user at a node
  static Future<Map<String, dynamic>> checkIn(String userId, String nodeId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/user/checkin'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'user_id': userId, 'node_id': nodeId}),
    );
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    throw Exception('Failed to check in');
  }

  /// Ask Gemini AI to decide
  static Future<Map<String, dynamic>> askGemini() async {
    final response = await http.post(Uri.parse('$baseUrl/api/agent/decide'));
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    throw Exception('Failed to contact Gemini');
  }

  /// Trigger emergency evacuation
  static Future<Map<String, dynamic>> triggerEmergency() async {
    final response = await http.post(Uri.parse('$baseUrl/api/emergency'));
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    throw Exception('Emergency activation failed');
  }

  /// Get leaderboard
  static Future<List<dynamic>> getLeaderboard() async {
    final response = await http.get(Uri.parse('$baseUrl/api/leaderboard'));
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return data['leaderboard'] ?? [];
    }
    throw Exception('Failed to load leaderboard');
  }
}
