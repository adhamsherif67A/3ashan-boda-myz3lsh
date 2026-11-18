#pragma once
#include <algorithm>
#include <cmath>
namespace realjoy {
inline double shape_pilot_axis(double value, bool invert, double expo, double deadzone, double sensitivity) {
  if (!std::isfinite(value)) return 0.0;
  value = std::clamp(value, -1.0, 1.0);
  if (invert) value = -value;
  const double magnitude = std::abs(value);
  if (magnitude <= deadzone) return 0.0;
  const double normalized = (magnitude - deadzone) / (1.0 - deadzone);
  return std::copysign((expo*normalized*normalized + (1.0-expo)*normalized)*sensitivity,value);
}
inline double bipolar_command(double value) {
  return std::isfinite(value) ? std::round(std::clamp(value,-1.0,1.0)*1000.0) : 0.0;
}
inline double heave_command(double value) {
  return std::isfinite(value) ? std::round(std::clamp(value,-1.0,1.0)*500.0+500.0) : 500.0;
}
}
