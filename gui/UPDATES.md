# Operation MX desktop releases and automatic updates

Supported platform: **Ubuntu 22.04 x86_64, ROS Humble, Gazebo Harmonic**.
An installed desktop checks the private GitHub repository for a stable release
at startup and every 15 minutes while idle. It downloads updates in the
background and activates them on the next launch, after the previous session
has closed. The **Auto updates** checkbox is remembered; **Check updates**
also works manually. Offline checks keep the installed version working.

Each user must have access to the repository and configure **GitHub access** in
the app. Use a personal token with repository **Contents: Read** permission.
**Actions: Read** is useful for maintainers monitoring builds but is unnecessary
for ordinary update downloads. Choose an expiration and replace expired tokens
through the same dialog. Never distribute the release-signing private key to
desktop users.

The token is stored outside the app/repository at
`~/.config/operation-mx/github-token` with permissions 600. `XDG_CONFIG_HOME`,
`OPERATION_MX_GITHUB_TOKEN_FILE`, and the session-only
`OPERATION_MX_GITHUB_TOKEN` environment variable are supported. The updater
authenticates GitHub API release-asset requests and strips authorization on CDN
redirects. GitHub access is separate from the signature/checksum verification.

## One-time installation for desktop users

The native environment must already contain ROS Humble, Gazebo Harmonic,
`ros_gz_sim`, `ros_gz_bridge`, MAVROS with GeographicLib datasets, RViz, xacro,
robot_state_publisher, joy, colcon, a C++ compiler, PyQt5 and python3-cryptography.
ArduSub and the working Harmonic ArduPilot Gazebo plugin must be installed.
The team's `real_joy` package must be built in the software workspace.
RTAB-Map and its native libraries are delivered in each desktop release.
The installer builds only the simulation ROS package, not ArduSub.

Download `operation-mx-installer-VERSION.tar.gz` from a published GitHub release.
Extract it and run:

```bash
cd operation-mx-installer
python3 install.py
```

Default existing workspaces are `~/Software2026` and `~/ardupilot`. For other
locations, use `--software-workspace /path/to/software --ardupilot /path/to/ardupilot`.
The installer checks these prerequisites before touching the launcher.
It requires no sudo, does not delete existing workspaces, and creates the
Operation MX application-menu and desktop shortcuts after its startup checks pass.
Existing desktop users need this migration once to receive subsequent releases.

For an existing **1.0.x** managed installation, download the 1.1.0 installer while
signed into GitHub, close the app and stop its simulation, then run
`python3 install.py --upgrade`. It preserves local paths, data and the previous
working release, and refuses an installer with a different signing key. Then
configure GitHub access. Older clients cannot download the first private update
automatically because they do not yet support authentication.

Per-user layout (respects `XDG_DATA_HOME`):

```text
~/.local/share/operation-mx/
  bin/operation-mx              stable entry point
  releases/1.0.0/               GUI, matching simulation source/build, RTAB-Map
  releases/1.0.1/               next version (previous version retained)
  current.json                 atomically selected current/previous versions
  config.json                  local workspace paths
  cache/                       verified downloads
  data/                        logs, captures, recordings, SLAM databases, icon
```

QGroundControl location and update preferences retain their existing Qt settings.
Previous logs/databases in `mako_ws/gui/runs` stay in that workspace; new managed
sessions save to the stable `data/runs` directory. Updates never remove either.

## Publishing a feature to all desktop installations

1. Commit the updater, public key, application/simulation changes and release
   workflow to GitHub. Private signing keys must stay outside the repository.
2. In repository **Settings → Secrets and variables → Actions**, add the secret
   `OPERATION_MX_SIGNING_KEY` containing the Ed25519 private PEM created for this
   application. The local private file is
   `~/.local/share/operation-mx-release-keys/release-signing-key.pem`.
   Keep a secure backup; losing it prevents signing updates for existing clients.
3. Use **Actions → Operation MX desktop release → Run workflow** with a stable
   version (for example `1.0.1`) to build reviewable artifacts without publishing.
4. To distribute from `main`, set `gui/mako_station/VERSION`, commit and push, then
   push a matching new version tag. For example:

   ```bash
   git switch main
   git pull --ff-only origin main
   # Commit the reviewed changes and matching VERSION first.
   git push origin main
   git tag v1.1.0
   git push origin v1.1.0
   ```

   The tag triggers a build. CI creates a draft release, uploads the complete
   asset set, and publishes it only after validation. Publishing a release through
   GitHub's UI is also supported. The workflow installs
   matching RTAB-Map packages in a ROS Humble build container, runs tests, bundles
   the runtime with the GUI and simulation, signs the manifest, and attaches:
   - `operation-mx-1.1.0-linux-x86_64.tar.gz`
   - `operation-mx-update.json` and its detached Ed25519 signature
   - `operation-mx-installer-1.1.0.tar.gz`
5. Connected clients download the release while idle. On their next launch the
   stable launcher verifies it again, builds its simulation package in a new
   directory, checks ROS/native dependencies and smoke-tests its UI. Only then
   does it change the active version.

Publishing a SLAM feature delivers its checkbox, launch files and matching
RTAB-Map runtime together. It does not turn on SLAM for every pilot. Users still
choose their own simulation settings. Changes pushed to `main` become available
to desktop users when a new release is published, not on every untested commit.
Use a new version for every release; published signed assets are not overwritten.
Collaborators with write access can push a release tag; they do not need a copy
of the private signing key. Pushing a regular commit to main alone does not
deploy it. App updates never flash the real flight controller or automatically
patch users' separate ArduPilot workspaces.

## Local packaging and checks

```bash
source /opt/ros/humble/setup.bash
python3 -m unittest discover -s gui/tests -p 'test_updater.py' -v
python3 tools/build_desktop_release.py --version 1.0.0 \
  --runtime .deps/rtabmap/root \
  --signing-key ~/.local/share/operation-mx-release-keys/release-signing-key.pem
```

The runtime path above is this development machine's existing local RTAB-Map
prefix. Release CI collects a fresh runtime from installed matching packages.
Both packaging and installation refuse unsigned or modified archives.
Archive extraction rejects traversal, symlinks, devices, duplicate files and
excessive expanded size. Native platform/compiler/ROS requirements remain host
prerequisites; graphics drivers are not shipped or replaced by app updates.

## Failure recovery

If setup fails, the previous release remains selected. See
`~/.local/share/operation-mx/data/update-setup.log`. Failed versions are excluded
from automatic retries; manual **Check updates** can retry once prerequisites
have been fixed. Keep the application closed while applying a rollback:

```bash
~/.local/share/operation-mx/bin/operation-mx --rollback
```

The previous working version is restored and the rejected version is not
automatically downloaded again. Files under `data/` and Qt preferences survive.
Restarting while offline works; network access is only needed to obtain updates.
An update server outage never blocks application startup.
