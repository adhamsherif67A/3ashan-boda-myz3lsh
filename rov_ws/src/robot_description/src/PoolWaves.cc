// Gentle linear-wave approximation; all motion follows Gazebo simulation time.
#include <cmath>
#include <chrono>
#include <vector>
#include <gz/plugin/Register.hh>
#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/sim/Util.hh>
#include <gz/sim/components/Model.hh>
#include <gz/sim/components/Name.hh>
#include <gz/sim/components/Pose.hh>
#include <gz/sim/components/Collision.hh>
#include <gz/sim/components/Link.hh>
#include <gz/sim/components/Inertial.hh>
#include <gz/sim/components/Volume.hh>
#include <gz/sim/components/CenterOfVolume.hh>
#include <sdf/Box.hh>
#include <sdf/Sphere.hh>
#include <sdf/Cylinder.hh>
#include <gz/transport/Node.hh>
#include <gz/msgs/vector3d.pb.h>

namespace mako {
class PoolWaves : public gz::sim::System,
                  public gz::sim::ISystemConfigure,
                  public gz::sim::ISystemPreUpdate,
                  public gz::sim::ISystemReset {
 public:
  void Configure(const gz::sim::Entity &, const std::shared_ptr<const sdf::Element> &sdf,
                 gz::sim::EntityComponentManager &, gz::sim::EventManager &) override {
    amplitude = sdf->Get<double>("amplitude", 0.018).first;
    wavelength = sdf->Get<double>("wavelength", 12.0).first;
    robot = sdf->Get<std::string>("robot_model", "mako").first;
    halfLength = sdf->Get<double>("half_length", 7.0).first;
    halfWidth = sdf->Get<double>("half_width", 6.0).first;
    waterDepth = sdf->Get<double>("water_depth", 3.0).first;
    publisher = node.Advertise<gz::msgs::Vector3d>("/model/" + robot + "/ocean_current");
  }
  void Reset(const gz::sim::UpdateInfo &, gz::sim::EntityComponentManager &) override {
    strips.clear();
    lastTime = -1;
    publisher.Publish(gz::msgs::Vector3d{});
  }
  void PreUpdate(const gz::sim::UpdateInfo &info, gz::sim::EntityComponentManager &ecm) override {
    if (info.paused) return;
    // World systems configure before model entities exist. Discover on update.
    if (strips.empty()) {
      ecm.Each<gz::sim::components::Model, gz::sim::components::Name>(
        [&](const gz::sim::Entity &entity, const auto *, const auto *name) {
          if (name->Data().find("pool_ripple_") == 0)
            strips.push_back(entity);
          return true;
        });
    }
    const double t = std::chrono::duration<double>(info.simTime).count();
    // Limit rendering and transport updates to 30 Hz; resets restart immediately.
    if (t >= lastTime && t - lastTime < 1.0 / 30.0) return;
    lastTime = t;
    const double k = 2.0 * M_PI / wavelength;
    const double omega = std::sqrt(9.81 * k);
    for (const auto entity : strips) {
      const double x = gz::sim::worldPose(entity, ecm).Pos().X();
      const double phase = k * x - omega * t;
      const double secondary = 2 * k * x + std::sqrt(2.0) * omega * t;
      const double z = amplitude * (std::sin(phase) + 0.3 * std::sin(secondary));
      const double slope = amplitude * k * (std::cos(phase) + 0.6 * std::cos(secondary));
      // Visual-only static models: change their scene poses directly.
      ecm.SetComponentData<gz::sim::components::Pose>(entity,
          gz::math::Pose3d(x, 0, z, 0, -std::atan(slope), 0));
      ecm.SetChanged(entity, gz::sim::components::Pose::typeId,
                     gz::sim::ComponentState::PeriodicChange);
    }
    const auto entity = ecm.EntityByComponents(gz::sim::components::Model(),
                                             gz::sim::components::Name(robot));
    gz::msgs::Vector3d current;
    if (entity != gz::sim::kNullEntity) {
      const auto pos = gz::sim::worldPose(entity, ecm).Pos();
      if (std::abs(pos.X()) <= halfLength && std::abs(pos.Y()) <= halfWidth && pos.Z() <= 0 && pos.Z() >= -waterDepth) {
        const double phase = k * pos.X() - omega * t;
        const double secondary = 2 * k * pos.X() + std::sqrt(2.0) * omega * t;
        // Orbital velocities of the same surface waves, attenuated with depth.
        const double primary = amplitude * omega * std::exp(k * pos.Z());
        const double second = 0.3 * amplitude * std::sqrt(2.0) * omega * std::exp(2*k*pos.Z());
        current.set_x(primary * std::sin(phase) - second * std::sin(secondary));
        current.set_z(-primary * std::cos(phase) - second * std::cos(secondary));
      }
    }
    publisher.Publish(current);
  }
 private:
  gz::transport::Node node;
  gz::transport::Node::Publisher publisher;
  std::vector<gz::sim::Entity> strips;
  std::string robot;
  double amplitude{0.018}, wavelength{12}, lastTime{-1};
  double halfLength{7}, halfWidth{6}, waterDepth{3};
};

// The initial ECM snapshot predates Buoyancy's generated Volume / CenterOfVolume
// components. After reset the existing links are not EachNew, so the stock
// plugin does not rebuild them. Restore the primitive displacement metadata
// before its next PreUpdate; graded buoyancy then applies its usual forces.
class ResetBuoyancy : public gz::sim::System, public gz::sim::ISystemReset {
 public:
  void Reset(const gz::sim::UpdateInfo &, gz::sim::EntityComponentManager &ecm) override {
    ecm.Each<gz::sim::components::Link, gz::sim::components::Inertial>(
      [&](const gz::sim::Entity &entity, const auto *, const auto *) {
        double volume = 0;
        gz::math::Vector3d moment{0, 0, 0};
        for (const auto collision : ecm.ChildrenByComponents(
                 entity, gz::sim::components::Collision())) {
          const auto *element = ecm.Component<gz::sim::components::CollisionElement>(collision);
          const auto *pose = ecm.Component<gz::sim::components::Pose>(collision);
          if (!element || !pose || !element->Data().Geom()) continue;
          const auto *geometry = element->Data().Geom();
          double displaced = 0;
          if (geometry->BoxShape()) displaced = geometry->BoxShape()->Shape().Volume();
          else if (geometry->SphereShape()) displaced = geometry->SphereShape()->Shape().Volume();
          else if (geometry->CylinderShape()) displaced = geometry->CylinderShape()->Shape().Volume();
          // These are the shapes supported by this pool's graded buoyancy.
          volume += displaced;
          moment += displaced * pose->Data().Pos();
        }
        ecm.SetComponentData<gz::sim::components::Volume>(entity, volume);
        const gz::math::Vector3d center = volume > 0 ? moment / volume : gz::math::Vector3d::Zero;
        ecm.SetComponentData<gz::sim::components::CenterOfVolume>(entity, center);
        return true;
      });
  }
};
}
GZ_ADD_PLUGIN(mako::PoolWaves, gz::sim::System,
              mako::PoolWaves::ISystemConfigure, mako::PoolWaves::ISystemPreUpdate,
              mako::PoolWaves::ISystemReset)
GZ_ADD_PLUGIN(mako::ResetBuoyancy, gz::sim::System, mako::ResetBuoyancy::ISystemReset)
