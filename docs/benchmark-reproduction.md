# Reproduce the MI355X GPU benchmarks

See [the common upstream dependency convention](upstream-dependencies.md) for every engine’s source URL, commit and clone command.

This guide starts from a new checkout. It reproduces the supplied-example workloads;
the repository contains their code and source pins, not virtual environments,
upstream payloads, models, private logs or an AMD driver installation.

[Experiment settings](benchmark-parameters.md) lists model, solver, env count, warm-up, seed and timing settings; the JSON manifest covers both measured cohorts.

## 1. Clone and select a target

```bash
git clone https://github.com/jackhan-amd/robotics-simulators.git
cd robotics-simulators
python3 -m simulators list
python3 -m simulators check
```

The measured target was one MI355X/gfx950 with 288 GiB VRAM, Ubuntu 24.04.5
and Python 3.12.3. Preserve the installed driver and use isolated user prefixes.
Read [the observed versions](../study/software-observations.json) and
[per-engine preparation](../study/REPRODUCE.md). The original core recipe smokes
retain their reviewed gfx1151 target; use the study adapters for MI355X.

## 2. Configure configured runtime storage

Prepare one runtime workspace and copy `study/profile.example.json` to the ignored
`private/study-profile.json` on the client, filling in your own connection and paths.
Alternatively set the documented environment variables. Never commit that profile.
On the Linux GPU target:

```bash
export LAB_ROOT="/path/to/external/benchmark"
export STUDY_STORAGE_ROOT="$LAB_ROOT/storage"
export STUDY_WORKTREE="$PWD"
export ROCM_PATH="/path/to/matching/rocm-sdk"
mkdir -p "$LAB_ROOT" "$STUDY_STORAGE_ROOT"
# User-owned bootstrap tools only; keep the existing driver and global Python.
python3 -m venv "$LAB_ROOT/bootstrap-tools"
"$LAB_ROOT/bootstrap-tools/bin/pip" install uv
export PATH="$LAB_ROOT/bootstrap-tools/bin:$PATH"
python3 study/bootstrap.py
source "$LAB_ROOT/env.sh"
```

The bootstrap links `$LAB_ROOT/repo` to this checkout and copies the adapters into
the flat workspace. It refuses conflicting files and preserves an existing env.sh.
Use a fresh runtime workspace when changing adapter versions.
The measurement code uses `$LAB_ROOT/storage/venvs`, `upstream`, `build`, `install`
and `official-taichi` as described in the engine guide. The base Torch/ROCm runtime
must already be supplied; the repository does not install global drivers.

## 3. Prepare one engine

The measured container already supplied Torch/ROCm. A fresh user prefix must
retain those packages. With Python 3.12 and a compatible ROCm Torch visible:

```bash
python3 -c "import sys,torch; assert sys.version_info[:2]==(3,12); assert torch.version.hip; print(torch.__version__)"
"$LAB_ROOT/bin/uv" venv --system-site-packages --python "$(command -v python3)" "$STUDY_STORAGE_ROOT/venvs/base"
python3 study/setup_remote.py
```

`setup_remote.py` creates user-owned native build tools and the MuJoCo package
used for sanity checks; it does not install CPU-only simulators. Record tool
versions after setup. Some dependencies are large; prepare one engine at a time.

Use [REPRODUCE.md](../study/REPRODUCE.md) for exact engine commands and source pins.
`study/install_gpu.py` prepares supported Python backends in isolated prefixes;
`study/build_engine.py` provides gfx950 native build adapters. MJX Humanoid uses
matched JAX/jaxlib/PJRT/plugin 0.12.0 and the isolated ROCm 7.14.1 loader:

```bash
python3 study/prepare_mjx_aligned.py
```

Read the script's required environment and [MJX profile](../study/mjx-profile.json)
before execution. FluidLab requires operator-authorized upstream source/runtime;
it is not bundled; use the common upstream clone tool for its pinned source. FluidLab measurements cover forward simulation only; gradient/backward, learning and optimization were not tested. Its engine runs on the same MI355X server GPU, with runtime files kept in a separate local directory. Taichi and Instinct Sim require their
documented payload/build/asset setup. An install exit code is not a physics check.

## 4. Run smoke, then env scaling

Inspect current device activity, choose the allocated GPU and leave unrelated
services untouched. The coordinator performs a bounded smoke before the sweep;
`run_remote.py` serializes GPU jobs. Run one coordinator at a time:

```bash
cd "$LAB_ROOT"
source ./env.sh
python3 representative_suite.py                  # MJWarp Humanoid
PROVIDED_MJX_VERSION=0.12.0 PROVIDED_MJX_COMPILER_PROFILE=default \
  python3 provided_mjx_suite.py                   # MJX Humanoid
```

MuJoCo envs are 2048, 4096, 8192, 16384, 32768 and 65536, with 1000 measured
steps and five synchronized timing samples. Physics XML, control inputs and
solver settings are pinned. CPU calculations check short same-scene trajectories
only; they are excluded from throughput.

Other supplied-example coordinators:

| Workload | Entry point in the flat workspace |
|---|---|
| Genesis Franka | `provided_scaling_suite.py` |
| Genesis SPH coupling | `PROVIDED_ENGINE=genesis-sph python3 provided_replicas_suite.py` |
| Chrono FSI-SPH / DEM | `provided_chrono_suite.py` |
| incflo | `PROVIDED_CFD_ENGINE=incflo python3 provided_cfd_suite.py` |
| nekRS TGV | `PROVIDED_CFD_ENGINE=nekrs PROVIDED_CFD_WINDOWS=1 python3 provided_cfd_suite.py` |
| FluidLab MixingEnv | `PROVIDED_ENGINE=fluidlab python3 provided_replicas_suite.py` |
| Taichi MPM88 | `PROVIDED_ENGINE=taichi python3 provided_replicas_suite.py` |
| Instinct Sim LIBERO | `provided_instinct_suite.py` |
| GSplat supplied garden fixture | `provided_gsplat_suite.py` |

Consult each coordinator's documented engine selection, library paths and time
budgets. Some native workloads replicate independent GPU processes rather than
batching inside one solver. GSplat counts cameras and performs rendering.

## 5. Validate and inspect results

Keep each raw JSON receipt with its execution log under `$LAB_ROOT/evidence`.
Check actual AMD GPU/backend, zero exit, scene-specific numerical checks,
five finite positive timing samples and any validation barriers. Compute
`env-steps/s = envs * measured_steps / median(synchronized_seconds)`.
For Chrono DEM, distinguish the 1 ms outer advance call from internal substeps;
for nekRS, retain the consecutive-window sampling definition.

From the configured client checkout, `python study/refresh_gpu_report.py --collect`
collects evidence and rebuilds an existing reviewed report package. A fresh code
clone does not contain the private report Markdown or raw history: results can be
inspected directly from receipts, or an independently supplied customer results
ZIP can be rebuilt with the offline commands in [study/README.md](../study/README.md).
Never label new runs PASS solely because a process exited successfully.
