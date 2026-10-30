#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <vector>

namespace mako {
struct Mapping {
  int forward{1}, lateral{0}, vertical{3}, yaw{2}, options{6};
  // Forward matches this repository's documented Mako inversion.
  double forward_sign{-1}, lateral_sign{1}, vertical_sign{1}, yaw_sign{-1};
  double deadzone{0.08}, gain{0.5};
};
struct Command { double x{0}, y{0}, z{500}, r{0}; };
inline bool valid_axes(const std::vector<float>& axes, const Mapping& m) {
  for (int i : {m.forward, m.lateral, m.vertical, m.yaw})
    if (i < 0 || static_cast<size_t>(i) >= axes.size() || !std::isfinite(axes[i]))
      return false;
  return true;
}
inline double shape(double v, const Mapping& m) {
  v = std::clamp(v, -1.0, 1.0);
  if (std::abs(v) <= m.deadzone) return 0;
  return std::copysign((std::abs(v)-m.deadzone)/(1-m.deadzone), v) * m.gain;
}
inline bool centered(const std::vector<float>& axes, const Mapping& m) {
  if (!valid_axes(axes, m)) return false;
  for (int i : {m.forward, m.lateral, m.vertical, m.yaw})
    if (std::abs(axes[i]) > m.deadzone) return false;
  return true;
}
inline Command map(const std::vector<float>& axes, const Mapping& m, bool enabled) {
  if (!enabled || !valid_axes(axes, m)) return {};
  return {1000*shape(axes[m.forward],m)*m.forward_sign,
          1000*shape(axes[m.lateral],m)*m.lateral_sign,
          500+500*shape(axes[m.vertical],m)*m.vertical_sign,
          1000*shape(axes[m.yaw],m)*m.yaw_sign};
}
class PressEdge {
  bool previous_{true}; // A button held at startup/reconnect must be released first.
public:
  void reset() { previous_=true; }
  bool update(bool pressed) {
    const bool edge=pressed && !previous_;
    previous_=pressed;
    return edge;
  }
};
} // namespace mako
