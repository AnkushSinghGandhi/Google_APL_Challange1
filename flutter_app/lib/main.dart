import 'package:flutter/material.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(const EventFlowApp());
}

class EventFlowApp extends StatelessWidget {
  const EventFlowApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'EventFlow AI',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF060A14),
        primaryColor: const Color(0xFF4285F4),
        colorScheme: ColorScheme.dark(
          primary: const Color(0xFF4285F4),
          secondary: const Color(0xFFA855F7),
          surface: const Color(0xFF0C1221),
          error: const Color(0xFFEA4335),
        ),
        cardTheme: CardThemeData(
          color: const Color(0xFF0C1221).withOpacity(0.85),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: BorderSide(color: Colors.white.withOpacity(0.05)),
          ),
          elevation: 0,
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF060A14),
          elevation: 0,
          centerTitle: true,
        ),
      ),
      home: const HomeScreen(),
    );
  }
}
