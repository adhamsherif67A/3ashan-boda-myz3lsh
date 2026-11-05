# 🌊 MarineXperts 2027 | Mako ROV

<p align="center">
  <strong>Underwater Robotics • Simulation • Software Engineering • Innovation</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Team-MarineXperts-00B8D9?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Project-Mako_ROV-003B5C?style=for-the-badge" />
  <img src="https://img.shields.io/badge/ROS-2_Humble-22314E?style=for-the-badge&logo=ros" />
  <img src="https://img.shields.io/badge/Gazebo-Harmonic-00A6C8?style=for-the-badge" />
</p>

---

## 🚀 Welcome to MarineXperts!

Welcome to the official software repository of **MarineXperts 2027**.

This repository is the central workspace for our software development team. It contains the software, simulation environment, control interfaces, firmware, tools, and development resources required to build and operate our Mako Remotely Operated Vehicle (ROV).

Our goal is to develop a reliable, modular, and well-documented underwater robotics system through teamwork, engineering, and continuous improvement.

**Every contribution matters. Every subsystem matters. Every team member matters.**

---

## 🎯 Project Overview

The MarineXperts Mako ROV software ecosystem includes:

- **ROV Simulation:** A simulated underwater environment for testing and development.
- **Vehicle Control:** ArduSub SITL integration for ROV control.
- **Pilot Interface:** Operation MX graphical interface.
- **Robotics Middleware:** ROS 2 Humble communication and integration.
- **Simulation Environment:** Gazebo Harmonic with custom underwater worlds.
- **Computer Vision:** Camera feeds, depth processing, and visual odometry.
- **Firmware:** Vehicle-related firmware development and configuration.
- **Development Tools:** Scripts and utilities for testing and maintaining the system.

### Main Technologies

| Technology | Purpose |
|---|---|
| Python | Software development and interfaces |
| ROS 2 Humble | Robotics communication |
| Gazebo Harmonic | Underwater simulation |
| ArduSub | ROV flight controller software |
| MAVROS | Communication with ArduPilot |
| Docker | Development environment |
| Git & GitHub | Version control and collaboration |

---

## 📁 Repository Structure

Please understand the repository structure before modifying any files.

```text
MarineXperts/
│
├── .github/
│   └── workflows/          # GitHub automation
│
├── docker/                 # Simulation build and run scripts
│
├── firmware/
│   └── ardusub-autotune/   # Firmware-related development
│
├── gui/                    # Operation MX pilot interface
│
├── src/                    # Main ROV ROS 2 source code
│
├── tools/                  # Development utilities
│
├── Dockerfile              # Simulation environment
├── entrypoint.sh           # Container entry point
├── commands.txt            # Useful commands
├── SIMULATION_READY.md     # Simulation readiness notes
├── README.md               # Main team documentation
└── readme.md               # Detailed simulation setup guide
```

### Where should you work?

| If you are working on... | Go to... |
|---|---|
| Pilot GUI | `gui/` |
| ROV model and ROS 2 | `src/` |
| Firmware | `firmware/` |
| Simulation setup | `docker/` |
| Development utilities | `tools/` |

---

## 🛠️ Getting Started

### 1. Prerequisites

The documented simulation setup is intended for Linux x86-64, preferably Ubuntu 22.04 or 24.04.

Install or prepare:

- Git
- Docker Engine
- A working graphics environment for Gazebo GUI
- NVIDIA Container Toolkit if using an NVIDIA GPU

**Important:** The documented simulation workflow is Linux-based. Windows and macOS Docker Desktop setups are not covered by the current instructions.

### 2. Clone the repository

Open your terminal:

```bash
git clone --branch boda --single-branch https://github.com/adhamsherif67A/3ashan-boda-myz3lsh.git MarineXperts
```

Enter the project directory:

```bash
cd MarineXperts
```

Verify your branch:

```bash
git branch --show-current
```

The expected branch is:

```text
boda
```

### 3. Build the simulation environment

```bash
./docker/build.sh
```

This prepares the required simulation environment and dependencies inside Docker.

### 4. Launch the simulation

For the team pool:

```bash
./docker/run.sh --world pool.world
```

For the ocean environment:

```bash
./docker/run.sh --world ocean.world
```

### 5. Verify the environment

```bash
docker run --rm marinexperts/mako:boda doctor
```

A successful check should report:

```text
RESULT: ready
```

For complete installation instructions, GPU configuration, simulation options, and troubleshooting, read the [Detailed Simulation Guide](readme.md).

---

## 💻 Working With the GUI

The repository includes **Operation MX**, our ROV pilot interface.

The GUI is designed to provide an interface for operating and monitoring the simulated vehicle.

Before making changes:

1. Navigate to the `gui/` directory.
2. Read its README.
3. Understand the existing project structure.
4. Test your changes before pushing them.

See the [Operation MX GUI Documentation](gui/README.md).

---

## 🔄 Git & Team Collaboration

This repository is shared between MarineXperts software team members.

To keep development organized, everyone should follow the same workflow.

### 1. Get the latest changes

Before starting work:

```bash
git checkout boda
git pull origin boda
```

### 2. Create your own development branch

Never work directly on the shared branch for experimental changes.

```bash
git checkout -b feature/your-feature-name
```

Examples:

```bash
git checkout -b feature/gui-improvements
git checkout -b feature/camera-system
git checkout -b fix/simulation-bug
```

### 3. Make your changes

Work only on the files related to your assigned task whenever possible.

Test your changes locally.

### 4. Commit your changes

```bash
git add .
git commit -m "Add: description of your changes"
```

Examples:

```bash
git commit -m "Add: camera monitoring interface"
git commit -m "Fix: simulation startup issue"
git commit -m "Update: ROV control system"
```

### 5. Push your branch

```bash
git push -u origin feature/your-feature-name
```

### 6. Create a Pull Request

On GitHub:

1. Open the repository.
2. Select your pushed branch.
3. Create a Pull Request targeting `boda`.
4. Explain what you changed.
5. Include screenshots or testing results when relevant.
6. Request a review before merging.

**Do not push untested experimental changes directly into the shared branch.**

---

## 📋 Development Guidelines

To maintain code quality and avoid conflicts, every member should follow these guidelines.

### Code Quality

- Write clean, readable, and maintainable code.
- Use meaningful variable and function names.
- Add comments where necessary.
- Avoid unnecessary duplicate code.
- Keep modules organized.
- Follow the existing project architecture.

### Before Committing

- [ ] Test your changes.
- [ ] Check that existing functionality still works.
- [ ] Remove unnecessary files and debugging code.
- [ ] Review your Git changes.
- [ ] Write a meaningful commit message.
- [ ] Update documentation when necessary.

### Repository Safety

- Never upload passwords, API keys, tokens, or private credentials.
- Avoid committing generated build files, temporary files, and unnecessary logs.
- Do not overwrite another member's work without coordination.
- Discuss major architectural changes before implementing them.

---

## 🧪 Testing & Validation

Testing is an essential part of our development process.

Depending on the subsystem, members should validate:

- ROS 2 communication and topic availability.
- ROV model and sensor configuration.
- ArduSub SITL connectivity.
- Gazebo simulation behavior.
- GUI functionality and control response.
- Camera and depth data.
- Changes to firmware-related components.

Use the existing test scripts and documentation before introducing new testing procedures.

---

## 📚 Important Documentation

| Resource | Description |
|---|---|
| [Simulation Guide](readme.md) | Full simulation installation and operation |
| [GUI Documentation](gui/README.md) | Operation MX instructions |
| [Simulation Readiness](SIMULATION_READY.md) | Simulation readiness information |
| [Commands Reference](commands.txt) | Useful project commands |
| [ZED Visual Odometry](src/robot_description/ZED_VO.md) | Visual odometry documentation |

---

## 🤝 Team Responsibilities

Every software team member is expected to:

1. Understand their assigned subsystem.
2. Keep their work updated with the shared repository.
3. Communicate progress and technical difficulties.
4. Document important changes.
5. Test before submitting code.
6. Review and respect other members' contributions.
7. Maintain a professional and collaborative development environment.

If you encounter a problem, document the error, steps to reproduce it, and any attempted solutions before requesting assistance.

---

## 🏁 Our Mission

We are not simply writing code.

We are building an integrated underwater robotics system that combines mechanical engineering, electronics, software, control systems, and intelligent technologies.

Every subsystem we develop contributes to the performance and reliability of the Mako ROV.

**One Team. One System. One Mission.**

<p align="center">
  <strong>MARINEXPERTS 2027</strong><br/>
  <em>Engineering Beneath the Surface.</em>
</p>

---

<p align="center">
  Made with dedication by the MarineXperts Software Team.
</p>
