
#if AUTOTUNE_ENABLED
class SubAutoTune : public AC_AutoTune_Multi {
public:
    bool init() override;
    uint8_t axes() const { return get_axis_bitmask(); }
    uint8_t configured_axes() const { return AC_AutoTune_Multi::get_axis_bitmask(); }
    void stop() { AC_AutoTune::stop(); frozen_axes = 0; }
    void release_axes() { frozen_axes = 0; }
    bool complete() const { return mode == TuneMode::FINISHED; }
    bool failed() const { return mode == TuneMode::FAILED; }
protected:
    uint8_t get_axis_bitmask() const override { return frozen_axes ? frozen_axes : configured_axes(); }
    float get_desired_climb_rate_ms() const override;
    void get_pilot_desired_rp_yrate_rad(float &roll, float &pitch, float &yaw_rate) override;
    void init_z_limits() override;
#if HAL_LOGGING_ENABLED
    void log_pids() override;
#endif
private:
    uint8_t frozen_axes = 0;
};

class ModeAutoTune : public Mode {
public:
    using Mode::Mode;
    bool init(bool ignore_checks) override;
    void run() override;
    void stop();
    void on_disarm();
    bool requires_GPS() const override { return false; }
    bool requires_altitude() const override { return true; }
    bool allows_arming(bool from_gcs) const override { return false; }
    SubAutoTune autotune;
protected:
    const char *name() const override { return "AUTOTUNE"; }
    const char *name4() const override { return "ATUN"; }
    Number number() const override { return Number::AUTOTUNE; }
private:
    float initial_z_cm = 0;
    uint32_t started_ms = 0;
    uint8_t axes = 0;
    bool active = false;
};
#endif
