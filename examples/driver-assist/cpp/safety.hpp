// Steering-command safety checker — C++ twin of drivekit/safety.py.
// Written the way embedded safety code usually is: no heap, no exceptions,
// fixed-width integers, every branch small enough to test exhaustively.
#pragma once
#include <cstdint>
#include <cstdlib>

struct SteerLimits {
  int32_t max_torque = 1500;
  int32_t max_rate_up = 10;    // per frame, moving away from zero
  int32_t max_rate_down = 25;  // per frame, moving toward zero
};

class SafetyChecker {
 public:
  explicit SafetyChecker(SteerLimits lim = {}) : lim_(lim) {}

  void on_brake(bool pressed) {
    if (pressed) controls_allowed_ = false;
  }
  void on_cruise(bool engaged) {
    if (engaged && !cruise_prev_) controls_allowed_ = true;  // rising edge only
    if (!engaged) controls_allowed_ = false;
    cruise_prev_ = engaged;
  }

  // Returns true if the command may be forwarded to the car.
  bool allow_steer(int32_t torque) {
    const bool ok = check(torque);
    if (ok && controls_allowed_) {
      last_ = torque;
    } else {
      last_ = 0;  // rejected or not allowed: judge the next command against 0, not a stale value
      if (!ok) ++violations_;
    }
    return ok;
  }

  bool controls_allowed() const { return controls_allowed_; }
  uint32_t violations() const { return violations_; }

 private:
  bool check(int32_t t) const {
    if (!controls_allowed_) return t == 0;
    // Range-check before std::abs: abs(INT32_MIN) is undefined behaviour.
    if (t > lim_.max_torque || t < -lim_.max_torque) return false;
    const int32_t a = std::abs(last_), b = std::abs(t);
    if (last_ == 0 || (t > 0) == (last_ > 0)) {
      return b > a ? (b - a) <= lim_.max_rate_up : (a - b) <= lim_.max_rate_down;
    }
    return a <= lim_.max_rate_down && b <= lim_.max_rate_up;  // direction change through zero
  }

  SteerLimits lim_;
  bool controls_allowed_ = false;
  bool cruise_prev_ = false;
  int32_t last_ = 0;
  uint32_t violations_ = 0;
};
