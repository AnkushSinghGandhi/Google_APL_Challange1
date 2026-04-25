import 'package:flutter/material.dart';

class ZoneCard extends StatelessWidget {
  final String name;
  final String emoji;
  final int crowd;
  final int capacity;
  final String congestion;
  final int waitTime;
  final bool isSelected;
  final VoidCallback onTap;

  const ZoneCard({
    super.key,
    required this.name,
    required this.emoji,
    required this.crowd,
    required this.capacity,
    required this.congestion,
    required this.waitTime,
    required this.isSelected,
    required this.onTap,
  });

  Color get congestionColor {
    switch (congestion) {
      case 'critical': return const Color(0xFFEA4335);
      case 'high': return const Color(0xFFF97316);
      case 'medium': return const Color(0xFFFBBC04);
      default: return const Color(0xFF34A853);
    }
  }

  @override
  Widget build(BuildContext context) {
    final percent = (crowd / capacity * 100).clamp(0, 150).round();

    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: isSelected
              ? congestionColor.withOpacity(0.1)
              : const Color(0xFF0C1221).withOpacity(0.85),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: isSelected ? congestionColor.withOpacity(0.4) : Colors.white.withOpacity(0.05),
            width: isSelected ? 1.5 : 1,
          ),
          boxShadow: isSelected
              ? [BoxShadow(color: congestionColor.withOpacity(0.15), blurRadius: 16)]
              : null,
        ),
        child: Row(
          children: [
            // Emoji + Ring
            SizedBox(
              width: 50,
              height: 50,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  SizedBox(
                    width: 50,
                    height: 50,
                    child: CircularProgressIndicator(
                      value: (crowd / capacity).clamp(0.0, 1.0),
                      strokeWidth: 3.5,
                      backgroundColor: Colors.white.withOpacity(0.06),
                      valueColor: AlwaysStoppedAnimation<Color>(congestionColor),
                    ),
                  ),
                  Text(emoji, style: const TextStyle(fontSize: 20)),
                ],
              ),
            ),

            const SizedBox(width: 14),

            // Info
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    name,
                    style: const TextStyle(
                      fontWeight: FontWeight.w600,
                      fontSize: 14,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    '$crowd / $capacity  ·  $percent%',
                    style: TextStyle(
                      fontSize: 12,
                      fontFamily: 'monospace',
                      color: Colors.white.withOpacity(0.5),
                    ),
                  ),
                ],
              ),
            ),

            // Right side badge
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: congestionColor.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    congestion.toUpperCase(),
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w700,
                      color: congestionColor,
                      letterSpacing: 0.5,
                    ),
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  '⏱ ${waitTime}m',
                  style: TextStyle(
                    fontSize: 11,
                    color: Colors.white.withOpacity(0.4),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
