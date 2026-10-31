// Reads events from stdin and prints the checker's decisions, so CI can compare
// this C++ implementation with the Python one on the same random event stream.
//   input lines:  "brake 0|1", "cruise 0|1", "steer <torque>"
//   output lines: "1" or "0" for each steer line
// Build: g++ -std=c++17 -O2 -Wall -Wextra safety_replay.cpp -o safety_replay
#include <iostream>
#include <string>

#include "safety.hpp"

int main() {
  SafetyChecker s;
  std::string kind;
  long value;
  while (std::cin >> kind >> value) {
    if (kind == "brake") s.on_brake(value != 0);
    else if (kind == "cruise") s.on_cruise(value != 0);
    else if (kind == "steer") std::cout << (s.allow_steer(static_cast<int32_t>(value)) ? 1 : 0) << '\n';
    else { std::cerr << "unknown event " << kind << '\n'; return 2; }
  }
}
